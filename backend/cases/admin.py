from django.contrib import admin
from .models import Case, ReferenceData, ComparisonResult


class ReferenceDataInline(admin.TabularInline):
    model = ReferenceData
    extra = 0
    fields = ['label', 'source', 'full_name', 'ssn', 'date_of_birth']


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'created_by', 'created_at', 'updated_at']
    list_filter = ['status']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [ReferenceDataInline]


@admin.register(ReferenceData)
class ReferenceDataAdmin(admin.ModelAdmin):
    list_display = ['label', 'source', 'full_name', 'case', 'uploaded_at']
    list_filter = ['source']
    search_fields = ['full_name', 'label']
    readonly_fields = ['id', 'uploaded_at']


@admin.register(ComparisonResult)
class ComparisonResultAdmin(admin.ModelAdmin):
    list_display = ['field_name', 'match_status', 'report_value', 'reference_value', 'case']
    list_filter = ['match_status', 'field_name']
