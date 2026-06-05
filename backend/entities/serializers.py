from rest_framework import serializers
from .models import Subject, AlternateName, Address, FinancialAccount


class AlternateNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlternateName
        fields = ['id', 'name', 'name_type']


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'street', 'city', 'state', 'zip_code', 'address_type', 'reported_date']


class FinancialAccountSerializer(serializers.ModelSerializer):
    account_type_display = serializers.CharField(source='get_account_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = FinancialAccount
        fields = [
            'id', 'creditor_name', 'account_number', 'account_type', 'account_type_display',
            'status', 'status_display', 'balance', 'credit_limit', 'monthly_payment',
            'date_opened', 'date_closed', 'payment_status',
        ]


class SubjectSerializer(serializers.ModelSerializer):
    alternate_names = AlternateNameSerializer(many=True, read_only=True)
    addresses = AddressSerializer(many=True, read_only=True)
    financial_accounts = FinancialAccountSerializer(many=True, read_only=True)

    class Meta:
        model = Subject
        fields = [
            'id', 'report', 'full_name', 'ssn', 'ssn_last_four', 'date_of_birth',
            'alternate_names', 'addresses', 'financial_accounts', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']
