from rest_framework import serializers
from .models import Case, ReferenceData, ComparisonResult


class ReferenceDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferenceData
        fields = [
            'id', 'case', 'source', 'label', 'full_name', 'ssn',
            'date_of_birth', 'raw_data', 'uploaded_at',
        ]
        read_only_fields = ['id', 'uploaded_at']


class ComparisonResultSerializer(serializers.ModelSerializer):
    match_status_display = serializers.CharField(source='get_match_status_display', read_only=True)

    class Meta:
        model = ComparisonResult
        fields = [
            'id', 'case', 'report', 'reference', 'field_name',
            'report_value', 'reference_value', 'match_status', 'match_status_display',
            'notes', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class CaseSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    report_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Case
        fields = [
            'id', 'name', 'description', 'status', 'status_display',
            'created_by', 'created_by_username', 'report_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_report_count(self, obj):
        return obj.reports.count()

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
