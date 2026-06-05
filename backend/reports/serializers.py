from rest_framework import serializers
from .models import CreditReport


class CreditReportSerializer(serializers.ModelSerializer):
    bureau_display = serializers.CharField(source='get_bureau_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    subject = serializers.SerializerMethodField()

    class Meta:
        model = CreditReport
        fields = [
            'id', 'file', 'original_filename', 'bureau', 'bureau_display',
            'status', 'status_display', 'case', 'page_count',
            'uploaded_at', 'parsed_at', 'error_message', 'subject',
        ]
        read_only_fields = [
            'id', 'bureau', 'status', 'page_count',
            'uploaded_at', 'parsed_at', 'error_message',
        ]

    def get_subject(self, obj):
        from entities.serializers import SubjectSerializer
        try:
            return SubjectSerializer(obj.subject).data
        except Exception:
            return None


class ReportUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    case = serializers.UUIDField(required=False, allow_null=True)
    auto_parse = serializers.BooleanField(default=True)
