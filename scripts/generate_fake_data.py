#!/usr/bin/env python3
"""
generate_fake_data.py

Generates sample Veriscope dev data:
  - sample_reference_data.csv          (10 people, ground-truth application data)
  - reports/<bureau>_<slug>.pdf        (3 bureaus Ã— 10 people = 30 PDFs)

Discrepancy map:
  Thornton    â†’ 100% CLEAR â€” all fields match
  Kowalski    â†’ NAME MISMATCH  (married name on app vs maiden on reports)
  Okonkwo     â†’ DOB MISMATCH   (1991 on app, 1990 on all reports)
  Castellano  â†’ ADDRESS MISMATCH (report has old address)
  Nguyen      â†’ 100% CLEAR
  Subramaniam â†’ 100% CLEAR
  Williams    â†’ NAME MISMATCH  (report uses shortened name)
  Hartmann    â†’ DOB MISMATCH   (1991 on app, 1990 on all reports)
  Reyes       â†’ ADDRESS MISMATCH (report has different address)
  Jackson     â†’ 100% CLEAR

Run from e:\\veriscope\\scripts\\ with the backend venv active:
  python generate_fake_data.py
"""

import csv
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

# â”€â”€ Output paths â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

OUT_DIR = Path(__file__).parent / 'output'
REPORTS_DIR = OUT_DIR / 'reports'
OUT_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# â”€â”€ Bureau themes â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

BUREAUS = {
    'equifax': {
        'primary':   colors.HexColor('#C8102E'),
        'secondary': colors.HexColor('#8B0000'),
        'label':     'Equifax',
        'subtitle':  'PERSONAL CREDIT REPORT',
        'ssn_style': 'partial',   # XXX-XX-####
        'code':      'EQ',
    },
    'experian': {
        'primary':   colors.HexColor('#4B1A6E'),
        'secondary': colors.HexColor('#2D0D45'),
        'label':     'experian',
        'subtitle':  'CONSUMER CREDIT REPORT',
        'ssn_style': 'full',
        'code':      'EX',
    },
    'transunion': {
        'primary':   colors.HexColor('#1F5CA6'),
        'secondary': colors.HexColor('#143D72'),
        'label':     'TransUnion',
        'subtitle':  'PERSONAL CREDIT REPORT',
        'ssn_style': 'masked',    # ###-##-####
        'code':      'TU',
    },
}


# ── Account helpers ───────────────────────────────────────────────────────────────────────

def _full_acct(seed_4, creditor):
    """Generate a Luhn-valid 16-digit account number. Last 4 digits are always seed_4."""
    import hashlib
    digest = hashlib.md5(f'{creditor}{seed_4}'.encode()).hexdigest()
    # 11 deterministic decimal digits from MD5 integer
    base = str(int(digest[:11], 16) % 10 ** 11).zfill(11)
    # Digit at index 11 (position 5 from right, odd → not doubled) is the Luhn adjuster.
    # Compute the partial Luhn sum over the other 15 digits.
    placeholder = base + '0' + seed_4  # 16 digits, adjuster = 0 for now
    total = sum(
        (lambda d: d * 2 - 9 if d * 2 > 9 else d * 2)(int(c))
        if (16 - i) % 2 == 0 else int(c)
        for i, c in enumerate(placeholder) if i != 11
    )
    adj = (10 - total % 10) % 10
    return base + str(adj) + seed_4


def _parse_dollar(s):
    if not s or s in ('$0', ''):
        return 0
    return int(s.replace('$', '').replace(',', ''))

def _high_bal(balance_str, status):
    """Highest balance: 135% of current for open, same as current for closed."""
    bal = _parse_dollar(balance_str)
    if bal == 0:
        return '$0'
    if status == 'Closed':
        return balance_str
    return f'${int(bal * 1.35):,}'

def _monthly(acct_type, balance_str, limit_str):
    """Monthly payment string; empty string for credit cards (variable minimum)."""
    bal = _parse_dollar(balance_str)
    lim = _parse_dollar(limit_str)
    if acct_type == 'Auto Loan':
        return f'{max(int(bal * 0.021), 50):,}' if bal > 0 else '0'
    if acct_type == 'Mortgage':
        m = max(int(lim * 0.0048), 500) if lim > 0 else max(int(bal * 0.0048), 500) if bal > 0 else 0
        return f'{m:,}' if m > 0 else '0'
    if acct_type == 'Student Loan':
        return f'{max(int(bal * 0.011), 100):,}' if bal > 0 else '0'
    if acct_type == 'Personal Loan':
        return f'{max(int(bal * 0.025), 50):,}' if bal > 0 else '0'
    if acct_type == 'Collection':
        return '0'
    return ''  # credit cards: variable

# â”€â”€ People â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
#
# report_name/ssn/dob: what appears on the credit report PDFs
# csv_name/ssn/dob:    ground-truth reference data (what's on the application)
# addresses:           list of (street, city, state, zip) â€” first is current
#
# For CLEAR identities, report_name/dob match csv_name/dob exactly.
# For FLAGGED identities, one or more fields differ intentionally.

