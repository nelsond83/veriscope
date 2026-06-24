from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IdentityViewSet, ComparisonResultViewSet, CorrectionViewSet

router = DefaultRouter()
router.register('identities', IdentityViewSet, basename='identity')
router.register('comparisons', ComparisonResultViewSet, basename='comparison')
router.register('corrections', CorrectionViewSet, basename='correction')

urlpatterns = [
    path('', include(router.urls)),
]
