import csv
import io

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import Case, ReferenceData, ComparisonResult
from .serializers import CaseSerializer, ReferenceDataSerializer, ComparisonResultSerializer


class CaseViewSet(viewsets.ModelViewSet):
    queryset = Case.objects.select_related('created_by').all()
    serializer_class = CaseSerializer

    @action(detail=True, methods=['post'], url_path='import-reference',
            parser_classes=[MultiPartParser, FormParser])
    def import_reference(self, request, pk=None):
        case = self.get_object()
        uploaded = request.FILES.get('file')
        if not uploaded:
            return Response({'detail': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)

        label = request.data.get('label', uploaded.name)
        raw = uploaded.read()
        try:
            content = raw.decode('utf-8-sig')
        except UnicodeDecodeError:
            content = raw.decode('latin-1')
        reader = csv.DictReader(io.StringIO(content))
        created = []

        for row in reader:
            ref = ReferenceData.objects.create(
                case=case,
                source='csv',
                label=label,
                full_name=row.get('full_name', row.get('name', '')),
                ssn=row.get('ssn', ''),
                raw_data=row,
            )
            dob_raw = row.get('date_of_birth', row.get('dob', ''))
            if dob_raw:
                from datetime import datetime
                for fmt in ['%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y']:
                    try:
                        ref.date_of_birth = datetime.strptime(dob_raw, fmt).date()
                        ref.save(update_fields=['date_of_birth'])
                        break
                    except ValueError:
                        continue
            created.append(ref)

        return Response(
            ReferenceDataSerializer(created, many=True).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'], url_path='compare')
    def compare(self, request, pk=None):
        case = self.get_object()
        report_id = request.data.get('report_id')
        reference_id = request.data.get('reference_id')

        try:
            from reports.models import CreditReport
            report = CreditReport.objects.get(pk=report_id, case=case)
            reference = ReferenceData.objects.get(pk=reference_id, case=case)
        except Exception:
            return Response({'detail': 'Report or reference not found.'}, status=status.HTTP_404_NOT_FOUND)

        subject = getattr(report, 'subject', None)
        if not subject:
            return Response({'detail': 'Report has not been parsed yet.'}, status=status.HTTP_400_BAD_REQUEST)

        ComparisonResult.objects.filter(case=case, report=report, reference=reference).delete()
        results = _run_comparison(case, report, subject, reference)

        return Response(
            ComparisonResultSerializer(results, many=True).data,
            status=status.HTTP_201_CREATED,
        )


class ReferenceDataViewSet(viewsets.ModelViewSet):
    queryset = ReferenceData.objects.select_related('case').all()
    serializer_class = ReferenceDataSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        case_id = self.request.query_params.get('case')
        if case_id:
            qs = qs.filter(case_id=case_id)
        return qs


class ComparisonResultViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ComparisonResult.objects.select_related('case', 'report', 'reference').all()
    serializer_class = ComparisonResultSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        case_id = self.request.query_params.get('case')
        report_id = self.request.query_params.get('report')
        if case_id:
            qs = qs.filter(case_id=case_id)
        if report_id:
            qs = qs.filter(report_id=report_id)
        return qs


# ── Comparison logic ─────────────────────────────────────────────────────────

def _normalize(value: str) -> str:
    return ' '.join(str(value or '').upper().split())


def _compare_field(case, report, reference, field_name, report_val, ref_val):
    a, b = _normalize(report_val), _normalize(ref_val)
    if not a and not b:
        return None
    if not a or not b:
        match_status = 'missing'
    elif a == b:
        match_status = 'match'
    elif a in b or b in a:
        match_status = 'partial'
    else:
        match_status = 'mismatch'

    return ComparisonResult(
        case=case,
        report=report,
        reference=reference,
        field_name=field_name,
        report_value=report_val or '',
        reference_value=ref_val or '',
        match_status=match_status,
    )


def _run_comparison(case, report, subject, reference):
    comparisons = []
    fields = [
        ('full_name', subject.full_name, reference.full_name),
        ('ssn', subject.ssn, reference.ssn),
        ('date_of_birth',
         str(subject.date_of_birth) if subject.date_of_birth else '',
         str(reference.date_of_birth) if reference.date_of_birth else ''),
    ]
    for field_name, report_val, ref_val in fields:
        result = _compare_field(case, report, reference, field_name, report_val, ref_val)
        if result:
            comparisons.append(result)

    ComparisonResult.objects.bulk_create(comparisons)
    return comparisons
