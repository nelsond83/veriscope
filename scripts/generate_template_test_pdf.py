#!/usr/bin/env python3
"""
generate_template_test_pdf.py

Generates a single fake bank statement PDF for testing the Veriscope
Document Template builder. Run from e:\veriscope\scripts\ with the backend venv.
"""

from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

OUT_DIR = Path(__file__).parent / 'output'
OUT_DIR.mkdir(exist_ok=True)
OUT_PATH = str(OUT_DIR / 'SAMPLE_BANK_STATEMENT.pdf')

# ── Styles ────────────────────────────────────────────────────────────────────

NAVY  = colors.HexColor('#0A2463')
LTGRY = colors.HexColor('#F5F7FA')
MDGRY = colors.HexColor('#E2E8F0')
DKGRY = colors.HexColor('#4A5568')
RED   = colors.HexColor('#C53030')
GRN   = colors.HexColor('#276749')

def s(name, **kw):
    return ParagraphStyle(name, **kw)

STYLES = {
    'bank_name': s('BankName', fontName='Helvetica-Bold', fontSize=22,
                   textColor=colors.white, leading=26),
    'bank_sub':  s('BankSub',  fontName='Helvetica', fontSize=9,
                   textColor=colors.HexColor('#BFD3F5'), leading=12),
    'section':   s('Section',  fontName='Helvetica-Bold', fontSize=9,
                   textColor=colors.white, backColor=NAVY, leading=14,
                   spaceBefore=10, spaceAfter=4,
                   borderPadding=(3, 6, 3, 6), leftIndent=-6, rightIndent=-6),
    'label':     s('Label',    fontName='Helvetica-Bold', fontSize=8,
                   textColor=DKGRY, leading=11),
    'value':     s('Value',    fontName='Helvetica', fontSize=10,
                   textColor=colors.HexColor('#1A202C'), leading=13),
    'note':      s('Note',     fontName='Helvetica', fontSize=7.5,
                   textColor=DKGRY, leading=10),
    'disclaimer':s('Disc',     fontName='Helvetica', fontSize=7,
                   textColor=colors.HexColor('#999999'), leading=10),
}

def sec(text):
    return Paragraph(f'&nbsp;&nbsp;{text}', STYLES['section'])

def kv(label, value):
    return [[Paragraph(label, STYLES['label']),
             Paragraph(value, STYLES['value'])]]

# ── Data ──────────────────────────────────────────────────────────────────────

CUSTOMER = {
    'name':    'Jonathan R. Preston',
    'address': '2847 Westover Hills Blvd',
    'city':    'Richmond',
    'state':   'VA',
    'zip':     '23225',
    'ssn':     'XXX-XX-7291',
    'dob':     '08/14/1977',
    'phone':   '804-555-0173',
    'email':   'j.preston@email.com',
    'employer':'Cascade Systems Group',
}

ACCOUNTS = [
    {
        'type':    'Checking Account',
        'number':  '4073829104651847',
        'opened':  '03/12/2009',
        'routing': '051000017',
        'balance': '$4,218.63',
        'status':  'Active',
    },
    {
        'type':    'Savings Account',
        'number':  '4073829104659202',
        'opened':  '03/12/2009',
        'routing': '051000017',
        'balance': '$18,445.00',
        'status':  'Active',
    },
    {
        'type':    'Home Equity Line of Credit',
        'number':  '8821047392015566',
        'opened':  '11/05/2018',
        'routing': '',
        'balance': '$42,000.00',
        'status':  'Active',
        'limit':   '$75,000.00',
        'rate':    '7.25%',
    },
]

TRANSACTIONS = [
    ('05/01/2025', 'Opening Balance',                    '',         '$4,010.44'),
    ('05/02/2025', 'Direct Deposit — Cascade Systems',   '$5,820.00',''),
    ('05/03/2025', 'Online Bill Pay — Dominion Energy',  '',         '$142.37'),
    ('05/05/2025', 'POS Purchase — Whole Foods Market',  '',         '$63.14'),
    ('05/07/2025', 'ATM Withdrawal — Main St Branch',    '',         '$200.00'),
    ('05/08/2025', 'Transfer to Savings',                '',         '$500.00'),
    ('05/10/2025', 'Check #1042 — PMC Property Mgmt',    '',         '$1,850.00'),
    ('05/12/2025', 'POS Purchase — Shell Gas Station',   '',         '$54.20'),
    ('05/14/2025', 'Venmo Transfer from M. Thornton',    '$250.00',  ''),
    ('05/16/2025', 'Online Bill Pay — Verizon Wireless', '',         '$89.99'),
    ('05/18/2025', 'POS Purchase — Harris Teeter',       '',         '$78.43'),
    ('05/20/2025', 'Direct Deposit — Cascade Systems',   '$5,820.00',''),
    ('05/22/2025', 'POS Purchase — Amazon.com',          '',         '$134.00'),
    ('05/25/2025', 'ATM Withdrawal — Airport Branch',    '',         '$300.00'),
    ('05/28/2025', 'Interest Credit',                    '$1.32',    ''),
    ('05/31/2025', 'Closing Balance',                    '',         '$4,218.63'),
]


