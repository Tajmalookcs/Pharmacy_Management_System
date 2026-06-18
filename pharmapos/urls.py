from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render


def handler400(request, exception=None):
    return render(request, '400.html', status=400)

def handler403(request, exception=None):
    return render(request, '403.html', status=403)

def handler404(request, exception=None):
    return render(request, '404.html', {'path': request.path}, status=404)

def handler500(request):
    return render(request, '500.html', status=500)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('inventory/', include('apps.inventory.urls')),
    path('sales/', include('apps.sales.urls')),
    path('reports/', include('apps.reports.urls')),
    path('settings/', include('apps.settings_app.urls')),
    path('', include('apps.accounts.urls_dashboard')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
