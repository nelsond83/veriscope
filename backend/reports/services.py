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
        # Full 9-digit SSN
        (r'\b(\d{3}-\d{2}-(\d{4}))\b', 1, 2),
        (r'(?:SSN|Social Security)[^\d]*(\d{3}-\d{2}-(\d{4}))', 1, 2),
        # Experian-style: XXX-XX-####
        (r'\b(XXX-XX-(\d{4}))\b', 1, 2),
        (r'(?:SSN|Social Security)[^\d]*XXX-XX-(\d{4})', None, 1),
        # TransUnion-style: ###-##-####
        (r'\b(###-##-(\d{4}))\b', 1, 2),
        (r'(?:SSN|Social Security)[^\d]*###-##-(\d{4})', None, 1),
        # Partial digit masking
        (r'\b(\d{3}-XX-(\d{4}))\b', 1, 2),
    ]
    for pattern, full_group, last4_group in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            full = match.group(full_group) if full_group and match.lastindex >= full_group else ''
            last_four = match.group(last4_group) if last4_group and match.lastindex >= last4_group else ''
            if not last_four and full:
                last_four = re.sub(r'\D', '', full)[-4:]
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
    _STOP = re.compile(
        r'\b(?:ADDRESS(?:\s+HISTORY)?|ACCOUNT(?:\s+SUMMARY)?|Current\s+Address|'
        r'Previous\s+Address|EMPLOYMENT|PAYMENT\s+HISTORY|CREDIT\s+INQUIR|'
        r'ADVERSE|BANKRUPTCY|SECTION)\b',
        re.IGNORECASE,
    )
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
                if not name:
                    break  # blank line marks end of the names block
                if _STOP.search(name):
                    break  # hit a section header — stop
                if len(name) >= 4 and re.search(r'[A-Za-z]', name):
                    names.append(name)
    return names


def extract_addresses(text: str) -> list[dict]:
    """
    Extracts address blocks from single-line address format:
    123 Main St, Springfield, IL 62701
    """
    addresses = []
    # Restrict to single line — use [ \t] not \s to avoid newline spanning
    inline_pattern = (
        r'(\d+[ \t]+[A-Za-z0-9 \t.#,-]+?)'
        r',[ \t]*([A-Za-z][A-Za-z \t]+?)'
        r',[ \t]*([A-Z]{2})[ \t]+'
        r'(\d{5}(?:-\d{4})?)'
    )
    for match in re.finditer(inline_pattern, text):
        street = match.group(1).strip()
        city = match.group(2).strip()
        state = match.group(3).strip()
        zip_code = match.group(4).strip()
        # Skip obvious false positives
        if len(street) < 5 or len(city) < 2:
            continue
        addresses.append({'street': street, 'city': city, 'state': state, 'zip_code': zip_code})

    # Deduplicate by street
    seen = set()
    unique = []
    for addr in addresses:
        key = addr['street'].lower()
        if key not in seen:
            seen.add(key)
            unique.append(addr)
    return unique


def extract_accounts_from_pdf_tables(file_path: str) -> list[dict]:
    """
    Parse the ACCOUNT SUMMARY table using pdfplumber cell extraction.
    More reliable than text extraction when columns are narrow.
    """
    accounts = []
    seen_creditors = set()

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            for table in (page.extract_tables() or []):
                if not table or len(table) < 2:
                    continue
                header = [str(c or '').strip().lower() for c in table[0]]
                if 'creditor' not in header:
                    continue

                def idx(name):
                    try:
                        return header.index(name)
                    except ValueError:
                        return -1

                ci = idx('creditor')
                ti = idx('type')
                ai = idx('account #')
                si = idx('status')
                bi = idx('balance')
                li = idx('limit')
                hi = idx('high bal')
                oi = idx('opened')

                for row in table[1:]:
                    def cell(i, _row=row):
                        if i < 0 or i >= len(_row):
                            return ''
                        return str(_row[i] or '').strip()

                    creditor = cell(ci)
                    if not creditor or len(creditor) < 4:
                        continue
                    if re.search(r'\b(address|employment|personal|summary|report|date|page|creditor|account|type|status|balance|limit|opened|history)\b', creditor, re.I):
                        continue
                    key = re.sub(r'\s+', ' ', creditor.lower())
                    if key in seen_creditors:
                        continue
                    seen_creditors.add(key)

                    def strip_dollar(s):
                        return re.sub(r'[$,]', '', s or '').strip()

                    accounts.append({
                        'creditor_name': creditor,
                        'account_type_raw': cell(ti),
                        'account_number': cell(ai),
                        'status_raw': cell(si),
                        'balance_raw': strip_dollar(cell(bi)),
                        'credit_limit_raw': strip_dollar(cell(li)),
                        'high_bal_raw': strip_dollar(cell(hi)),
                        'date_opened_raw': cell(oi),
                    })
    return accounts


