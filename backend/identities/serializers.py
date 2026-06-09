import csv
import io
from datetime import datetime
from rest_framework import serializers
from .models import Identity, IdentityAddress, IdentityNameVariation, IdentityPhone, IdentityAccount, ComparisonResult


class ComparisonResultSerializer(serializers.ModelSerializer):
    match_status_display = serializers.CharField(source='get_match_status_display', read_only=True)

    class Meta:
        model = ComparisonResult
        fields = [
            'id', 'identity', 'report', 'field_name',
            'identity_value', 'report_value',
            'match_status', 'match_status_display', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class IdentityAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdentityAddress
        fields = ['id', 'street', 'city', 'state', 'zip_code', 'address_type', 'order']
        read_only_fields = ['id']


class IdentityNameVariationSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdentityNameVariation
        fields = ['id', 'name', 'note']
        read_only_fields = ['id']


class IdentityPhoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdentityPhone
        fields = ['id', 'number', 'phone_type', 'order']
        read_only_fields = ['id']



class IdentityAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdentityAccount
        fields = [
            'id', 'creditor_name', 'account_type', 'account_number', 'status',
            'balance', 'credit_limit', 'highest_balance', 'monthly_payment',
            'date_opened', 'account_address', 'order',
        ]
        read_only_fields = ['id']


class IdentitySerializer(serializers.ModelSerializer):
    dd_status = serializers.ReadOnlyField()
    report_count = serializers.SerializerMethodField()
    reports_by_bureau = serializers.SerializerMethodField()
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    addresses = IdentityAddressSerializer(many=True, required=False)
    name_variations = IdentityNameVariationSerializer(many=True, required=False)
    phones = IdentityPhoneSerializer(many=True, required=False)
    ref_accounts = IdentityAccountSerializer(many=True, required=False)

    class Meta:
        model = Identity
        fields = [
            'id', 'full_name', 'ssn', 'date_of_birth', 'gender',
            'addresses', 'name_variations', 'phones', 'ref_accounts',
            'notes', 'expected_fico_range',
            'dd_status', 'report_count', 'reports_by_bureau',
            'created_by_username', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_report_count(self, obj):
        return obj.reports.count()

    def get_reports_by_bureau(self, obj):
        return {r.bureau: {'id': str(r.id), 'status': r.status} for r in obj.reports.all()}

    def _save_related(self, identity, addresses_data, name_variations_data, phones_data, ref_accounts_data):
        if addresses_data is not None:
            identity.addresses.all().delete()
            for i, item in enumerate(addresses_data):
                item.pop('id', None)
                item.pop('order', None)
                IdentityAddress.objects.create(identity=identity, order=i, **item)
        if name_variations_data is not None:
            identity.name_variations.all().delete()
            for item in name_variations_data:
                item.pop('id', None)
                IdentityNameVariation.objects.create(identity=identity, **item)
        if phones_data is not None:
            identity.phones.all().delete()
            for i, item in enumerate(phones_data):
                item.pop('id', None)
                item.pop('order', None)
                IdentityPhone.objects.create(identity=identity, order=i, **item)
        if ref_accounts_data is not None:
            identity.ref_accounts.all().delete()
            for i, item in enumerate(ref_accounts_data):
                item.pop('id', None)
                item.pop('order', None)
                IdentityAccount.objects.create(identity=identity, order=i, **item)

    def create(self, validated_data):
        addresses_data = validated_data.pop('addresses', [])
        name_variations_data = validated_data.pop('name_variations', [])
        phones_data = validated_data.pop('phones', [])
        ref_accounts_data = validated_data.pop('ref_accounts', [])
        identity = Identity.objects.create(**validated_data)
        self._save_related(identity, addresses_data, name_variations_data, phones_data, ref_accounts_data)
        return identity

    def update(self, instance, validated_data):
        addresses_data = validated_data.pop('addresses', None)
        name_variations_data = validated_data.pop('name_variations', None)
        phones_data = validated_data.pop('phones', None)
        ref_accounts_data = validated_data.pop('ref_accounts', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        self._save_related(instance, addresses_data, name_variations_data, phones_data, ref_accounts_data)
        return instance


class IdentityDetailSerializer(IdentitySerializer):
    from reports.serializers import CreditReportSerializer
    reports = serializers.SerializerMethodField()
    comparisons = ComparisonResultSerializer(many=True, read_only=True)

    class Meta(IdentitySerializer.Meta):
        fields = IdentitySerializer.Meta.fields + ['reports', 'comparisons']

    def get_reports(self, obj):
        from reports.serializers import CreditReportSerializer
        return CreditReportSerializer(
            obj.reports.all(), many=True, context=self.context
        ).data
