import csv
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Identity, IdentityAddress, IdentityNameVariation, IdentityPhone, IdentityAccount, ComparisonResult
from .serializers import IdentitySerializer, IdentityDetailSerializer, ComparisonResultSerializer
from .services import run_comparison, auto_match_and_compare


class IdentityViewSet(viewsets.ModelViewSet):
    queryset = Identity.objects.prefetch_related(
        'reports', 'comparisons', 'addresses', 'name_variations', 'phones', 'ref_accounts'
    ).all()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return IdentityDetailSerializer
        return IdentitySerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['post'], url_path='import-csv',
            parser_classes=[MultiPartParser, FormParser])
    def import_csv(self, request):
        uploaded = request.FILES.get('file')
        if not uploaded:
            return Response({'detail': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)

        raw = uploaded.read()
        try:
            content = raw.decode('utf-8-sig')
        except UnicodeDecodeError:
            content = raw.decode('latin-1')

        reader = csv.DictReader(io.StringIO(content))
        created, skipped = [], 0

        for row in reader:
            name = row.get('full_name', row.get('name', '')).strip()
            if not name:
                skipped += 1
                continue

            ssn = row.get('ssn', '').strip()
            notes = row.get('notes', '').strip()
            dob = None
            dob_raw = row.get('date_of_birth', row.get('dob', '')).strip()
            if dob_raw:
                for fmt in ['%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y']:
                    try:
                        dob = datetime.strptime(dob_raw, fmt).date()
                        break
                    except ValueError:
                        continue

            gender = row.get('gender', '').strip().lower()
            if gender not in ('male', 'female', 'other', 'unknown'):
                gender = ''

            fico_range = row.get('expected_fico_range', '').strip()
            valid_fico = {'800-850', '740-799', '670-739', '580-669', '300-579'}
            if fico_range not in valid_fico:
                fico_range = ''

            identity = Identity.objects.create(
                full_name=name,
                ssn=ssn,
                date_of_birth=dob,
                gender=gender,
                notes=notes,
                expected_fico_range=fico_range,
                created_by=request.user,
            )

            street = row.get('street', '').strip()
            city = row.get('city', '').strip()
            state = row.get('state', '').strip()
            zip_code = row.get('zip_code', '').strip()
            if any([street, city, state, zip_code]):
                IdentityAddress.objects.create(
                    identity=identity, street=street, city=city,
                    state=state, zip_code=zip_code, address_type='current', order=0,
                )

            # Prior addresses: semicolon-separated entries, each "street|city|state|zip"
            prior_order = 1
            for entry in row.get('prior_addresses', '').split(';'):
                entry = entry.strip()
                if not entry:
                    continue
                parts = [p.strip() for p in entry.split('|')]
                if len(parts) == 4 and parts[0]:
                    IdentityAddress.objects.create(
                        identity=identity,
                        street=parts[0], city=parts[1], state=parts[2], zip_code=parts[3],
                        address_type='previous', order=prior_order,
                    )
                    prior_order += 1

            for raw in row.get('name_variations', '').split(';'):
                variation = raw.strip()
                if variation:
                    IdentityNameVariation.objects.create(identity=identity, name=variation)

            for i, raw in enumerate(row.get('phones', '').split(';')):
                number = raw.strip()
                if number:
                    IdentityPhone.objects.create(identity=identity, number=number, order=i)


            # Reference accounts: semicolon-separated
            # "creditor|type|acct_num|status|balance|credit_limit|high_bal|monthly_pmt|date_opened"
            for i, entry in enumerate(row.get('accounts', '').split(';')):
                entry = entry.strip()
                if not entry:
                    continue
                parts = [p.strip() for p in entry.split('|')]
                if len(parts) >= 1 and parts[0]:
                    def _dec(s):
                        if not s:
                            return None
                        try:
                            return Decimal(s.replace('$', '').replace(',', ''))
                        except InvalidOperation:
                            return None

                    def _dt(s):
                        if not s:
                            return None
                        try:
                            return datetime.strptime(s, '%m/%Y').date()
                        except ValueError:
                            try:
                                return datetime.strptime(s, '%m/%d/%Y').date()
                            except ValueError:
                                return None

                    IdentityAccount.objects.create(
                        identity=identity,
                        creditor_name=parts[0],
                        account_type=parts[1] if len(parts) > 1 else '',
                        account_number=parts[2] if len(parts) > 2 else '',
                        status=parts[3] if len(parts) > 3 else '',
                        balance=_dec(parts[4]) if len(parts) > 4 else None,
                        credit_limit=_dec(parts[5]) if len(parts) > 5 else None,
                        highest_balance=_dec(parts[6]) if len(parts) > 6 else None,
                        monthly_payment=_dec(parts[7]) if len(parts) > 7 else None,
                        date_opened=_dt(parts[8]) if len(parts) > 8 else None,
                        order=i,
                    )

            created.append(identity)

        return Response(
            {'created': len(created), 'skipped': skipped,
             'identities': IdentitySerializer(created, many=True).data},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'], url_path='run-comparison')
    def run_comparison_action(self, request, pk=None):
        identity = self.get_object()
        all_results = []
        for report in identity.reports.filter(status='parsed'):
            results = run_comparison(identity, report)
            all_results.extend(results)
        return Response(
            ComparisonResultSerializer(all_results, many=True).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'], url_path='assign-report')
    def assign_report(self, request, pk=None):
        identity = self.get_object()
        report_id = request.data.get('report_id')
        if not report_id:
            return Response({'detail': 'report_id required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            from reports.models import CreditReport
            report = CreditReport.objects.get(pk=report_id)
        except Exception:
            return Response({'detail': 'Report not found.'}, status=status.HTTP_404_NOT_FOUND)

        report.identity = identity
        report.match_confidence = 'manual'
        report.save(update_fields=['identity', 'match_confidence'])

        if report.status == 'parsed':
            run_comparison(identity, report)

        return Response({'detail': 'Report assigned.'})


    @action(detail=False, methods=['post'], url_path='reset-all')
    def reset_all(self, request):
        """Delete all identities, reports, and related data. Dev/testing only."""
        from reports.models import CreditReport
        import shutil, os
        from django.conf import settings

        # Delete uploaded files
        media_reports = os.path.join(settings.MEDIA_ROOT, 'reports')
        if os.path.isdir(media_reports):
            shutil.rmtree(media_reports)

        CreditReport.objects.all().delete()
        Identity.objects.all().delete()
        return Response({'detail': 'All records cleared.'})


class ComparisonResultViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ComparisonResult.objects.select_related('identity', 'report').all()
    serializer_class = ComparisonResultSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        identity_id = self.request.query_params.get('identity')
        report_id = self.request.query_params.get('report')
        if identity_id:
            qs = qs.filter(identity_id=identity_id)
        if report_id:
            qs = qs.filter(report_id=report_id)
        return qs
