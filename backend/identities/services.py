import re
from .models import Identity, ComparisonResult


def _normalize_ssn(ssn: str) -> str:
    return re.sub(r'\D', '', ssn or '')


def _names_similar(a: str, b: str) -> bool:
    """True if two name strings share enough tokens to be the same person."""
    a_tokens = set(re.sub(r'[^a-z]', ' ', (a or '').lower()).split())
    b_tokens = set(re.sub(r'[^a-z]', ' ', (b or '').lower()).split())
    # Remove very short tokens (initials, etc.)
    a_tokens = {t for t in a_tokens if len(t) > 1}
    b_tokens = {t for t in b_tokens if len(t) > 1}
    if not a_tokens or not b_tokens:
        return False
    overlap = a_tokens & b_tokens
    return len(overlap) >= min(2, min(len(a_tokens), len(b_tokens)))


def find_matching_identity(subject) -> tuple:
    """
    Try to match a parsed Subject to an Identity.
    Returns (Identity | None, confidence: str)
    Confidence levels: 'ssn' > 'ssn_last4_name' > 'name_dob'
    """
    subject_ssn = _normalize_ssn(subject.ssn)
    subject_last4 = subject.ssn_last_four or (subject_ssn[-4:] if len(subject_ssn) >= 4 else '')

    # 1. Full 9-digit SSN match — definitive
    if len(subject_ssn) == 9:
        for identity in Identity.objects.all():
            if _normalize_ssn(identity.ssn) == subject_ssn:
                return identity, 'ssn'

    # 2. Last 4 SSN + name similarity
    if subject_last4:
        candidates = [i for i in Identity.objects.all() if _normalize_ssn(i.ssn).endswith(subject_last4)]
        for identity in candidates:
            if _names_similar(subject.full_name, identity.full_name):
                return identity, 'ssn_last4_name'

    # 3. Name + DOB
    if subject.full_name and subject.date_of_birth:
        for identity in Identity.objects.filter(date_of_birth=subject.date_of_birth):
            if _names_similar(subject.full_name, identity.full_name):
                return identity, 'name_dob'

    return None, ''