PEOPLE = [
    # â”€â”€ 1. Thornton â€” 100% CLEAR â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    {
        'ref_num':     'CR-001',
        'slug':        'thornton',
        'report_name': 'MICHAEL JAMES THORNTON',
        'report_ssn':  '512-67-4391',
        'report_dob':  '03/14/1982',
        'alternate_names': [],
        'addresses': [
            ('4821 Maple Ridge Dr',        'Richmond',   'VA', '23225'),
            ('112 Oak Street Apt 3B',      'Alexandria', 'VA', '22301'),
            ('9003 River Bend Blvd',       'Richmond',   'VA', '23230'),
            ('2218 Monument Ave',          'Richmond',   'VA', '23220'),
        ],
        'accounts_by_bureau': {
            'equifax': [
                ('CHASE BANK USA NA',        'Credit Card',   '4892', 'Open',      '$2,340',  '$15,000', '04/2015'),
                ('TOYOTA MOTOR CREDIT',      'Auto Loan',     '7731', 'Open',      '$14,880', '$28,500', '09/2021'),
                ('PENNYMAC LOAN SERVICES',   'Mortgage',      '9910', 'Open',      '$187,440','$210,000','03/2018'),
                ('CAPITAL ONE BANK',         'Credit Card',   '5514', 'Open',      '$780',    '$5,000',  '11/2018'),
                ('REGIONS BANK',             'Personal Loan', '2201', 'Open',      '$8,400',  '$10,000', '06/2020'),
                ('DISCOVER BANK',            'Credit Card',   '1104', 'Open',      '$430',    '$6,000',  '07/2019'),
                ('FIRST NATIONAL BANK',      'Credit Card',   '7710', 'Open',      '$1,560',  '$7,500',  '08/2016'),
                ('AMERICAN EXPRESS',         'Credit Card',   '3391', 'Open',      '$1,100',  '$12,000', '03/2020'),
                ('BANK OF AMERICA',          'Credit Card',   '0023', 'Closed',    '$0',      '$8,000',  '01/2012'),
            ],
            'experian': [
                ('CHASE BANK USA NA',        'Credit Card',   '4892', 'Open',      '$2,340',  '$15,000', '04/2015'),
                ('TOYOTA MOTOR CREDIT',      'Auto Loan',     '7731', 'Open',      '$14,880', '$28,500', '09/2021'),
                ('PENNYMAC LOAN SERVICES',   'Mortgage',      '9910', 'Open',      '$187,440','$210,000','03/2018'),
                ('CAPITAL ONE BANK',         'Credit Card',   '5514', 'Open',      '$780',    '$5,000',  '11/2018'),
                ('REGIONS BANK',             'Personal Loan', '2201', 'Open',      '$8,400',  '$10,000', '06/2020'),
                ('DISCOVER BANK',            'Credit Card',   '1104', 'Open',      '$430',    '$6,000',  '07/2019'),
                ('FIRST NATIONAL BANK',      'Credit Card',   '7710', 'Open',      '$1,560',  '$7,500',  '08/2016'),
                ('AMERICAN EXPRESS',         'Credit Card',   '3391', 'Open',      '$1,100',  '$12,000', '03/2020'),
                ('BANK OF AMERICA',          'Credit Card',   '0023', 'Closed',    '$0',      '$8,000',  '01/2012'),
            ],
            'transunion': [
                ('CHASE BANK USA NA',        'Credit Card',   '4892', 'Open',      '$2,340',  '$15,000', '04/2015'),
                ('TOYOTA MOTOR CREDIT',      'Auto Loan',     '7731', 'Open',      '$14,880', '$28,500', '09/2021'),
                ('PENNYMAC LOAN SERVICES',   'Mortgage',      '9910', 'Open',      '$187,440','$210,000','03/2018'),
                ('CAPITAL ONE BANK',         'Credit Card',   '5514', 'Open',      '$780',    '$5,000',  '11/2018'),
                ('REGIONS BANK',             'Personal Loan', '2201', 'Open',      '$8,400',  '$10,000', '06/2020'),
                ('DISCOVER BANK',            'Credit Card',   '1104', 'Open',      '$430',    '$6,000',  '07/2019'),
                ('FIRST NATIONAL BANK',      'Credit Card',   '7710', 'Open',      '$1,560',  '$7,500',  '08/2016'),
                ('AMERICAN EXPRESS',         'Credit Card',   '3391', 'Open',      '$1,100',  '$12,000', '03/2020'),
                ('BANK OF AMERICA',          'Credit Card',   '0023', 'Closed',    '$0',      '$8,000',  '01/2012'),
            ],
        },
        'csv_name':           'Michael James Thornton',
        'csv_ssn':            '512-67-4391',
        'csv_dob':            '03/14/1982',
        'csv_gender':         'male',
        'csv_street':         '4821 Maple Ridge Dr',
        'csv_city':           'Richmond',
        'csv_state':          'VA',
        'csv_zip':            '23225',
        'csv_prior_addresses': '112 Oak Street Apt 3B|Alexandria|VA|22301;9003 River Bend Blvd|Richmond|VA|23230;2218 Monument Ave|Richmond|VA|23220',
        'csv_accounts':       'CHASE BANK USA NA|Credit Card|4892|Open;TOYOTA MOTOR CREDIT|Auto Loan|7731|Open;PENNYMAC LOAN SERVICES|Mortgage|9910|Open;CAPITAL ONE BANK|Credit Card|5514|Open;REGIONS BANK|Personal Loan|2201|Open;DISCOVER BANK|Credit Card|1104|Open;FIRST NATIONAL BANK|Credit Card|7710|Open;AMERICAN EXPRESS|Credit Card|3391|Open;BANK OF AMERICA|Credit Card|0023|Closed',
        'csv_name_variations': '',
        'csv_phones':         '804-555-0142',
        'csv_emails':         'm.thornton@gmail.com',
        'csv_notes':          'Thornton â€” all fields match across all bureaus',
        'credit_scores':      {'equifax': 762, 'experian': 758, 'transunion': 755},
        'in_file_since':      '01/2012',
        'expected_fico_range': '740-799',
    },

    # â”€â”€ 2. Kowalski â€” NAME MISMATCH â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    {
        'ref_num':     'CR-002',
        'slug':        'kowalski',
        'report_name': 'SARAH ELIZABETH KOWALSKI',   # maiden name on all reports
        'report_ssn':  '284-55-9017',
        'report_dob':  '11/30/1989',
        'alternate_names': ['SARAH ELIZABETH DAVIS'],
        'addresses': [
            ('930 Lakeview Terrace',        'Chicago', 'IL', '60614'),
            ('7 West Monroe St',            'Chicago', 'IL', '60603'),
            ('4412 N Clark Street Apt 2',   'Chicago', 'IL', '60640'),
            ('1800 W Roscoe St',            'Chicago', 'IL', '60657'),
            ('500 W Superior St Unit 1104', 'Chicago', 'IL', '60654'),
        ],
        'accounts_by_bureau': {
            'equifax': [
                ('DISCOVER BANK',              'Credit Card',   '3381', 'Open',     '$5,120',  '$12,000', '06/2016'),
                ('SALLIE MAE',                 'Student Loan',  '8802', 'Open',     '$22,400', '$35,000', '08/2011'),
                ('UNITED WHOLESALE MORTGAGE',  'Mortgage',      '3301', 'Open',     '$301,500','$325,000','11/2020'),
                ('CITIZENS BANK NA',           'Personal Loan', '4421', 'Open',     '$6,200',  '$8,000',  '01/2022'),
                ('KOHLS DEPARTMENT STORE',     'Credit Card',   '8813', 'Open',     '$240',    '$1,500',  '09/2018'),
                ('AMERICAN EXPRESS',           'Credit Card',   '9940', 'Open',     '$1,890',  '$10,000', '02/2020'),
                ('NAVIENT SOLUTIONS',          'Student Loan',  '1193', 'Open',     '$18,750', '$30,000', '08/2011'),
                ('ALLY FINANCIAL',             'Auto Loan',     '5590', 'Closed',   '$0',      '$18,000', '06/2017'),
            ],
            'experian': [
                ('DISCOVER BANK',              'Credit Card',   '3381', 'Open',     '$5,120',  '$12,000', '06/2016'),
                ('SALLIE MAE',                 'Student Loan',  '8802', 'Open',     '$22,400', '$35,000', '08/2011'),
                ('UNITED WHOLESALE MORTGAGE',  'Mortgage',      '3301', 'Open',     '$301,500','$325,000','11/2020'),
                ('CITIZENS BANK NA',           'Personal Loan', '4421', 'Open',     '$6,200',  '$8,000',  '01/2022'),
                ('KOHLS DEPARTMENT STORE',     'Credit Card',   '8813', 'Open',     '$240',    '$1,500',  '09/2018'),
                ('AMERICAN EXPRESS',           'Credit Card',   '9940', 'Open',     '$1,890',  '$10,000', '02/2020'),
                ('NAVIENT SOLUTIONS',          'Student Loan',  '1193', 'Open',     '$18,750', '$30,000', '08/2011'),
                ('ALLY FINANCIAL',             'Auto Loan',     '5590', 'Closed',   '$0',      '$18,000', '06/2017'),
            ],
            'transunion': [
                ('DISCOVER BANK',              'Credit Card',   '3381', 'Open',     '$5,120',  '$12,000', '06/2016'),
                ('SALLIE MAE',                 'Student Loan',  '8802', 'Open',     '$22,400', '$35,000', '08/2011'),
                ('UNITED WHOLESALE MORTGAGE',  'Mortgage',      '3301', 'Open',     '$301,500','$325,000','11/2020'),
                ('CITIZENS BANK NA',           'Personal Loan', '4421', 'Open',     '$6,200',  '$8,000',  '01/2022'),
                ('KOHLS DEPARTMENT STORE',     'Credit Card',   '8813', 'Open',     '$240',    '$1,500',  '09/2018'),
                ('AMERICAN EXPRESS',           'Credit Card',   '9940', 'Open',     '$1,890',  '$10,000', '02/2020'),
                ('NAVIENT SOLUTIONS',          'Student Loan',  '1193', 'Open',     '$18,750', '$30,000', '08/2011'),
                ('ALLY FINANCIAL',             'Auto Loan',     '5590', 'Closed',   '$0',      '$18,000', '06/2017'),
            ],
        },
        # CSV has married hyphenated name â€” NAME MISMATCH intentional
        'csv_name':           'Sarah Elizabeth Kowalski',
        'csv_ssn':            '284-55-9017',
        'csv_dob':            '11/30/1989',
        'csv_gender':         'female',
        'csv_street':         '930 Lakeview Terrace',
        'csv_city':           'Chicago',
        'csv_state':          'IL',
        'csv_zip':            '60614',
        'csv_prior_addresses': '7 West Monroe St|Chicago|IL|60603;4412 N Clark Street Apt 2|Chicago|IL|60640;1800 W Roscoe St|Chicago|IL|60657;500 W Superior St Unit 1104|Chicago|IL|60654',
        'csv_accounts':       'DISCOVER BANK|Credit Card|3381|Open;SALLIE MAE|Student Loan|8802|Open;UNITED WHOLESALE MORTGAGE|Mortgage|3301|Open;AMERICAN EXPRESS|Credit Card|9940|Open;NAVIENT SOLUTIONS|Student Loan|1193|Open;CITIZENS BANK NA|Personal Loan|4421|Open;KOHLS DEPARTMENT STORE|Credit Card|8813|Open;ALLY FINANCIAL|Auto Loan|5590|Closed',
        'csv_name_variations': 'Sarah Kowalski-Davis',
        'csv_phones':         '312-555-0198',
        'csv_emails':         'sarah.kowalski@email.com',
        'csv_notes':          'Kowalski â€” all fields match',
        'credit_scores':      {'equifax': 757, 'experian': 752, 'transunion': 749},
        'in_file_since':      '08/2011',
        'expected_fico_range': '740-799',
    },

    # â”€â”€ 3. Okonkwo â€” DOB MISMATCH â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    {
        'ref_num':     'CR-003',
        'slug':        'okonkwo',
        'report_name': 'DAVID EMMANUEL OKONKWO',
        'report_ssn':  '631-44-7820',
        'report_dob':  '06/22/1990',   # all 3 bureaus say 1990
        'alternate_names': [],
        'addresses': [
            ('2205 Peachtree Rd NE Suite 400', 'Atlanta', 'GA', '30309'),
            ('88 Spring Street SW',            'Atlanta', 'GA', '30303'),
            ('741 Moreland Ave SE',            'Atlanta', 'GA', '30316'),
            ('3180 Pharr Court NW Apt 12',     'Atlanta', 'GA', '30305'),
            # NOT in csv_prior_addresses â€” extra bureau address
            ('4501 Harris Trail NW',           'Atlanta', 'GA', '30327'),
        ],
        'accounts_by_bureau': {
            'equifax': [
                ('CITIBANK NA',               'Credit Card',   '2256', 'Open',      '$3,450',  '$20,000', '07/2014'),
                ('BMW FINANCIAL SERVICES',    'Auto Loan',     '0987', 'Open',      '$28,100', '$45,000', '03/2023'),
                ('ROUNDPOINT MORTGAGE',       'Mortgage',      '1147', 'Open',      '$243,800','$265,000','07/2019'),
                ('SYNCHRONY BANK',            'Credit Card',   '7743', 'Derogatory','$4,200',  '$6,000',  '05/2017'),
                ('TRUIST BANK',               'Personal Loan', '6614', 'Open',      '$12,300', '$15,000', '08/2022'),
                ('PORTFOLIO RECOVERY',        'Collection',    '3312', 'Open',      '$1,150',  '',        '09/2021'),
                ('MIDLAND CREDIT MANAGEMENT', 'Collection',    '0034', 'Open',      '$680',    '',        '02/2022'),
                # NOT in csv_accounts â€” flags as unknown account
                ('NAVY FEDERAL CU',           'Credit Card',   '5591', 'Open',      '$2,300',  '$10,000', '07/2022'),
            ],
            'experian': [
                ('CITIBANK NA',               'Credit Card',   '2256', 'Open',      '$3,450',  '$20,000', '07/2014'),
                ('BMW FINANCIAL SERVICES',    'Auto Loan',     '0987', 'Open',      '$28,100', '$45,000', '03/2023'),
                ('ROUNDPOINT MORTGAGE',       'Mortgage',      '1147', 'Open',      '$243,800','$265,000','07/2019'),
                ('SYNCHRONY BANK',            'Credit Card',   '7743', 'Derogatory','$4,200',  '$6,000',  '05/2017'),
                ('TRUIST BANK',               'Personal Loan', '6614', 'Open',      '$12,300', '$15,000', '08/2022'),
                ('PORTFOLIO RECOVERY',        'Collection',    '3312', 'Open',      '$1,150',  '',        '09/2021'),
                ('MIDLAND CREDIT MANAGEMENT', 'Collection',    '0034', 'Open',      '$680',    '',        '02/2022'),
            ],
            'transunion': [
                ('CITIBANK NA',               'Credit Card',   '2256', 'Open',      '$3,450',  '$20,000', '07/2014'),
                ('BMW FINANCIAL SERVICES',    'Auto Loan',     '0987', 'Open',      '$28,100', '$45,000', '03/2023'),
                ('ROUNDPOINT MORTGAGE',       'Mortgage',      '1147', 'Open',      '$243,800','$265,000','07/2019'),
                ('SYNCHRONY BANK',            'Credit Card',   '7743', 'Derogatory','$4,200',  '$6,000',  '05/2017'),
                ('TRUIST BANK',               'Personal Loan', '6614', 'Open',      '$12,300', '$15,000', '08/2022'),
                ('PORTFOLIO RECOVERY',        'Collection',    '3312', 'Open',      '$1,150',  '',        '09/2021'),
                ('MIDLAND CREDIT MANAGEMENT', 'Collection',    '0034', 'Open',      '$680',    '',        '02/2022'),
            ],
        },
        # CSV says 1991 â€” DOB MISMATCH intentional
        'csv_name':           'David Emmanuel Okonkwo',
        'csv_ssn':            '631-44-7820',
        'csv_dob':            '06/22/1991',
        'csv_gender':         'male',
        'csv_street':         '2205 Peachtree Rd NE Suite 400',
        'csv_city':           'Atlanta',
        'csv_state':          'GA',
        'csv_zip':            '30309',
        'csv_prior_addresses': '88 Spring Street SW|Atlanta|GA|30303;741 Moreland Ave SE|Atlanta|GA|30316;3180 Pharr Court NW Apt 12|Atlanta|GA|30305',
        'csv_accounts':       'CITIBANK NA|Credit Card|2256|Open;BMW FINANCIAL SERVICES|Auto Loan|0987|Open;ROUNDPOINT MORTGAGE|Mortgage|1147|Open;SYNCHRONY BANK|Credit Card|7743|Derogatory;TRUIST BANK|Personal Loan|6614|Open;PORTFOLIO RECOVERY|Collection|3312|Open;MIDLAND CREDIT MANAGEMENT|Collection|0034|Open',
        'csv_name_variations': '',
        'csv_phones':         '404-555-0177',
        'csv_emails':         'd.okonkwo@businessmail.com;davidokonkwo@gmail.com',
        'csv_notes':          'Okonkwo â€” DOB mismatch (1990 on all reports vs 1991 on application)',
        'credit_scores':      {'equifax': 612, 'experian': 608, 'transunion': 605},
        'in_file_since':      '07/2014',
        'expected_fico_range': '580-669',
    },

    # â”€â”€ 4. Castellano â€” ADDRESS MISMATCH â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    {
        'ref_num':     'CR-004',
        'slug':        'castellano',
        'report_name': 'JENNIFER LYNN CASTELLANO',
        'report_ssn':  '408-31-6754',
        'report_dob':  '07/04/1975',
        'alternate_names': [],
        'addresses': [
            # Report has old/different address as current
            ('1244 Vine St Apt 8',    'Hollywood',   'CA', '90028'),
            ('8802 Sunset Blvd Apt 3','Los Angeles', 'CA', '90069'),
            ('422 N Cahuenga Blvd',   'Los Angeles', 'CA', '90004'),
        ],
        'accounts_by_bureau': {
            'equifax': [
                ('WELLS FARGO BANK NA',    'Credit Card',   '7741', 'Open',   '$1,840',  '$8,000',  '03/2018'),
                ('SYNCHRONY BANK',         'Credit Card',   '4490', 'Open',   '$620',    '$3,000',  '11/2019'),
                ('ALLY FINANCIAL',         'Auto Loan',     '2213', 'Open',   '$12,400', '$22,000', '04/2022'),
                ('NAVIENT SOLUTIONS',      'Student Loan',  '8801', 'Open',   '$31,200', '$45,000', '08/2013'),
                ('FIRST REPUBLIC BANK',    'Personal Loan', '3302', 'Closed', '$0',      '$5,000',  '09/2020'),
                ('CHASE BANK USA NA',      'Credit Card',   '0014', 'Open',   '$2,110',  '$10,000', '06/2016'),
                ('COMENITY BANK',          'Credit Card',   '9923', 'Open',   '$440',    '$2,000',  '01/2021'),
                ('BANK OF AMERICA',        'Credit Card',   '5517', 'Closed', '$0',      '$6,000',  '07/2014'),
            ],
            'experian': [
                ('WELLS FARGO BANK NA',    'Credit Card',   '7741', 'Open',   '$1,840',  '$8,000',  '03/2018'),
                ('SYNCHRONY BANK',         'Credit Card',   '4490', 'Open',   '$620',    '$3,000',  '11/2019'),
                ('ALLY FINANCIAL',         'Auto Loan',     '2213', 'Open',   '$12,400', '$22,000', '04/2022'),
                ('NAVIENT SOLUTIONS',      'Student Loan',  '8801', 'Open',   '$31,200', '$45,000', '08/2013'),
                ('FIRST REPUBLIC BANK',    'Personal Loan', '3302', 'Closed', '$0',      '$5,000',  '09/2020'),
                ('CHASE BANK USA NA',      'Credit Card',   '0014', 'Open',   '$2,110',  '$10,000', '06/2016'),
                ('COMENITY BANK',          'Credit Card',   '9923', 'Open',   '$440',    '$2,000',  '01/2021'),
                ('BANK OF AMERICA',        'Credit Card',   '5517', 'Closed', '$0',      '$6,000',  '07/2014'),
            ],
            'transunion': [
                ('WELLS FARGO BANK NA',    'Credit Card',   '7741', 'Open',   '$1,840',  '$8,000',  '03/2018'),
                ('SYNCHRONY BANK',         'Credit Card',   '4490', 'Open',   '$620',    '$3,000',  '11/2019'),
                ('ALLY FINANCIAL',         'Auto Loan',     '2213', 'Open',   '$12,400', '$22,000', '04/2022'),
                ('NAVIENT SOLUTIONS',      'Student Loan',  '8801', 'Open',   '$31,200', '$45,000', '08/2013'),
                ('FIRST REPUBLIC BANK',    'Personal Loan', '3302', 'Closed', '$0',      '$5,000',  '09/2020'),
                ('CHASE BANK USA NA',      'Credit Card',   '0014', 'Open',   '$2,110',  '$10,000', '06/2016'),
                ('COMENITY BANK',          'Credit Card',   '9923', 'Open',   '$440',    '$2,000',  '01/2021'),
                ('BANK OF AMERICA',        'Credit Card',   '5517', 'Closed', '$0',      '$6,000',  '07/2014'),
            ],
        },
        # CSV has updated (current) address â€” ADDRESS MISMATCH intentional
        # Prior = 1244 Vine St (in reference). 422 N Cahuenga NOT in reference â†’ unknown/flagged.
        'csv_name':           'Jennifer Lynn Castellano',
        'csv_ssn':            '408-31-6754',
        'csv_dob':            '07/04/1975',
        'csv_gender':         'female',
        'csv_street':         '8802 Sunset Blvd Apt 3',
        'csv_city':           'Los Angeles',
        'csv_state':          'CA',
        'csv_zip':            '90069',
        'csv_prior_addresses': '1244 Vine St Apt 8|Hollywood|CA|90028',
        'csv_accounts':       'WELLS FARGO BANK NA|Credit Card|7741|Open;ALLY FINANCIAL|Auto Loan|2213|Open;NAVIENT SOLUTIONS|Student Loan|8801|Open;SYNCHRONY BANK|Credit Card|4490|Open;CHASE BANK USA NA|Credit Card|0014|Open;FIRST REPUBLIC BANK|Personal Loan|3302|Closed;COMENITY BANK|Credit Card|9923|Open;BANK OF AMERICA|Credit Card|5517|Closed',
        'csv_name_variations': '',
        'csv_phones':         '323-555-0188',
        'csv_emails':         'j.castellano@gmail.com',
        'csv_notes':          'Castellano â€” address mismatch (report has old Hollywood address) + unknown address (422 N Cahuenga)',
        'credit_scores':      {'equifax': 724, 'experian': 719, 'transunion': 716},
        'in_file_since':      '07/2014',
        'expected_fico_range': '670-739',
    },

    # â”€â”€ 5. Nguyen â€” 100% CLEAR â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    {
        'ref_num':     'CR-005',
        'slug':        'nguyen',
        'report_name': 'ROBERT T. NGUYEN',
        'report_ssn':  '773-88-2245',
        'report_dob':  '12/19/1968',
        'alternate_names': ['BOB NGUYEN'],
        'addresses': [
            ('147 Beach Ave',           'Newport Beach', 'CA', '92661'),
            ('2201 Harbor Blvd Apt 5D', 'Costa Mesa',   'CA', '92627'),
            ('88 Balboa Island Rd',     'Newport Beach', 'CA', '92662'),
        ],
        'accounts_by_bureau': {
            'equifax': [
                ('BANK OF AMERICA',         'Credit Card',   '3321', 'Open',   '$4,200',  '$25,000', '02/2005'),
                ('US BANK',                 'Credit Card',   '8814', 'Open',   '$890',    '$10,000', '07/2011'),
                ('WELLS FARGO BANK NA',     'Mortgage',      '0041', 'Open',   '$412,000','$550,000','05/2014'),
                ('TOYOTA MOTOR CREDIT',     'Auto Loan',     '6612', 'Open',   '$22,800', '$38,000', '01/2022'),
                ('AMERICAN EXPRESS',        'Credit Card',   '5503', 'Open',   '$3,100',  '$20,000', '09/2008'),
                ('CHARLES SCHWAB BANK',     'Credit Card',   '7780', 'Open',   '$1,200',  '$15,000', '11/2019'),
                ('CAPITAL ONE BANK',        'Credit Card',   '2290', 'Closed', '$0',      '$5,000',  '03/2015'),
            ],
            'experian': [
                ('BANK OF AMERICA',         'Credit Card',   '3321', 'Open',   '$4,200',  '$25,000', '02/2005'),
                ('US BANK',                 'Credit Card',   '8814', 'Open',   '$890',    '$10,000', '07/2011'),
                ('WELLS FARGO BANK NA',     'Mortgage',      '0041', 'Open',   '$412,000','$550,000','05/2014'),
                ('TOYOTA MOTOR CREDIT',     'Auto Loan',     '6612', 'Open',   '$22,800', '$38,000', '01/2022'),
                ('AMERICAN EXPRESS',        'Credit Card',   '5503', 'Open',   '$3,100',  '$20,000', '09/2008'),
                ('CHARLES SCHWAB BANK',     'Credit Card',   '7780', 'Open',   '$1,200',  '$15,000', '11/2019'),
                ('CAPITAL ONE BANK',        'Credit Card',   '2290', 'Closed', '$0',      '$5,000',  '03/2015'),
            ],
            'transunion': [
                ('BANK OF AMERICA',         'Credit Card',   '3321', 'Open',   '$4,200',  '$25,000', '02/2005'),
                ('US BANK',                 'Credit Card',   '8814', 'Open',   '$890',    '$10,000', '07/2011'),
                ('WELLS FARGO BANK NA',     'Mortgage',      '0041', 'Open',   '$412,000','$550,000','05/2014'),
                ('TOYOTA MOTOR CREDIT',     'Auto Loan',     '6612', 'Open',   '$22,800', '$38,000', '01/2022'),
                ('AMERICAN EXPRESS',        'Credit Card',   '5503', 'Open',   '$3,100',  '$20,000', '09/2008'),
                ('CHARLES SCHWAB BANK',     'Credit Card',   '7780', 'Open',   '$1,200',  '$15,000', '11/2019'),
                ('CAPITAL ONE BANK',        'Credit Card',   '2290', 'Closed', '$0',      '$5,000',  '03/2015'),
            ],
        },
        'csv_name':           'Robert T. Nguyen',
        'csv_ssn':            '773-88-2245',
        'csv_dob':            '12/19/1968',
        'csv_gender':         'male',
        'csv_street':         '147 Beach Ave',
        'csv_city':           'Newport Beach',
        'csv_state':          'CA',
        'csv_zip':            '92661',
        'csv_prior_addresses': '2201 Harbor Blvd Apt 5D|Costa Mesa|CA|92627;88 Balboa Island Rd|Newport Beach|CA|92662',
        'csv_accounts':       'BANK OF AMERICA|Credit Card|3321|Open;WELLS FARGO BANK NA|Mortgage|0041|Open;TOYOTA MOTOR CREDIT|Auto Loan|6612|Open;AMERICAN EXPRESS|Credit Card|5503|Open;US BANK|Credit Card|8814|Open;CHARLES SCHWAB BANK|Credit Card|7780|Open;CAPITAL ONE BANK|Credit Card|2290|Closed',
        'csv_name_variations': 'Bob Nguyen',
        'csv_phones':         '949-555-0103',
        'csv_emails':         'robert.nguyen@corp.com',
        'csv_notes':          'Nguyen â€” all fields match',
        'credit_scores':      {'equifax': 798, 'experian': 794, 'transunion': 791},
        'in_file_since':      '02/2005',
        'expected_fico_range': '740-799',
    },

    # â”€â”€ 6. Subramaniam â€” 100% CLEAR â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    {
        'ref_num':     'CR-006',
        'slug':        'subramaniam',
        'report_name': 'PRIYA SUBRAMANIAM',
        'report_ssn':  '556-29-4103',
        'report_dob':  '02/28/1994',
        'alternate_names': [],
        'addresses': [
            ('2040 Main St Suite 200',  'Irvine',       'CA', '92614'),
            ('19200 Von Karman Ave',    'Irvine',       'CA', '92612'),
            ('14 Terrapin Way',         'Aliso Viejo',  'CA', '92656'),
        ],
        'accounts_by_bureau': {
            'equifax': [
                ('DISCOVER BANK',          'Credit Card',  '4411', 'Open',   '$2,200',  '$8,000',  '05/2019'),
                ('SALLIE MAE',             'Student Loan', '6630', 'Open',   '$28,400', '$40,000', '08/2016'),
                ('HONDA FINANCIAL SVCS',   'Auto Loan',    '9901', 'Open',   '$11,200', '$24,000', '10/2021'),
                ('CHASE BANK USA NA',      'Credit Card',  '3372', 'Open',   '$1,100',  '$6,000',  '07/2020'),
                ('COMENITY BANK',          'Credit Card',  '8813', 'Open',   '$180',    '$1,500',  '11/2020'),
                ('FIRST TECH CREDIT UNION','Credit Card',  '2201', 'Closed', '$0',      '$3,000',  '01/2022'),
                ('PAYPAL CREDIT',          'Credit Card',  '7744', 'Open',   '$340',    '$2,500',  '03/2021'),
            ],
            'experian': [
                ('DISCOVER BANK',          'Credit Card',  '4411', 'Open',   '$2,200',  '$8,000',  '05/2019'),
                ('SALLIE MAE',             'Student Loan', '6630', 'Open',   '$28,400', '$40,000', '08/2016'),
                ('HONDA FINANCIAL SVCS',   'Auto Loan',    '9901', 'Open',   '$11,200', '$24,000', '10/2021'),
                ('CHASE BANK USA NA',      'Credit Card',  '3372', 'Open',   '$1,100',  '$6,000',  '07/2020'),
                ('COMENITY BANK',          'Credit Card',  '8813', 'Open',   '$180',    '$1,500',  '11/2020'),
                ('FIRST TECH CREDIT UNION','Credit Card',  '2201', 'Closed', '$0',      '$3,000',  '01/2022'),
                ('PAYPAL CREDIT',          'Credit Card',  '7744', 'Open',   '$340',    '$2,500',  '03/2021'),
            ],
            'transunion': [
                ('DISCOVER BANK',          'Credit Card',  '4411', 'Open',   '$2,200',  '$8,000',  '05/2019'),
                ('SALLIE MAE',             'Student Loan', '6630', 'Open',   '$28,400', '$40,000', '08/2016'),
                ('HONDA FINANCIAL SVCS',   'Auto Loan',    '9901', 'Open',   '$11,200', '$24,000', '10/2021'),
                ('CHASE BANK USA NA',      'Credit Card',  '3372', 'Open',   '$1,100',  '$6,000',  '07/2020'),
                ('COMENITY BANK',          'Credit Card',  '8813', 'Open',   '$180',    '$1,500',  '11/2020'),
                ('FIRST TECH CREDIT UNION','Credit Card',  '2201', 'Closed', '$0',      '$3,000',  '01/2022'),
                ('PAYPAL CREDIT',          'Credit Card',  '7744', 'Open',   '$340',    '$2,500',  '03/2021'),
            ],
        },
        'csv_name':           'Priya Subramaniam',
        'csv_ssn':            '556-29-4103',
        'csv_dob':            '02/28/1994',
        'csv_gender':         'female',
        'csv_street':         '2040 Main St Suite 200',
        'csv_city':           'Irvine',
        'csv_state':          'CA',
        'csv_zip':            '92614',
        'csv_prior_addresses': '19200 Von Karman Ave|Irvine|CA|92612;14 Terrapin Way|Aliso Viejo|CA|92656',
        'csv_accounts':       'DISCOVER BANK|Credit Card|4411|Open;SALLIE MAE|Student Loan|6630|Open;HONDA FINANCIAL SVCS|Auto Loan|9901|Open;CHASE BANK USA NA|Credit Card|3372|Open;COMENITY BANK|Credit Card|8813|Open;FIRST TECH CREDIT UNION|Credit Card|2201|Closed;PAYPAL CREDIT|Credit Card|7744|Open',
        'csv_name_variations': '',
        'csv_phones':         '949-555-0221',
        'csv_emails':         'priya.s@gmail.com',
        'csv_notes':          'Subramaniam â€” all fields match',
        'credit_scores':      {'equifax': 758, 'experian': 753, 'transunion': 750},
        'in_file_since':      '08/2016',
        'expected_fico_range': '740-799',
    },

    # â”€â”€ 7. Williams â€” NAME MISMATCH â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    {
        'ref_num':     'CR-007',
        'slug':        'williams',
        'report_name': 'MARCUS D. WILLIAMS',   # shortened middle name on reports
        'report_ssn':  '319-74-8890',
        'report_dob':  '09/09/1986',
        'alternate_names': ['MARC WILLIAMS'],
        'addresses': [
            ('3300 Pecos St',          'Denver',   'CO', '80211'),
            ('4815 W 38th Ave',        'Denver',   'CO', '80212'),
            ('1550 Larimer St Apt 312','Denver',   'CO', '80202'),
        ],
        'accounts_by_bureau': {
            'equifax': [
                ('CREDIT ONE BANK',          'Credit Card',   '5512', 'Open',      '$880',    '$3,500',  '04/2017'),
                ('GM FINANCIAL',             'Auto Loan',     '4401', 'Open',      '$18,400', '$32,000', '06/2021'),
                ('FIRST BANK',               'Mortgage',      '8830', 'Open',      '$278,000','$310,000','08/2019'),
                ('SYNCHRONY BANK',           'Credit Card',   '2293', 'Derogatory','$2,800',  '$4,000',  '03/2018'),
                ('CAPITAL ONE BANK',         'Credit Card',   '0044', 'Open',      '$1,200',  '$5,000',  '01/2020'),
                ('MIDLAND CREDIT MGMT',      'Collection',    '7701', 'Open',      '$950',    '',        '11/2022'),
                ('JEFFERSON CAPITAL SYSTEMS','Collection',    '3312', 'Open',      '$680',    '',        '05/2023'),
            ],
            'experian': [
                ('CREDIT ONE BANK',          'Credit Card',   '5512', 'Open',      '$880',    '$3,500',  '04/2017'),
                ('GM FINANCIAL',             'Auto Loan',     '4401', 'Open',      '$18,400', '$32,000', '06/2021'),
                ('FIRST BANK',               'Mortgage',      '8830', 'Open',      '$278,000','$310,000','08/2019'),
                ('SYNCHRONY BANK',           'Credit Card',   '2293', 'Derogatory','$2,800',  '$4,000',  '03/2018'),
                ('CAPITAL ONE BANK',         'Credit Card',   '0044', 'Open',      '$1,200',  '$5,000',  '01/2020'),
                ('MIDLAND CREDIT MGMT',      'Collection',    '7701', 'Open',      '$950',    '',        '11/2022'),
                ('JEFFERSON CAPITAL SYSTEMS','Collection',    '3312', 'Open',      '$680',    '',        '05/2023'),
            ],
            'transunion': [
                ('CREDIT ONE BANK',          'Credit Card',   '5512', 'Open',      '$880',    '$3,500',  '04/2017'),
                ('GM FINANCIAL',             'Auto Loan',     '4401', 'Open',      '$18,400', '$32,000', '06/2021'),
                ('FIRST BANK',               'Mortgage',      '8830', 'Open',      '$278,000','$310,000','08/2019'),
                ('SYNCHRONY BANK',           'Credit Card',   '2293', 'Derogatory','$2,800',  '$4,000',  '03/2018'),
                ('CAPITAL ONE BANK',         'Credit Card',   '0044', 'Open',      '$1,200',  '$5,000',  '01/2020'),
                ('MIDLAND CREDIT MGMT',      'Collection',    '7701', 'Open',      '$950',    '',        '11/2022'),
                ('JEFFERSON CAPITAL SYSTEMS','Collection',    '3312', 'Open',      '$680',    '',        '05/2023'),
            ],
        },
        # CSV has full middle name â€” NAME MISMATCH intentional
        'csv_name':           'Marcus D. Williams',
        'csv_ssn':            '319-74-8890',
        'csv_dob':            '09/09/1986',
        'csv_gender':         'male',
        'csv_street':         '3300 Pecos St',
        'csv_city':           'Denver',
        'csv_state':          'CO',
        'csv_zip':            '80211',
        'csv_prior_addresses': '4815 W 38th Ave|Denver|CO|80212;1550 Larimer St Apt 312|Denver|CO|80202',
        'csv_accounts':       'CREDIT ONE BANK|Credit Card|5512|Open;GM FINANCIAL|Auto Loan|4401|Open;FIRST BANK|Mortgage|8830|Open;SYNCHRONY BANK|Credit Card|2293|Derogatory;CAPITAL ONE BANK|Credit Card|0044|Open;MIDLAND CREDIT MGMT|Collection|7701|Open;JEFFERSON CAPITAL SYSTEMS|Collection|3312|Open',
        'csv_name_variations': 'Marc Williams',
        'csv_phones':         '720-555-0167',
        'csv_emails':         'marcus.williams@email.com',
        'csv_notes':          'Williams â€” all fields match',
        'credit_scores':      {'equifax': 618, 'experian': 614, 'transunion': 611},
        'in_file_since':      '04/2017',
        'expected_fico_range': '580-669',
    },

    # â”€â”€ 8. Hartmann â€” DOB MISMATCH â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    {
        'ref_num':     'CR-008',
        'slug':        'hartmann',
        'report_name': 'EMILY ROSE HARTMANN',
        'report_ssn':  '642-16-3377',
        'report_dob':  '05/17/1990',   # all 3 bureaus say 1990
        'alternate_names': [],
        'addresses': [
            ('550 Park Ave Apt 12C', 'New York', 'NY', '10065'),
            ('211 E 70th St Apt 4A', 'New York', 'NY', '10021'),
            ('88 Morningside Dr',    'New York', 'NY', '10027'),
        ],
        'accounts_by_bureau': {
            'equifax': [
                ('CHASE BANK USA NA',    'Credit Card',  '1192', 'Open',   '$3,400',  '$15,000', '03/2016'),
                ('AMERICAN EXPRESS',     'Credit Card',  '8801', 'Open',   '$7,200',  '$25,000', '11/2013'),
                ('CITIBANK NA',          'Mortgage',     '4490', 'Open',   '$680,000','$780,000','06/2020'),
                ('SALLIE MAE',           'Student Loan', '7723', 'Open',   '$14,500', '$22,000', '08/2012'),
                ('MARCUS BY GOLDMAN',    'Personal Loan','3301', 'Closed', '$0',      '$8,000',  '10/2021'),
                ('DISCOVER BANK',        'Credit Card',  '6614', 'Open',   '$1,100',  '$7,500',  '09/2018'),
                ('WELLS FARGO BANK NA',  'Credit Card',  '0044', 'Open',   '$900',    '$5,000',  '07/2019'),
            ],
            'experian': [
                ('CHASE BANK USA NA',    'Credit Card',  '1192', 'Open',   '$3,400',  '$15,000', '03/2016'),
                ('AMERICAN EXPRESS',     'Credit Card',  '8801', 'Open',   '$7,200',  '$25,000', '11/2013'),
                ('CITIBANK NA',          'Mortgage',     '4490', 'Open',   '$680,000','$780,000','06/2020'),
                ('SALLIE MAE',           'Student Loan', '7723', 'Open',   '$14,500', '$22,000', '08/2012'),
                ('MARCUS BY GOLDMAN',    'Personal Loan','3301', 'Closed', '$0',      '$8,000',  '10/2021'),
                ('DISCOVER BANK',        'Credit Card',  '6614', 'Open',   '$1,100',  '$7,500',  '09/2018'),
                ('WELLS FARGO BANK NA',  'Credit Card',  '0044', 'Open',   '$900',    '$5,000',  '07/2019'),
            ],
            'transunion': [
                ('CHASE BANK USA NA',    'Credit Card',  '1192', 'Open',   '$3,400',  '$15,000', '03/2016'),
                ('AMERICAN EXPRESS',     'Credit Card',  '8801', 'Open',   '$7,200',  '$25,000', '11/2013'),
                ('CITIBANK NA',          'Mortgage',     '4490', 'Open',   '$680,000','$780,000','06/2020'),
                ('SALLIE MAE',           'Student Loan', '7723', 'Open',   '$14,500', '$22,000', '08/2012'),
                ('MARCUS BY GOLDMAN',    'Personal Loan','3301', 'Closed', '$0',      '$8,000',  '10/2021'),
                ('DISCOVER BANK',        'Credit Card',  '6614', 'Open',   '$1,100',  '$7,500',  '09/2018'),
                ('WELLS FARGO BANK NA',  'Credit Card',  '0044', 'Open',   '$900',    '$5,000',  '07/2019'),
            ],
        },
        # CSV says 1991 â€” DOB MISMATCH intentional
        'csv_name':           'Emily Rose Hartmann',
        'csv_ssn':            '642-16-3377',
        'csv_dob':            '05/17/1990',
        'csv_gender':         'female',
        'csv_street':         '550 Park Ave Apt 12C',
        'csv_city':           'New York',
        'csv_state':          'NY',
        'csv_zip':            '10065',
        'csv_prior_addresses': '211 E 70th St Apt 4A|New York|NY|10021;88 Morningside Dr|New York|NY|10027',
        'csv_accounts':       'CHASE BANK USA NA|Credit Card|1192|Open;AMERICAN EXPRESS|Credit Card|8801|Open;CITIBANK NA|Mortgage|4490|Open;SALLIE MAE|Student Loan|7723|Open;DISCOVER BANK|Credit Card|6614|Open;MARCUS BY GOLDMAN|Personal Loan|3301|Closed;WELLS FARGO BANK NA|Credit Card|0044|Open',
        'csv_name_variations': '',
        'csv_phones':         '212-555-0144',
        'csv_emails':         'emily.hartmann@nyc.rr.com',
        'csv_notes':          'Hartmann â€” all fields match',
        'credit_scores':      {'equifax': 751, 'experian': 746, 'transunion': 743},
        'in_file_since':      '08/2012',
        'expected_fico_range': '740-799',
    },

    # â”€â”€ 9. Reyes â€” ADDRESS MISMATCH â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    {
        'ref_num':     'CR-009',
        'slug':        'reyes',
        'report_name': 'CARLOS ALBERTO REYES',
        'report_ssn':  '487-63-1029',
        'report_dob':  '10/31/1979',
        'alternate_names': [],
        'addresses': [
            # Report has different address from CSV reference
            ('9200 NW 36th St Apt 4', 'Doral',  'FL', '33166'),
            ('6721 SW 8th St',        'Miami',  'FL', '33144'),
            ('1400 S Bayshore Dr',    'Miami',  'FL', '33131'),
        ],
        'accounts_by_bureau': {
            'equifax': [
                ('REGIONS BANK',           'Credit Card',   '6613', 'Open',      '$2,100',  '$9,000',  '08/2014'),
                ('NISSAN MOTOR ACCEPT',    'Auto Loan',     '3302', 'Open',      '$16,800', '$28,000', '03/2022'),
                ('TRUIST BANK',            'Mortgage',      '7740', 'Open',      '$198,000','$220,000','04/2017'),
                ('SYNCHRONY BANK',         'Credit Card',   '4421', 'Derogatory','$3,600',  '$5,000',  '01/2019'),
                ('PORTFOLIO RECOVERY',     'Collection',    '8812', 'Open',      '$1,400',  '',        '06/2023'),
                ('DISCOVER BANK',          'Credit Card',   '1193', 'Open',      '$580',    '$3,500',  '12/2020'),
                ('CAPITAL ONE BANK',       'Credit Card',   '9902', 'Closed',    '$0',      '$4,500',  '07/2016'),
                # NOT in csv_accounts â€” flags as unknown account
                ('BEALLS DEPARTMENT STORE','Credit Card',   '8801', 'Open',      '$180',    '$500',    '11/2021'),
            ],
            'experian': [
                ('REGIONS BANK',           'Credit Card',   '6613', 'Open',      '$2,100',  '$9,000',  '08/2014'),
                ('NISSAN MOTOR ACCEPT',    'Auto Loan',     '3302', 'Open',      '$16,800', '$28,000', '03/2022'),
                ('TRUIST BANK',            'Mortgage',      '7740', 'Open',      '$198,000','$220,000','04/2017'),
                ('SYNCHRONY BANK',         'Credit Card',   '4421', 'Derogatory','$3,600',  '$5,000',  '01/2019'),
                ('PORTFOLIO RECOVERY',     'Collection',    '8812', 'Open',      '$1,400',  '',        '06/2023'),
                ('DISCOVER BANK',          'Credit Card',   '1193', 'Open',      '$580',    '$3,500',  '12/2020'),
                ('CAPITAL ONE BANK',       'Credit Card',   '9902', 'Closed',    '$0',      '$4,500',  '07/2016'),
            ],
            'transunion': [
                ('REGIONS BANK',           'Credit Card',   '6613', 'Open',      '$2,100',  '$9,000',  '08/2014'),
                ('NISSAN MOTOR ACCEPT',    'Auto Loan',     '3302', 'Open',      '$16,800', '$28,000', '03/2022'),
                ('TRUIST BANK',            'Mortgage',      '7740', 'Open',      '$198,000','$220,000','04/2017'),
                ('SYNCHRONY BANK',         'Credit Card',   '4421', 'Derogatory','$3,600',  '$5,000',  '01/2019'),
                ('PORTFOLIO RECOVERY',     'Collection',    '8812', 'Open',      '$1,400',  '',        '06/2023'),
                ('DISCOVER BANK',          'Credit Card',   '1193', 'Open',      '$580',    '$3,500',  '12/2020'),
                ('CAPITAL ONE BANK',       'Credit Card',   '9902', 'Closed',    '$0',      '$4,500',  '07/2016'),
            ],
        },
        # CSV has Miami address â€” ADDRESS MISMATCH intentional
        # Prior = 1400 S Bayshore (in reference). 9200 NW 36th NOT in reference â†’ unknown/flagged.
        'csv_name':           'Carlos Alberto Reyes',
        'csv_ssn':            '487-63-1029',
        'csv_dob':            '10/31/1979',
        'csv_gender':         'male',
        'csv_street':         '6721 SW 8th St',
        'csv_city':           'Miami',
        'csv_state':          'FL',
        'csv_zip':            '33144',
        'csv_prior_addresses': '1400 S Bayshore Dr|Miami|FL|33131',
        'csv_accounts':       'REGIONS BANK|Credit Card|6613|Open;NISSAN MOTOR ACCEPT|Auto Loan|3302|Open;TRUIST BANK|Mortgage|7740|Open;SYNCHRONY BANK|Credit Card|4421|Derogatory;DISCOVER BANK|Credit Card|1193|Open;PORTFOLIO RECOVERY|Collection|8812|Open;CAPITAL ONE BANK|Credit Card|9902|Closed',
        'csv_name_variations': '',
        'csv_phones':         '305-555-0192',
        'csv_emails':         'carlosreyes79@gmail.com',
        'csv_notes':          'Reyes â€” address mismatch (report shows Doral address) + unknown address (9200 NW 36th St)',
        'credit_scores':      {'equifax': 637, 'experian': 633, 'transunion': 630},
        'in_file_since':      '08/2014',
        'expected_fico_range': '580-669',
    },

    # â”€â”€ 10. Jackson â€” 100% CLEAR â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    {
        'ref_num':     'CR-010',
        'slug':        'jackson',
        'report_name': 'AISHA MONIQUE JACKSON',
        'report_ssn':  '924-55-6612',
        'report_dob':  '01/08/2000',
        'alternate_names': [],
        'addresses': [
            ('1204 Elm Street NW',    'Washington', 'DC', '20001'),
            ('3300 16th St NW Apt 2', 'Washington', 'DC', '20010'),
            ('800 Columbia Rd NW',    'Washington', 'DC', '20009'),
        ],
        'accounts_by_bureau': {
            'equifax': [
                ('CAPITAL ONE BANK',    'Credit Card',  '3301', 'Open',   '$840',   '$4,000',  '06/2021'),
                ('SALLIE MAE',          'Student Loan', '7712', 'Open',   '$18,200','$28,000',  '08/2018'),
                ('HONDA FINANCIAL SVCS','Auto Loan',    '5544', 'Open',   '$9,600', '$19,000',  '11/2022'),
                ('DISCOVER BANK',       'Credit Card',  '8890', 'Open',   '$320',   '$2,000',   '03/2022'),
                ('NAVY FEDERAL CU',     'Credit Card',  '1123', 'Open',   '$650',   '$5,000',   '09/2021'),
            ],
            'experian': [
                ('CAPITAL ONE BANK',    'Credit Card',  '3301', 'Open',   '$840',   '$4,000',  '06/2021'),
                ('SALLIE MAE',          'Student Loan', '7712', 'Open',   '$18,200','$28,000',  '08/2018'),
                ('HONDA FINANCIAL SVCS','Auto Loan',    '5544', 'Open',   '$9,600', '$19,000',  '11/2022'),
                ('DISCOVER BANK',       'Credit Card',  '8890', 'Open',   '$320',   '$2,000',   '03/2022'),
                ('NAVY FEDERAL CU',     'Credit Card',  '1123', 'Open',   '$650',   '$5,000',   '09/2021'),
            ],
            'transunion': [
                ('CAPITAL ONE BANK',    'Credit Card',  '3301', 'Open',   '$840',   '$4,000',  '06/2021'),
                ('SALLIE MAE',          'Student Loan', '7712', 'Open',   '$18,200','$28,000',  '08/2018'),
                ('HONDA FINANCIAL SVCS','Auto Loan',    '5544', 'Open',   '$9,600', '$19,000',  '11/2022'),
                ('DISCOVER BANK',       'Credit Card',  '8890', 'Open',   '$320',   '$2,000',   '03/2022'),
                ('NAVY FEDERAL CU',     'Credit Card',  '1123', 'Open',   '$650',   '$5,000',   '09/2021'),
            ],
        },
        'csv_name':           'Aisha Monique Jackson',
        'csv_ssn':            '924-55-6612',
        'csv_dob':            '01/08/2000',
        'csv_gender':         'female',
        'csv_street':         '1204 Elm Street NW',
        'csv_city':           'Washington',
        'csv_state':          'DC',
        'csv_zip':            '20001',
        'csv_prior_addresses': '3300 16th St NW Apt 2|Washington|DC|20010;800 Columbia Rd NW|Washington|DC|20009',
        'csv_accounts':       'CAPITAL ONE BANK|Credit Card|3301|Open;SALLIE MAE|Student Loan|7712|Open;HONDA FINANCIAL SVCS|Auto Loan|5544|Open;DISCOVER BANK|Credit Card|8890|Open;NAVY FEDERAL CU|Credit Card|1123|Open',
        'csv_name_variations': '',
        'csv_phones':         '202-555-0155',
        'csv_emails':         'aisha.jackson@gmail.com',
        'csv_notes':          'Jackson â€” all fields match',
        'credit_scores':      {'equifax': 712, 'experian': 708, 'transunion': 705},
        'in_file_since':      '08/2018',
        'expected_fico_range': '670-739',
    },

    # â”€â”€ 11. Caldwell â€” NOT IN REFERENCE DATA (unmatched test) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    {
        'ref_num':     'CR-011',
        'slug':        'caldwell',
        'report_name': 'THOMAS E. CALDWELL',
        'report_ssn':  '711-33-5892',   # not in any reference identity
        'report_dob':  '04/15/1983',
        'alternate_names': [],
        'addresses': [
            ('455 Briar Patch Rd',      'Seattle', 'WA', '98101'),
            ('8800 Roosevelt Way NE',   'Seattle', 'WA', '98115'),
        ],
        'accounts_by_bureau': {
            'equifax': [
                ('WASHINGTON FEDERAL',    'Credit Card',  '8832', 'Open',   '$1,100', '$5,000', '03/2015'),
                ('SOFI BANK NA',          'Personal Loan','4410', 'Open',   '$14,200','$20,000','09/2022'),
                ('ALLY FINANCIAL',        'Auto Loan',    '7723', 'Open',   '$19,800','$32,000','11/2023'),
            ],
        },
        'unmatched_only': True,       # generates PDF only â€” no CSV row
        'bureaus_to_generate': ['equifax'],
        'credit_scores':      {'equifax': 698},
        'in_file_since':      '03/2015',
    },
]


