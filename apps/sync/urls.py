from django.urls import path
from . import views
from django.views.generic import TemplateView
app_name = 'sync'

urlpatterns = [
    path('api/sync/', views.SyncData.as_view(), name='sync_data'),
    path('sync/test/', TemplateView.as_view(template_name='sync_test.html'), name='sync_test'),
]