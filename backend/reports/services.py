import re
import zipfile
import tempfile
import os
from datetime import datetime, date
from pathlib import Path

import pdfplumber

from .models import CreditReport


# ── Bureau detection ────────────────────────────────────────────────────────

BUREAU_SIGNATURES = {
    'equifax': [r'equifax', r'myequifax'],
    'experian': [r'experian'],
    'transunion': [r'transunion', r'trans union'],
}


def detect_bureau(text: str) -> str:
    lower = text.lower()
    for bureau, patterns in BUREAU_SIGNATURES.items():
        if any(re.search(p, lower) for p in patterns):
            return bureau
    return 'unknown'


# ── Text extraction ──────────────────────────────────────────────────────────

def extract_text_from_pdf(file_path: str) -> tuple[str, int]:
    """Return (full_text, page_count) from a PDF file."""
    pages = []
    with pdfplumber.open(file_path) as pdf:
        page_count = len(pdf.pages)
        for page in pdf.pages:
            text = page.extract_text() or ''
            pages.append(text)
    return '\n'.join(pages), page_count


# ── Field extractors ─────────────────────────────────────────────────────────

def extract_name(text: str) -> str:
    patterns = [
        r'(?:Name|Full Name|Consumer Name|Borrower)[:\s]+([A-Z][A-Za-z,.\s-]{2,60})(?:\n|$)',
        r'^([A-Z][A-Z\s,.-]{4,50})$',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.MULTILINE)
        if match:
            name = match.group(1).strip().rstrip(',')
            if len(name) >= 4:
                return name
    return ''


def extract_ssn(text: str) -> tuple[str, str]:
    """Return (full_or_masked_ssn, last_four). Common credit reports mask SSN."""
    patterns = [
        r'\b(\d{3}-\d{2}-\d{4})\b',
        r'\b(XXX-XX-(\d{4}))\b',
        r'\b(\d{3}-XX-(\d{4}))\b',
        r'(?:SSN|Social Security)[^\d]*(\d{3}-\d{2}-\d{4}|\d{9})',
        r'(?:SSN|Social Security)[^\d]*(?:XXX-XX-(\d{4})|xxx-xx-(\d{4}))',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            full = match.group(1) if match.lastindex and match.group(1) else ''
            last_four = ''
            if match.lastindex and match.lastindex >= 2:
                last_four = match.group(2) or ''
            elif full and len(full) >= 4:
                last_four = full[-4:]
            return full, last_four
    return '', ''


def extract_dob(text: str) -> date | None:
    patterns = [
        r'(?:Date of Birth|DOB|Birth Date|Born)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'(?:Date of Birth|DOB|Birth Date|Born)[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
    ]
    date_formats = ['%m/%d/%Y', '%m-%d-%Y', '%m/%d/%y', '%B %d, %Y', '%B %d %Y']
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw = match.group(1).strip()
            for fmt in date_formats:
                try:
                    return datetime.strptime(raw, fmt).date()
                except ValueError:
                    continue
    return None


def extract_alternate_names(text: str) -> list[str]:
    patterns = [
        r'(?:Also Known As|AKA|Other Names?|Previous Names?|Aliases?)[:\s]+((?:[A-Z][A-Za-z,.\s-]+\n?)+)',
    ]
    names = []
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            block = match.group(1)
            for line in block.split('\n'):
                name = line.strip().rstrip(',')
                if len(name) >= 4 and re.search(r'[A-Za-z]', name):
                    names.append(name)
    return names


def extract_addresses(text: str) -> list[dict]:
    """
    Extracts address blocks. Handles common formats:
    123 Main St, Springfield, IL 62701
    123 Main St
    Springfield, IL  62701
    """
    addresses = []
    # Pattern for full inline address
    inline_pattern = r'(\d+\s+[A-Za-z0-9\s.#,-]+),\s*([A-Za-z\s]+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)'
    for match in re.finditer(inline_pattern, text):
        addresses.append({
            'street': match.group(1).strip(),
            'city': match.group(2).strip(),
            'state': match.group(3).strip(),
            'zip_code': match.group(4).strip(),
        })

    # Deduplicate by street
    seen = set()
    unique = []
    for addr in addresses:
        key = addr['street'].lower()
        if key not in seen:
            seen.add(key)
            unique.append(addr)
    return unique


def extract_accounts(text: str) -> list[dict]:
    """
    Extracts financial account blocks. Looks for creditor name + balance patterns.
    Credit reports vary wildly in formatting; this captures common patterns.
    """
    accounts = []

    # Look for creditor blocks: "CREDITOR NAME\nAccount #: ...\nBalance: $..."
    account_pattern = re.compile(
        r'([A-Z][A-Z\s&.,/-]{3,50})\n'
        r'(?:.*?(?:Account(?:\s+Number)?|Acct)[:\s#]+([\w*-]+).*?\n)?'
        r'(?:.*?Balance[:\s]+\$?([\d,]+).*?\n)?',
        re.MULTILINE
    )
    for match in account_pattern.finditer(text):
        creditor = match.group(1).strip()
        if len(creditor) < 4:
            continue
        if re.search(r'(address|employment|personal|summary|report|date|page)', creditor, re.I):
            continue
        accounts.append({
            'creditor_name': creditor,
            'account_number': (match.group(2) or '').strip(),
            'balance_raw': (match.group(3) or '').strip(),
        })

    return accounts[:50]  # cap at 50 to avoid false positives


# ── Main parse orchestrator ──────────────────────────────────────────────────

def parse_report(report: CreditReport) -> dict:
    """
    Parse a CreditReport record. Returns extracted data dict.
    Saves raw_text, bureau, page_count, and status back to the report.
    """
    from django.utils import timezone

    report.status = 'parsing'
    report.save(update_fields=['status'])

    try:
        text, page_count = extract_text_from_pdf(report.file.path)

        bureau = detect_bureau(text)
        ssn, ssn_last_four = extract_ssn(text)

        extracted = {
            'bureau': bureau,
            'page_count': page_count,
            'full_name': extract_name(text),
            'ssn': ssn,
            'ssn_last_four': ssn_last_four,
            'date_of_birth': extract_dob(text),
            'alternate_names': extract_alternate_names(text),
            'addresses': extract_addresses(text),
            'accounts': extract_accounts(text),
        }

        report.raw_text = text
        report.bureau = bureau
        report.page_count = page_count
        report.status = 'parsed'
        report.parsed_at = timezone.now()
        report.error_message = ''
        report.save(update_fields=['raw_text', 'bureau', 'page_count', 'status', 'parsed_at', 'error_message'])

        return extracted

    except Exception as exc:
        report.status = 'failed'
        report.error_message = str(exc)
        report.save(update_fields=['status', 'error_message'])
        raise


def handle_zip_upload(zip_file_path: str, case=None) -> list[CreditReport]:
    """Extract PDFs from a zip archive and create CreditReport records."""
    from django.core.files import File

    reports = []
    with zipfile.ZipFile(zip_file_path, 'r') as zf:
        pdf_names = [n for n in zf.namelist() if n.lower().endswith('.pdf')]
        for pdf_name in pdf_names:
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                tmp.write(zf.read(pdf_name))
                tmp_path = tmp.name

            try:
                with open(tmp_path, 'rb') as f:
                    report = CreditReport(
                        original_filename=Path(pdf_name).name,
                        case=case,
                    )
                    report.file.save(Path(pdf_name).name, File(f), save=True)
                reports.append(report)
            finally:
                os.unlink(tmp_path)

    return reports