# â”€â”€ Style helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def make_styles(theme):
    primary = theme['primary']
    return {
        'bureau_name': ParagraphStyle(
            'BureauName', fontName='Helvetica-Bold', fontSize=28,
            textColor=colors.white, leading=34,
        ),
        'report_subtitle': ParagraphStyle(
            'ReportSubtitle', fontName='Helvetica', fontSize=9,
            textColor=colors.white, leading=12, spaceBefore=2,
        ),
        'section_header': ParagraphStyle(
            'SectionHeader', fontName='Helvetica-Bold', fontSize=9,
            textColor=colors.white, backColor=primary, leading=14,
            spaceBefore=12, spaceAfter=4, leftIndent=-6, rightIndent=-6,
            borderPadding=(3, 6, 3, 6),
        ),
        'field_label': ParagraphStyle(
            'FieldLabel', fontName='Helvetica-Bold', fontSize=8,
            textColor=colors.HexColor('#666666'), leading=11, spaceAfter=1,
        ),
        'field_value': ParagraphStyle(
            'FieldValue', fontName='Helvetica', fontSize=10,
            textColor=colors.HexColor('#1a1a1a'), leading=13, spaceAfter=6,
        ),
        'disclaimer': ParagraphStyle(
            'Disclaimer', fontName='Helvetica', fontSize=7,
            textColor=colors.HexColor('#999999'), leading=10,
        ),
    }


