from django.contrib import admin
from .models import CreditReport


@admin.register(CreditReport)
class CreditReportAdmin(admin.ModelAdmin):
    list_display = ['original_filename', 'bureau', 'status', 'case', 'uploaded_at', 'parsed_at']
    list_filter = ['bureau', 'status']
    search_fields = ['original_filename']
    readonly_fields = ['id', 'uploaded_at', 'parsed_at', 'raw_text', 'page_count']
