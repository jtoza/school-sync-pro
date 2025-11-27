from django.urls import path
from . import views

urlpatterns = [
    path('', views.ParentPortalHomeView.as_view(), name='parent-portal-home'),
    path('lookup/', views.StudentFeeLookupView.as_view(), name='student-fee-lookup'),
    path('student/<int:student_id>/fees/', views.StudentFeeDetailPublicView.as_view(), name='student-fee-detail-public'),
    path('receipt/<int:receipt_id>/download/', views.DownloadReceiptView.as_view(), name='download-receipt'),
    path('statement/<int:student_id>/', views.StudentStatementView.as_view(), name='student-statement'),
]