def section_header(text, styles):
    return Paragraph(f'&nbsp;&nbsp;{text}', styles['section_header'])


def fmt_ssn(ssn, style):
    parts = ssn.split('-')
    if style == 'partial':
        return f'XXX-XX-{parts[2]}'
    elif style == 'masked':
        return f'###-##-{parts[2]}'
    return ssn  # full


# â”€â”€ PDF builder â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def build_report_pdf(person, bureau_key):
    theme = BUREAUS[bureau_key]
    filename = f'{theme["code"]}-{person["ref_num"]}.pdf'
    out_path = str(REPORTS_DIR / filename)
    styles = make_styles(theme)

    doc = SimpleDocTemplate(
        out_path, pagesize=letter,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0, bottomMargin=0.75 * inch,
    )
    story = []

    # â”€â”€ Header banner â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    header_data = [[
        Paragraph(theme['label'], styles['bureau_name']),
        Paragraph(theme['subtitle'], styles['report_subtitle']),
        Paragraph('Report Date: 05/01/2025', styles['report_subtitle']),
    ]]
    header_table = Table(header_data, colWidths=[2.5 * inch, 3 * inch, 1.5 * inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), theme['primary']),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 18),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 18),
        ('LEFTPADDING', (0, 0), (0, -1), 18),
        ('RIGHTPADDING', (-1, 0), (-1, -1), 12),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.2 * inch))

    # â”€â”€ Personal Information â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    story.append(section_header('PERSONAL INFORMATION', styles))
    story.append(Spacer(1, 4))

    score_type_label = 'FICO Score 8' if bureau_key != 'transunion' else 'VantageScore 3.0'
    score_value = person.get('credit_scores', {}).get(bureau_key, '')
    ssn_display = fmt_ssn(person['report_ssn'], theme['ssn_style'])
    pi_data = [
        ['Name:', person['report_name']],
        ['Social Security Number:', ssn_display],
        ['Date of Birth:', person['report_dob']],
    ]
    if person.get('in_file_since'):
        pi_data.append(['In File Since:', person['in_file_since']])
    if score_value:
        pi_data.append([f'{score_type_label}:', str(score_value)])
    if person['alternate_names']:
        pi_data.append(['Also Known As:', '\n'.join(person['alternate_names'])])

    pi_table = Table(pi_data, colWidths=[2.0 * inch, 5.0 * inch])
    pi_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#555555')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#111111')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#F7F7F7')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
    ]))
    story.append(pi_table)
    story.append(Spacer(1, 0.1 * inch))

    # â”€â”€ Address History â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    story.append(section_header('ADDRESS HISTORY', styles))
    story.append(Spacer(1, 4))

    for i, (street, city, state, zip_code) in enumerate(person['addresses']):
        addr_type = 'Current Address' if i == 0 else 'Previous Address'
        addr_table = Table(
            [[addr_type, f'{street}, {city}, {state} {zip_code}']],
            colWidths=[1.5 * inch, 5.5 * inch],
        )
        addr_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#555555')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#E8E8E8')),
        ]))
        story.append(addr_table)

    story.append(Spacer(1, 0.15 * inch))

    # â”€â”€ Account Summary â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    story.append(section_header('ACCOUNT SUMMARY', styles))
    story.append(Spacer(1, 4))

    accounts = person['accounts_by_bureau'][bureau_key]
    acct_headers = [['Creditor', 'Type', 'Account #', 'Status', 'Balance', 'Limit', 'High Bal', 'Mthly Pmt', 'Opened']]
    acct_data = acct_headers + [
        [a[0], a[1], _full_acct(a[2], a[0]), a[3], a[4], a[5],
         _high_bal(a[4], a[3]),
         (f'${_monthly(a[1], a[4], a[5])}' if _monthly(a[1], a[4], a[5]) else '—'),
         a[6]]
        for a in accounts
    ]

    status_colors = {
        'Open': colors.HexColor('#166534'),
        'Closed': colors.HexColor('#374151'),
        'Derogatory': colors.HexColor('#991B1B'),
        'Collection': colors.HexColor('#92400E'),
    }

    acct_table = Table(
        acct_data,
        colWidths=[1.75*inch, 0.75*inch, 1.0*inch, 0.65*inch, 0.5*inch, 0.5*inch, 0.55*inch, 0.6*inch, 0.5*inch],
    )
    acct_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), theme['secondary']),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('ALIGN', (4, 0), (7, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DDDDDD')),
    ])
    for i, row in enumerate(accounts, start=1):
        status = row[3]
        if status in status_colors:
            acct_style.add('TEXTCOLOR', (3, i), (3, i), status_colors[status])
            acct_style.add('FONTNAME', (3, i), (3, i), 'Helvetica-Bold')
    acct_table.setStyle(acct_style)
    story.append(acct_table)
    story.append(Spacer(1, 0.15 * inch))

    # ── Account Details ─────────────────────────────────────────────────────────────────
    story.append(section_header('ACCOUNT DETAILS', styles))
    story.append(Spacer(1, 4))

    current_addr = person['addresses'][0] if person['addresses'] else None
    addr_pipe = ''
    if current_addr:
        street, city, state, zip_code = current_addr
        addr_pipe = f'{street} | {city} | {state} | {zip_code}'

    detail_rows = []
    for a in accounts:
        creditor, acct_type, acct_num, status, balance, limit, opened = a
        monthly = _monthly(acct_type, balance, limit)
        parts = []
        if monthly:
            parts.append(f'Monthly Pmt: ${monthly}')
        if addr_pipe:
            parts.append(f'Addr: {addr_pipe}')
        full_num = _full_acct(acct_num, creditor)
        detail_rows.append([f'{creditor} ({full_num})', '  '.join(parts)])

    detail_table = Table(detail_rows, colWidths=[2.6*inch, 4.4*inch])
    detail_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 7.5),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#333333')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#555555')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E5E5')),
    ]))
    story.append(detail_table)
    story.append(Spacer(1, 0.2 * inch))

    # â”€â”€ Footer â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    story.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#CCCCCC')))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        f'This {theme["label"]} Credit Report is a SAMPLE document generated for development '
        'and testing purposes only. All personal information, SSNs, and financial data are '
        'entirely fictional. Any resemblance to real individuals is coincidental.',
        styles['disclaimer'],
    ))

    doc.build(story)
    print(f'  Created: {out_path}')
    return out_path


