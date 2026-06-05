from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CaseViewSet, ReferenceDataViewSet, ComparisonResultViewSet

router = DefaultRouter()
router.register('cases', CaseViewSet, basename='case')
router.register('reference-data', ReferenceDataViewSet, basename='reference-data')
router.register('comparisons', ComparisonResultViewSet, basename='comparison')

urlpatterns = [
    path('', include(router.urls)),
]
