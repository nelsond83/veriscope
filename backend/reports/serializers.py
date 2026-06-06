from rest_framework import serializers
from .models import CreditReport, MonitoringBatch


class MonitoringBatchSerializer(serializers.ModelSerializer):
    report_count = serializers.SerializerMethodField()

    class Meta:
        model = MonitoringBatch
        fields = ['id', 'label', 'run_date', 'created_at', 'report_count']
        read_only_fields = ['id', 'created_at']

    def get_report_count(self, obj):
        return obj.reports.count()


class CreditReportSerializer(serializers.ModelSerializer):
    bureau_display = serializers.CharField(source='get_bureau_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    match_confidence_display = serializers.CharField(source='get_match_confidence_display', read_only=True)
    batch_id = serializers.UUIDField(source='batch.id', read_only=True, allow_null=True)
    batch_run_date = serializers.DateField(source='batch.run_date', read_only=True, allow_null=True)
    subject = serializers.SerializerMethodField()

    class Meta:
        model = CreditReport
        fields = [
            'id', 'file', 'original_filename', 'bureau', 'bureau_display',
            'status', 'status_display', 'identity', 'match_confidence',
            'match_confidence_display', 'batch_id', 'batch_run_date', 'page_count',
            'uploaded_at', 'parsed_at', 'error_message', 'raw_text', 'subject',
        ]
        read_only_fields = [
            'id', 'bureau', 'status', 'page_count',
            'uploaded_at', 'parsed_at', 'error_message', 'match_confidence',
        ]

    def get_subject(self, obj):
        from entities.serializers import SubjectSerializer
        try:
            return SubjectSerializer(obj.subject).data
        except Exception:
            return None


class ReportUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    auto_parse = serializers.BooleanField(default=True)