def build():
    doc = SimpleDocTemplate(
        OUT_PATH, pagesize=letter,
        leftMargin=0.75*inch, rightMargin=0.75*inch,
        topMargin=0, bottomMargin=0.75*inch,
    )
    story = []

    # Header
    hdr = Table([[
        Paragraph('First National Bank', STYLES['bank_name']),
        Paragraph('Account Statement\nPeriod: May 1 – May 31, 2025', STYLES['bank_sub']),
        Paragraph('Statement Date: 06/01/2025', STYLES['bank_sub']),
    ]], colWidths=[2.6*inch, 2.8*inch, 1.6*inch])
    hdr.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,-1), NAVY),
        ('VALIGN', (0,0),(-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0),(-1,-1), 18),
        ('BOTTOMPADDING', (0,0),(-1,-1), 18),
        ('LEFTPADDING', (0,0),(0,-1), 18),
        ('RIGHTPADDING', (-1,0),(-1,-1), 12),
    ]))
    story += [hdr, Spacer(1, 0.2*inch)]

    # Customer Information
    story.append(sec('CUSTOMER INFORMATION'))
    story.append(Spacer(1, 4))
    ci_data = [
        ['Customer Name:',   CUSTOMER['name']],
        ['Address:',         CUSTOMER['address']],
        ['City / State / ZIP:', f"{CUSTOMER['city']}, {CUSTOMER['state']} {CUSTOMER['zip']}"],
        ['SSN:',             CUSTOMER['ssn']],
        ['Date of Birth:',   CUSTOMER['dob']],
        ['Phone:',           CUSTOMER['phone']],
        ['Email:',           CUSTOMER['email']],
        ['Employer:',        CUSTOMER['employer']],
    ]
    ci_table = Table(ci_data, colWidths=[2.0*inch, 5.0*inch])
    ci_table.setStyle(TableStyle([
        ('FONTNAME', (0,0),(0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (1,0),(1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0),(-1,-1), 9),
        ('TEXTCOLOR', (0,0),(0,-1), DKGRY),
        ('TOPPADDING', (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('ROWBACKGROUNDS', (0,0),(-1,-1), [colors.white, LTGRY]),
        ('GRID', (0,0),(-1,-1), 0.5, MDGRY),
    ]))
    story += [ci_table, Spacer(1, 0.15*inch)]

    # Accounts Summary
    story.append(sec('ACCOUNTS ON FILE'))
    story.append(Spacer(1, 4))
    for acct in ACCOUNTS:
        acct_rows = [
            ['Account Type:',   acct['type']],
            ['Account Number:', acct['number']],
            ['Date Opened:',    acct['opened']],
            ['Current Balance:',acct['balance']],
            ['Status:',         acct['status']],
        ]
        if acct.get('routing'):
            acct_rows.append(['Routing Number:', acct['routing']])
        if acct.get('limit'):
            acct_rows.append(['Credit Limit:', acct['limit']])
        if acct.get('rate'):
            acct_rows.append(['Interest Rate:', acct['rate']])
        t = Table(acct_rows, colWidths=[2.0*inch, 5.0*inch])
        t.setStyle(TableStyle([
            ('FONTNAME', (0,0),(0,-1), 'Helvetica-Bold'),
            ('FONTNAME', (1,0),(1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0),(-1,-1), 9),
            ('TEXTCOLOR', (0,0),(0,-1), DKGRY),
            ('TOPPADDING', (0,0),(-1,-1), 4),
            ('BOTTOMPADDING', (0,0),(-1,-1), 4),
            ('ROWBACKGROUNDS', (0,0),(-1,-1), [colors.white, LTGRY]),
            ('GRID', (0,0),(-1,-1), 0.5, MDGRY),
            ('LINEABOVE', (0,0),(-1,0), 1.5, NAVY),
        ]))
        story += [t, Spacer(1, 0.1*inch)]

    # Transactions
    story.append(sec('TRANSACTION HISTORY — Checking Account (…1847)'))
    story.append(Spacer(1, 4))
    tx_hdr = [['Date', 'Description', 'Credit (+)', 'Debit (–)']]
    tx_data = tx_hdr + list(TRANSACTIONS)
    tx_table = Table(tx_data, colWidths=[1.0*inch, 4.0*inch, 1.2*inch, 1.2*inch])
    tx_style = TableStyle([
        ('BACKGROUND', (0,0),(-1,0), colors.HexColor('#1A365D')),
        ('TEXTCOLOR', (0,0),(-1,0), colors.white),
        ('FONTNAME', (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,1),(-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0),(-1,-1), 8.5),
        ('ALIGN', (2,0),(3,-1), 'RIGHT'),
        ('TOPPADDING', (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('LEFTPADDING', (0,0),(-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1),(-1,-1), [colors.white, LTGRY]),
        ('GRID', (0,0),(-1,-1), 0.5, MDGRY),
    ])
    # Color credit entries green, debit entries red
    for i, tx in enumerate(TRANSACTIONS, start=1):
        if tx[2]:
            tx_style.add('TEXTCOLOR', (2,i),(2,i), GRN)
            tx_style.add('FONTNAME',  (2,i),(2,i), 'Helvetica-Bold')
        if tx[3] and i not in (0, len(TRANSACTIONS)):
            tx_style.add('TEXTCOLOR', (3,i),(3,i), RED)
    tx_table.setStyle(tx_style)
    story += [tx_table, Spacer(1, 0.2*inch)]

    # Footer
    story.append(HRFlowable(width='100%', thickness=0.5, color=MDGRY))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        'First National Bank — SAMPLE document generated for development and testing purposes only. '
        'All personal information, account numbers, and financial data are entirely fictional. '
        'Any resemblance to real individuals or accounts is coincidental.',
        STYLES['disclaimer'],
    ))

    doc.build(story)
    print(f'Created: {OUT_PATH}')


if __name__ == '__main__':
    build()
