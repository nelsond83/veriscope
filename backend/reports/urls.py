from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CreditReportViewSet

router = DefaultRouter()
router.register('reports', CreditReportViewSet, basename='report')

urlpatterns = [
    path('', include(router.urls)),
]