# â”€â”€ CSV writer â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def build_csv():
    out_path = OUT_DIR / 'sample_reference_data.csv'
    rows = []
    for p in PEOPLE:
        if p.get('unmatched_only'):
            continue

        # Build financial lookup from equifax (or first available bureau) keyed by last-4
        first_bureau = p.get('bureaus_to_generate', list(BUREAUS.keys()))[0]
        fin_lookup = {a[2]: a for a in p.get('accounts_by_bureau', {}).get(first_bureau, [])}

        # Enrich csv_accounts: creditor|type|acct_num|status|balance|limit|high_bal|monthly_pmt|date_opened
        enriched = []
        for entry in p.get('csv_accounts', '').split(';'):
            entry = entry.strip()
            if not entry:
                continue
            parts = [x.strip() for x in entry.split('|')]
            creditor = parts[0] if parts else ''
            acct_type = parts[1] if len(parts) > 1 else ''
            acct_num = parts[2] if len(parts) > 2 else ''
            acct_status = parts[3] if len(parts) > 3 else ''
            fin = fin_lookup.get(acct_num)
            if fin:
                balance, limit, date_opened = fin[4], fin[5], fin[6]
                high_bal = _high_bal(balance, acct_status)
                monthly = _monthly(acct_type, balance, limit)
                enriched.append(
                    f'{creditor}|{acct_type}|{_full_acct(acct_num, creditor)}|{acct_status}'
                    f'|{balance}|{limit}|{high_bal}|{monthly}|{date_opened}'
                )
            else:
                enriched.append(entry)

        rows.append({
            'full_name':            p['csv_name'],
            'ssn':                  p['csv_ssn'],
            'date_of_birth':        p['csv_dob'],
            'gender':               p['csv_gender'],
            'street':               p['csv_street'],
            'city':                 p['csv_city'],
            'state':                p['csv_state'],
            'zip_code':             p['csv_zip'],
            'prior_addresses':      p.get('csv_prior_addresses', ''),
            'accounts':             ';'.join(enriched),
            'name_variations':      p['csv_name_variations'],
            'phones':               p['csv_phones'],
            'notes':                p['csv_notes'],
            'expected_fico_range':  p.get('expected_fico_range', ''),
        })

    fieldnames = [
        'full_name', 'ssn', 'date_of_birth', 'gender',
        'street', 'city', 'state', 'zip_code', 'prior_addresses',
        'accounts', 'name_variations', 'phones', 'notes', 'expected_fico_range',
    ]
    with open(out_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f'  Created: {out_path}  ({len(rows)} rows)')


