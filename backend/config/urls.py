from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from config.auth_views import me, login_view, logout_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/me/', me),
    path('api/auth/login/', login_view),
    path('api/auth/logout/', logout_view),
    path('api/', include('reports.urls')),
    path('api/', include('entities.urls')),
    path('api/', include('identities.urls')),
    path('api/', include('doctemplates.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
