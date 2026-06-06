#!/usr/bin/env python3
"""
clear_data.py

Truncates all application data so you can start fresh without
dropping the schema or losing the superuser account.

Run from e:\\veriscope\\scripts\\ with the backend venv active:
  python clear_data.py
"""

import os
import sys
import shutil
from pathlib import Path

# Bootstrap Django
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.contrib.auth.models import User
from identities.models import Identity, ComparisonResult
from reports.models import CreditReport
from entities.models import Subject, AlternateName, Address, FinancialAccount
from django.conf import settings


def confirm(prompt):
    answer = input(f'{prompt} [y/N] ').strip().lower()
    return answer == 'y'


def clear_media():
    reports_dir = Path(settings.MEDIA_ROOT) / 'reports'
    if reports_dir.exists():
        shutil.rmtree(reports_dir)
        reports_dir.mkdir(parents=True, exist_ok=True)
        print('  Cleared media/reports/')
    else:
        print('  media/reports/ not found, skipping')


def clear_tables():
    counts = {
        'ComparisonResult': ComparisonResult.objects.count(),
        'Subject/Entities':  Subject.objects.count(),
        'CreditReport':      CreditReport.objects.count(),
        'Identity':          Identity.objects.count(),
    }

    print('\nCurrent row counts:')
    for name, n in counts.items():
        print(f'  {name:20s} {n}')

    total = sum(counts.values())
    if total == 0:
        print('\nTables are already empty.')
        return

    print()
    if not confirm('Delete all application data? (superuser kept)'):
        print('Aborted.')
        sys.exit(0)

    # Delete in dependency order
    ComparisonResult.objects.all().delete()
    AlternateName.objects.all().delete()
    Address.objects.all().delete()
    FinancialAccount.objects.all().delete()
    Subject.objects.all().delete()
    CreditReport.objects.all().delete()
    Identity.objects.all().delete()

    print('\nTables cleared.')

    if confirm('Also delete uploaded PDF files from media/?'):
        clear_media()

    users = User.objects.filter(is_superuser=False).count()
    print(f'\nDone. Superuser(s) kept: {User.objects.filter(is_superuser=True).count()}')
    if users:
        print(f'Non-superuser accounts kept: {users}')


if __name__ == '__main__':
    print('\nVeriscope — Clear Data\n')
    clear_tables()
    print()
