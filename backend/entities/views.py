from rest_framework import viewsets
from .models import Subject, FinancialAccount, Address
from .serializers import SubjectSerializer, FinancialAccountSerializer, AddressSerializer


class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Subject.objects.prefetch_related(
        'alternate_names', 'addresses', 'financial_accounts'
    ).select_related('report').all()
    serializer_class = SubjectSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        report_id = self.request.query_params.get('report')
        if report_id:
            qs = qs.filter(report_id=report_id)
        return qs
