from django.contrib import admin
from .models import Identity, ComparisonResult

@admin.register(Identity)
class IdentityAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'ssn', 'date_of_birth', 'dd_status', 'created_at']
    search_fields = ['full_name', 'ssn']

@admin.register(ComparisonResult)
class ComparisonResultAdmin(admin.ModelAdmin):
    list_display = ['identity', 'report', 'field_name', 'match_status']
    list_filter = ['match_status', 'field_name']
