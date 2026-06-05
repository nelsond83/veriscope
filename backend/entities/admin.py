from django.contrib import admin
from .models import Subject, AlternateName, Address, FinancialAccount


class AlternateNameInline(admin.TabularInline):
    model = AlternateName
    extra = 0


class AddressInline(admin.TabularInline):
    model = Address
    extra = 0


class FinancialAccountInline(admin.TabularInline):
    model = FinancialAccount
    extra = 0
    fields = ['creditor_name', 'account_type', 'status', 'balance', 'date_opened']


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'ssn_last_four', 'date_of_birth', 'report']
    search_fields = ['full_name', 'ssn_last_four']
    readonly_fields = ['id', 'created_at']
    inlines = [AlternateNameInline, AddressInline, FinancialAccountInline]


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['street', 'city', 'state', 'zip_code', 'address_type', 'subject']
    list_filter = ['state', 'address_type']


@admin.register(FinancialAccount)
class FinancialAccountAdmin(admin.ModelAdmin):
    list_display = ['creditor_name', 'account_type', 'status', 'balance', 'subject']
    list_filter = ['account_type', 'status']
    search_fields = ['creditor_name']
