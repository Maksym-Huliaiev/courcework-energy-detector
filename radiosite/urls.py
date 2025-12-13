from django.contrib import admin
from django.urls import path
from scanner import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='home'),
    path('api/scan/', views.scan_api, name='scan_api'),
    path('api/history/', views.history_api, name='history_api'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
