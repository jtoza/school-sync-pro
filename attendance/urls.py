from django.urls import path

from . import views

app_name = 'attendance'

urlpatterns = [
    path('', views.AttendanceRegisterListView.as_view(), name='register_list'),
    path('create/', views.AttendanceRegisterCreateView.as_view(), name='register_create'),
    path('bulk-create/', views.BulkRegisterCreateView.as_view(), name='bulk_register_create'),
    path('<int:pk>/', views.AttendanceRegisterDetailView.as_view(), name='register_detail'),
    path('<int:pk>/edit/', views.AttendanceRegisterUpdateView.as_view(), name='register_edit'),
    path('<int:pk>/delete/', views.AttendanceRegisterDeleteView.as_view(), name='register_delete'),
    path('<int:pk>/take/', views.take_attendance, name='take_attendance'),
    path('<int:pk>/lock/', views.lock_register, name='lock_register'),
    path('<int:pk>/unlock/', views.unlock_register, name='unlock_register'),
    path('reports/', views.AttendanceReportView.as_view(), name='attendance_reports'),
    path('api/summary-data/', views.attendance_summary_data, name='attendance_summary_data'),
    path('dashboard/', views.DailyAttendanceDashboard.as_view(), name='daily_dashboard'),
]