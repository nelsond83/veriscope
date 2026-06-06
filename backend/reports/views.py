import os
import tempfile
from pathlib import Path

from django.core.files import File
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import CreditReport, MonitoringBatch
from .serializers import CreditReportSerializer, ReportUploadSerializer
from .services import parse_report, handle_zip_upload


class CreditReportViewSet(viewsets.ModelViewSet):
    queryset = CreditReport.objects.select_related('identity').all()
    serializer_class = CreditReportSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        qs = super().get_queryset()
        identity_id = self.request.query_params.get('identity')
        unmatched = self.request.query_params.get('unmatched')
        if identity_id:
            qs = qs.filter(identity_id=identity_id)
        if unmatched == '1':
            qs = qs.filter(identity__isnull=True)
        return qs

    @action(detail=False, methods=['post'], url_path='upload')
    def upload(self, request):
        serializer = ReportUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data['file']
        auto_parse = serializer.validated_data.get('auto_parse', True)
        filename = uploaded_file.name.lower()
        created_reports = []

        if filename.endswith('.zip'):
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
                for chunk in uploaded_file.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name
            try:
                created_reports = handle_zip_upload(tmp_path)
            finally:
                os.unlink(tmp_path)
        elif filename.endswith('.pdf'):
            report = CreditReport(original_filename=uploaded_file.name)
            report.file.save(uploaded_file.name, uploaded_file, save=True)
            created_reports = [report]
        else:
            return Response(
                {'detail': 'Unsupported file type. Upload a PDF or ZIP of PDFs.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Assign all reports in this upload to today's monitoring batch
        from datetime import date
        batch, _ = MonitoringBatch.objects.get_or_create(
            run_date=date.today(),
            created_by=request.user if request.user.is_authenticated else None,
        )
        for report in created_reports:
            report.batch = batch
            report.save(update_fields=['batch'])

        if auto_parse:
            from identities.services import auto_match_and_compare
            for report in created_reports:
                try:
                    extracted = parse_report(report)
                    _save_extracted_data(report, extracted)
                    auto_match_and_compare(report)
                except Exception:
                    pass

        out = CreditReportSerializer(created_reports, many=True, context={'request': request})
        return Response(out.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='parse')
    def parse(self, request, pk=None):
        report = self.get_object()
        if report.status == 'parsing':
            return Response({'detail': 'Already parsing.'}, status=status.HTTP_409_CONFLICT)
        try:
            from identities.services import auto_match_and_compare
            extracted = parse_report(report)
            _save_extracted_data(report, extracted)
            auto_match_and_compare(report)
        except Exception as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(self.get_serializer(report).data)


def _save_extracted_data(report: CreditReport, extracted: dict):
    from entities.models import Subject, AlternateName, Address, FinancialAccount

    subject, _ = Subject.objects.get_or_create(report=report)
    subject.full_name = extracted.get('full_name', '')
    subject.ssn = extracted.get('ssn', '')
    subject.ssn_last_four = extracted.get('ssn_last_four', '')
    subject.date_of_birth = extracted.get('date_of_birth')
    subject.save()

    AlternateName.objects.filter(subject=subject).delete()
    for name in extracted.get('alternate_names', []):
        AlternateName.objects.create(subject=subject, name=name)

    Address.objects.filter(subject=subject).delete()
    for addr in extracted.get('addresses', []):
        Address.objects.create(
            subject=subject,
            street=addr.get('street', ''),
            city=addr.get('city', ''),
            state=addr.get('state', ''),
            zip_code=addr.get('zip_code', ''),
        )

    FinancialAccount.objects.filter(subject=subject).delete()
    for acct in extracted.get('accounts', []):
        balance = None
        raw_balance = acct.get('balance_raw', '').replace(',', '')
        if raw_balance:
            try:
                balance = float(raw_balance)
            except ValueError:
                pass
        FinancialAccount.objects.create(
            subject=subject,
            creditor_name=acct.get('creditor_name', ''),
            account_number=acct.get('account_number', ''),
            balance=balance,
        )