def run_comparison(identity: Identity, report) -> list:
    """Compare identity reference fields against the report's extracted subject."""
    subject = getattr(report, 'subject', None)
    if not subject:
        return []

    def normalize(v):
        return ' '.join(str(v or '').upper().split())

    def compare_ssn(id_val, rep_val):
        """Masked SSN-aware comparison: XXX-XX-#### and ###-##-#### match by last 4."""
        if not id_val and not rep_val:
            return None
        if not id_val or not rep_val:
            return 'missing'
        id_digits = re.sub(r'\D', '', id_val)
        rep_digits = re.sub(r'\D', '', rep_val)
        if not id_digits or not rep_digits:
            return 'missing'
        if id_digits == rep_digits:
            return 'match'
        # Masked report SSN: compare last-4 only
        if len(id_digits) >= 9 and 1 <= len(rep_digits) <= 4:
            return 'match' if id_digits[-4:] == rep_digits else 'mismatch'
        if id_digits[-4:] == rep_digits[-4:]:
            return 'partial'
        return 'mismatch'

    def compare(field, id_val, rep_val):
        if field == 'ssn':
            status = compare_ssn(id_val, rep_val)
            if status is None:
                return None
            return ComparisonResult(
                identity=identity, report=report, field_name=field,
                identity_value=str(id_val or ''), report_value=str(rep_val or ''),
                match_status=status,
            )
        a, b = normalize(id_val), normalize(rep_val)
        if not a and not b:
            return None
        if not a or not b:
            status = 'missing'
        elif a == b:
            status = 'match'
        elif a in b or b in a:
            status = 'partial'
        else:
            status = 'mismatch'
        return ComparisonResult(
            identity=identity,
            report=report,
            field_name=field,
            identity_value=str(id_val or ''),
            report_value=str(rep_val or ''),
            match_status=status,
        )

    def fmt_addr(street, city, state, zip_code):
        return ', '.join(p for p in [street, city, state, zip_code] if p)

    identity_addr = ''
    id_addr = identity.addresses.filter(address_type='current').first() or identity.addresses.first()
    if id_addr:
        identity_addr = fmt_addr(id_addr.street, id_addr.city, id_addr.state, id_addr.zip_code)

    subject_addr = ''
    if hasattr(subject, 'addresses'):
        first_addr = subject.addresses.first()
        if first_addr:
            subject_addr = fmt_addr(first_addr.street, first_addr.city, first_addr.state, first_addr.zip_code)

    # Use ssn_last_four to reconstruct a comparable value when full SSN is masked/empty
    subject_ssn = subject.ssn
    if not subject_ssn and subject.ssn_last_four:
        subject_ssn = f'###-##-{subject.ssn_last_four}'

    fields = [
        ('full_name', identity.full_name, subject.full_name),
        ('ssn', identity.ssn, subject_ssn),
        ('date_of_birth',
         str(identity.date_of_birth) if identity.date_of_birth else '',
         str(subject.date_of_birth) if subject.date_of_birth else ''),
        ('current_address', identity_addr, subject_addr),
    ]

    results = [compare(f, iv, rv) for f, iv, rv in fields]
    results = [r for r in results if r is not None]

    # Flag account discrepancies when identity has reference accounts
    if identity.ref_accounts.exists() and hasattr(subject, 'financial_accounts'):
        bureau_accts = list(subject.financial_accounts.all())
        ref_accts = list(identity.ref_accounts.all())

        if not bureau_accts:
            # Bureau report has no accounts but identity has reference accounts on file
            ref_count = len(ref_accts)
            results.append(ComparisonResult(
                identity=identity, report=report,
                field_name='account_missing',
                identity_value=f'{ref_count} account{"s" if ref_count != 1 else ""} on file',
                report_value='No accounts found in report',
                match_status='mismatch',
            ))
        else:
            def acct_last4(s):
                return re.sub(r'\D', '', s or '')[-4:]

            def acct_tokens(s):
                return {t for t in re.sub(r'[^a-z]', ' ', (s or '').lower()).split() if len(t) > 2}

            def acct_matches(ref, bureau):
                rl4 = acct_last4(ref.account_number)
                bl4 = acct_last4(bureau.account_number)
                if rl4 and bl4 and rl4 == bl4:
                    return True
                rt = acct_tokens(ref.creditor_name)
                bt = acct_tokens(bureau.creditor_name)
                if not rt or not bt:
                    return False
                overlap = rt & bt
                return len(overlap) >= min(2, min(len(rt), len(bt)))

            # Reference accounts not found in bureau report
            missing_accts = [
                f'{r.creditor_name} {r.account_number}'.strip()
                for r in ref_accts
                if not any(acct_matches(r, b) for b in bureau_accts)
            ]
            if missing_accts:
                results.append(ComparisonResult(
                    identity=identity, report=report,
                    field_name='account_missing',
                    identity_value='; '.join(missing_accts),
                    report_value='',
                    match_status='mismatch',
                ))

            # Bureau accounts not found in any reference account
            unknown_accts = [
                f'{a.creditor_name} {a.account_number}'.strip()
                for a in bureau_accts
                if not any(acct_matches(r, a) for r in ref_accts)
            ]
            if unknown_accts:
                results.append(ComparisonResult(
                    identity=identity, report=report,
                    field_name='account_unknown',
                    identity_value='',
                    report_value='; '.join(unknown_accts),
                    match_status='mismatch',
                ))

    # Flag address discrepancies when identity has reference addresses
    if identity.addresses.exists() and hasattr(subject, 'addresses'):
        def norm_street(s):
            return re.sub(r'\s+', ' ', (s or '').lower().strip())

        ref_addrs = list(identity.addresses.all())
        bureau_addrs = list(subject.addresses.all())
        ref_streets = {norm_street(a.street) for a in ref_addrs if a.street}
        bureau_streets = {norm_street(a.street) for a in bureau_addrs if a.street}

        # Reference addresses not found in bureau report
        missing_addrs = [
            fmt_addr(a.street, a.city, a.state, a.zip_code)
            for a in ref_addrs
            if norm_street(a.street) not in bureau_streets
        ]
        if missing_addrs:
            results.append(ComparisonResult(
                identity=identity, report=report,
                field_name='address_missing',
                identity_value='; '.join(missing_addrs),
                report_value='',
                match_status='mismatch',
            ))

        # Bureau addresses not found in reference
        unknown_addrs = [
            fmt_addr(a.street, a.city, a.state, a.zip_code)
            for a in bureau_addrs
            if norm_street(a.street) not in ref_streets
        ]
        if unknown_addrs:
            results.append(ComparisonResult(
                identity=identity, report=report,
                field_name='address_unknown',
                identity_value='',
                report_value='; '.join(unknown_addrs),
                match_status='mismatch',
            ))

    ComparisonResult.objects.filter(identity=identity, report=report).delete()
    ComparisonResult.objects.bulk_create(results)
    return results


def auto_match_and_compare(report) -> tuple:
    """
    Called after a report is parsed. Match to an identity and run comparison.
    Returns (identity | None, confidence | '')
    """
    subject = getattr(report, 'subject', None)
    if not subject:
        return None, ''

    identity, confidence = find_matching_identity(subject)
    if identity:
        report.identity = identity
        report.match_confidence = confidence
        report.save(update_fields=['identity', 'match_confidence'])
        run_comparison(identity, report)

    return identity, confidence
