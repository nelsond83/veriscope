import re
import os
import tempfile
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import DocumentTemplate, TemplateField
from .serializers import DocumentTemplateSerializer, TemplateFieldSerializer


def _run_pattern(pattern, text, capture_group, case_insensitive):
    """Return list of match dicts or raise re.error."""
    flags = re.IGNORECASE if case_insensitive else 0
    matches = []
    for m in re.finditer(pattern, text, flags):
        grp = min(capture_group, m.lastindex or 0)
        try:
            val = m.group(grp)
        except (IndexError, error):
            val = m.group(0)
        if val is not None:
            start = m.start(grp) if grp else m.start()
            end = m.end(grp) if grp else m.end()
            matches.append({'value': val.strip(), 'start': start, 'end': end})
    return matches


class DocumentTemplateViewSet(viewsets.ModelViewSet):
    queryset = DocumentTemplate.objects.prefetch_related('fields').all()
    serializer_class = DocumentTemplateSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_parsers(self):
        if self.action in ('list', 'retrieve', 'create', 'update', 'partial_update', 'preview', 'apply'):
            from rest_framework.parsers import JSONParser
            return [JSONParser()]
        return super().get_parsers()

    @action(detail=False, methods=['post'], url_path='extract-text',
            parser_classes=[MultiPartParser, FormParser])
    def extract_text(self, request):
        """Upload a PDF and return its extracted text."""
        pdf_file = request.FILES.get('file')
        if not pdf_file:
            return Response({'detail': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        if not pdf_file.name.lower().endswith('.pdf'):
            return Response({'detail': 'File must be a PDF'}, status=status.HTTP_400_BAD_REQUEST)

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                for chunk in pdf_file.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name
            from reports.services import extract_text_from_pdf
            text, page_count = extract_text_from_pdf(tmp_path)
            return Response({'text': text, 'page_count': page_count})
        except Exception as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    @action(detail=False, methods=['post'], url_path='preview')
    def preview(self, request):
        """Test a single regex against provided text."""
        text = request.data.get('text', '')
        pattern = request.data.get('pattern', '')
        capture_group = int(request.data.get('capture_group', 1) or 1)
        case_insensitive = request.data.get('case_insensitive', True)

        if not pattern:
            return Response({'matches': [], 'error': 'No pattern provided'})

        flags = re.IGNORECASE if case_insensitive else 0
        try:
            matches = []
            for m in re.finditer(pattern, text, flags):
                grp = min(capture_group, m.lastindex or 0)
                try:
                    val = m.group(grp)
                except IndexError:
                    val = m.group(0)
                if val is not None:
                    start = m.start(grp) if grp else m.start()
                    end = m.end(grp) if grp else m.end()
                    matches.append({'value': val.strip(), 'start': start, 'end': end})
            return Response({'matches': matches})
        except re.error as exc:
            return Response(
                {'matches': [], 'error': str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=['post'], url_path='apply')
    def apply(self, request, pk=None):
        """Apply template fields to a report's raw text or provided text."""
        template = self.get_object()
        report_id = request.data.get('report_id')
        text = request.data.get('text', '')

        if report_id and not text:
            from reports.models import CreditReport
            try:
                report = CreditReport.objects.get(pk=report_id)
                text = report.raw_text or ''
            except CreditReport.DoesNotExist:
                return Response({'detail': 'Report not found'}, status=status.HTTP_404_NOT_FOUND)

        if not text:
            return Response({'detail': 'No text provided'}, status=status.HTTP_400_BAD_REQUEST)

        results = {}
        for tf in template.fields.order_by('order'):
            label = tf.custom_label if tf.field_name == 'custom' and tf.custom_label else tf.field_name
            flags = re.IGNORECASE if tf.case_insensitive else 0
            try:
                first_match = ''
                for m in re.finditer(tf.regex_pattern, text, flags):
                    grp = min(tf.capture_group, m.lastindex or 0)
                    try:
                        val = m.group(grp)
                    except IndexError:
                        val = m.group(0)
                    if val:
                        first_match = val.strip()
                        break
                results[label] = first_match
            except re.error:
                results[label] = ''

        return Response({'extracted': results, 'template': template.name})