def extract_accounts(text: str) -> list[dict]:
    """
    Extracts financial account blocks. Handles both labeled and table-row formats.
    Table format: Creditor | Type | Acct# | Status | Balance | Limit | [High Bal] | Opened
    """
    accounts = []
    seen_creditors = set()

    def _add(creditor, account_type_str, account_number, status_str, balance_raw, credit_limit_raw, high_bal_raw, date_opened_raw):
        creditor = creditor.strip()
        if len(creditor) < 4:
            return
        if re.search(r'\b(address|employment|personal|summary|report|date|page|creditor|account|type|status|balance|limit|opened|history)\b', creditor, re.I):
            return
        key = re.sub(r'\s+', ' ', creditor.lower())
        if key in seen_creditors:
            return
        seen_creditors.add(key)
        accounts.append({
            'creditor_name': creditor,
            'account_type_raw': (account_type_str or '').strip(),
            'account_number': (account_number or '').strip(),
            'status_raw': (status_str or '').strip(),
            'balance_raw': (balance_raw or '').replace(',', ''),
            'credit_limit_raw': (credit_limit_raw or '').replace(',', ''),
            'high_bal_raw': (high_bal_raw or '').replace(',', ''),
            'date_opened_raw': (date_opened_raw or '').strip(),
        })

    # Pattern 1 — table row: ALL_CAPS_CREDITOR  MixedCase Type  AccountNum  Status  $Balance  $Limit  [$HighBal]  MM/YYYY
    # Captures 3 optional dollar groups: balance, credit_limit, high_bal (backward-compatible with old 7-col PDFs)
    table_row = re.compile(
        r'^([A-Z][A-Z0-9\s&.,\-/]{3,50}?)(?=\s+[A-Z][a-z]|\s+\*{2}|\s+\d{4})'
        r'\s+([A-Z][a-z]+(?:\s+[A-Za-z]+){0,2})'
        r'\s+(\*{2,}\d+|\d{4,20})'
        r'\s+(Open|Closed|Derogatory|Collection|Charged(?:\s+Off)?)'
        r'(?:\s+\$([\d,]+))?'
        r'(?:\s+\$([\d,]+))?'
        r'(?:\s+\$([\d,]+))?'
        r'(?:\s+(\d{2}/\d{4}))?',
        re.MULTILINE
    )
    for m in table_row.finditer(text):
        _add(m.group(1), m.group(2), m.group(3), m.group(4),
             m.group(5) or '', m.group(6) or '', m.group(7) or '', m.group(8) or '')

    # Pattern 2 — labeled block: "CREDITOR NAME\nAccount #: NNNN\nBalance: $..."
    labeled_block = re.compile(
        r'([A-Z][A-Z\s&.,/-]{3,50})\n'
        r'(?:.*?(?:Account(?:\s+Number)?|Acct)[:\s#]+([\w*-]+).*?\n)?'
        r'(?:.*?Balance[:\s]+\$?([\d,]+).*?\n)?',
        re.MULTILINE
    )
    for m in labeled_block.finditer(text):
        acct_num = (m.group(2) or '').strip()
        if not acct_num:
            continue
        _add(m.group(1), '', acct_num, '', m.group(3) or '', '', '', '')

    return accounts[:50]


def extract_account_details(text: str) -> dict:
    """
    Parse the ACCOUNT DETAILS section for monthly payment and account address.
    Returns dict keyed by account_number → {monthly_payment_raw, account_address}.
    """
    details = {}
    section_m = re.search(r'ACCOUNT DETAILS\n(.*?)(?=\n[A-Z][A-Z\s]{3,}\n|\Z)', text, re.DOTALL)
    if not section_m:
        return details
    section = section_m.group(1)
    line_re = re.compile(
        r'^(.+?)\s+\((\d{4,20})\)'
        r'(?:\s+Monthly Pmt:\s+\$([\d,]+))?'
        r'(?:\s+Addr:\s+([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([A-Z]{2})\s*\|\s*(\d{5}))?',
        re.MULTILINE
    )
    for m in line_re.finditer(section):
        acct_num = m.group(2).strip()
        monthly_raw = m.group(3) or ''
        if m.group(4):
            address = f"{m.group(4).strip()}, {m.group(5).strip()}, {m.group(6)} {m.group(7)}"
        else:
            address = ''
        details[acct_num] = {
            'monthly_payment_raw': monthly_raw,
            'account_address': address,
        }
    return details


def extract_in_file_since(text: str):
    """Parse 'In File Since: MM/YYYY' → date or None."""
    m = re.search(r'In File Since:\s+(\d{2}/\d{4})', text, re.IGNORECASE)
    if m:
        parts = m.group(1).split('/')
        try:
            return date(int(parts[1]), int(parts[0]), 1)
        except (ValueError, IndexError):
            pass
    return None


def extract_credit_score(text: str) -> tuple:
    """Parse credit score lines. Returns (score_int | None, score_type_str)."""
    patterns = [
        (r'FICO Score 8:\s+(\d{3})', 'FICO 8'),
        (r'FICO Score:\s+(\d{3})', 'FICO'),
        (r'VantageScore 3\.0:\s+(\d{3})', 'VantageScore 3.0'),
        (r'VantageScore:\s+(\d{3})', 'VantageScore'),
    ]
    for pattern, score_type in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return int(m.group(1)), score_type
    return None, ''


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
        credit_score, score_type = extract_credit_score(text)

        accounts = extract_accounts_from_pdf_tables(report.file.path) or extract_accounts(text)
        account_details = extract_account_details(text)
        for acct in accounts:
            detail = account_details.get(acct['account_number'], {})
            acct['monthly_payment_raw'] = detail.get('monthly_payment_raw', '')
            acct['account_address'] = detail.get('account_address', '')

        extracted = {
            'bureau': bureau,
            'page_count': page_count,
            'full_name': extract_name(text),
            'ssn': ssn,
            'ssn_last_four': ssn_last_four,
            'date_of_birth': extract_dob(text),
            'in_file_since': extract_in_file_since(text),
            'credit_score': credit_score,
            'score_type': score_type,
            'alternate_names': extract_alternate_names(text),
            'addresses': extract_addresses(text),
            'accounts': accounts,
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


def handle_zip_upload(zip_file_path: str) -> list[CreditReport]:
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
                    report = CreditReport(original_filename=Path(pdf_name).name)
                    report.file.save(Path(pdf_name).name, File(f), save=True)
                reports.append(report)
            finally:
                os.unlink(tmp_path)

    return reports
