from django.urls import path
from . import views
from .views import (
    StaffCreateView,
    StaffDeleteView,
    StaffDetailView,
    StaffListView,
    StaffUpdateView,
)

app_name = 'staffs'

urlpatterns = [
    path("list/", StaffListView.as_view(), name="staff-list"),
    path("<int:pk>/", StaffDetailView.as_view(), name="staff-detail"),
    path("create/", StaffCreateView.as_view(), name="staff-create"),
    path("<int:pk>/update/", StaffUpdateView.as_view(), name="staff-update"),
    path("<int:pk>/delete/", StaffDeleteView.as_view(), name="staff-delete"),
    path('attendance/', views.teacher_attendance_dashboard, name='attendance-dashboard'),
    path('attendance/mark/', views.mark_attendance, name='mark-attendance'),
    path('attendance/records/', views.attendance_records, name='attendance-records'),
]