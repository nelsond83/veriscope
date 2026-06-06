from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IdentityViewSet, ComparisonResultViewSet

router = DefaultRouter()
router.register('identities', IdentityViewSet, basename='identity')
router.register('comparisons', ComparisonResultViewSet, basename='comparison')

urlpatterns = [
    path('', include(router.urls)),
]
