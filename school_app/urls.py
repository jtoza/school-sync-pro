from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView, TemplateView
from django.shortcuts import redirect
from django.http import HttpResponse, FileResponse
from django.http import HttpResponse, FileResponse
import os
from apps.corecode import views
from apps.corecode.views_test import test_database

# Custom redirect view to handle the accounts/login issue
def redirect_to_login(request):
    return redirect('/login/')

# PWA Views - serve with correct headers
def manifest_view(request):
    manifest_path = os.path.join(settings.BASE_DIR, 'templates', 'manifest.json')
    with open(manifest_path, 'r') as f:
        content = f.read()
    return HttpResponse(content, content_type='application/manifest+json')

def service_worker_view(request):
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'js', 'sw.js')
    with open(sw_path, 'r') as f:
        content = f.read()
    response = HttpResponse(content, content_type='application/javascript')
    # Add cache control headers for service worker
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

urlpatterns = [
    # Handle the accounts/login/ URL that Django's auth system expects
    path('accounts/login/', redirect_to_login),
    path('accounts/logout/', RedirectView.as_view(pattern_name='logout', permanent=True)),
    
    path('admin/', admin.site.urls),
    path('', views.landing_view, name='home'),
    path('dashboard/', views.IndexView.as_view(), name='dashboard'),
    path('core/', include(('apps.corecode.urls', 'corecode'), namespace='corecode')),
    path('students/', include('apps.students.urls', namespace='students')),  # ADDED NAMESPACE
    path('staffs/', include('apps.staffs.urls', namespace='staffs')),
    path('finance/', include('apps.finance.urls')),
    path('result/', include('apps.result.urls')),
    path('parents/', include('apps.parents.urls')),
    path('attendance/', include('attendance.urls', namespace='attendance')),
    
    # PWA URLs - serve with proper headers
    path('manifest.json', manifest_view, name='manifest'),
    path('service-worker.js', service_worker_view, name='service_worker'),
    path('offline/', TemplateView.as_view(template_name='offline.html'), name='offline'),
    path('idcards/', include('apps.idcards.urls', namespace='idcards')),  # ADDED NAMESPACE

    path('sync/', include('apps.sync.urls')),
    path('sync/test/', TemplateView.as_view(template_name='sync_test.html'), name='sync_test'),
    path('portfolio/', include('student_portfolio.urls')),
    path('backup/', include('backup_manager.urls')),
    path('homework/', include('apps.homework.urls')),
    path('chat/', include('chatroom.urls', namespace='chatroom')),
    path('test-db/', test_database, name='test_db'),

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)