# â”€â”€ Main â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

if __name__ == '__main__':
    print('\nVeriscope â€” Fake Data Generator\n')

    print('Generating CSV reference data...')
    build_csv()

    matched_count = sum(1 for p in PEOPLE if not p.get('unmatched_only'))
    unmatched_count = len(PEOPLE) - matched_count
    total_pdfs = sum(len(p.get('bureaus_to_generate', list(BUREAUS.keys()))) for p in PEOPLE)
    print(f'\nGenerating credit report PDFs ({total_pdfs} total: {matched_count * 3} matched + {unmatched_count} unmatched)...')
    for person in PEOPLE:
        bureaus = person.get('bureaus_to_generate', list(BUREAUS.keys()))
        for bureau_key in bureaus:
            build_report_pdf(person, bureau_key)

    print(f'\nDone. Files are in: {OUT_DIR.resolve()}\n')
    print('Expected DD results after import + upload:')
    print('  Thornton    â€” CLEAR   (all fields match)')
    print('  Kowalski    â€” CLEAR   (all fields match)')
    print('  Okonkwo     â€” FLAGGED (DOB: 1991 app vs 1990 reports)')
    print('  Castellano  â€” FLAGGED (address: Sunset Blvd vs Vine St)')
    print('  Nguyen      â€” CLEAR   (all fields match)')
    print('  Subramaniam â€” CLEAR   (all fields match)')
    print('  Williams    â€” CLEAR   (all fields match)')
    print('  Hartmann    â€” CLEAR   (all fields match)')
    print('  Reyes       â€” FLAGGED (address: Miami vs Doral)')
    print('  Jackson     â€” CLEAR   (all fields match)')

