from django.urls import path
from .views import (
    VehicleListView, VehicleDetailView, VehicleCreateView, VehicleUpdateView, VehicleDeleteView,
    RouteListView, RouteDetailView, RouteCreateView, RouteUpdateView, RouteDeleteView,
    AssignmentListView, AssignmentCreateView, AssignmentUpdateView, AssignmentDeleteView,
)

app_name = 'transport'

urlpatterns = [
    path('vehicles/', VehicleListView.as_view(), name='vehicle-list'),
    path('vehicles/create/', VehicleCreateView.as_view(), name='vehicle-create'),
    path('vehicles/<int:pk>/', VehicleDetailView.as_view(), name='vehicle-detail'),
    path('vehicles/<int:pk>/update/', VehicleUpdateView.as_view(), name='vehicle-update'),
    path('vehicles/<int:pk>/delete/', VehicleDeleteView.as_view(), name='vehicle-delete'),

    path('routes/', RouteListView.as_view(), name='route-list'),
    path('routes/create/', RouteCreateView.as_view(), name='route-create'),
    path('routes/<int:pk>/', RouteDetailView.as_view(), name='route-detail'),
    path('routes/<int:pk>/update/', RouteUpdateView.as_view(), name='route-update'),
    path('routes/<int:pk>/delete/', RouteDeleteView.as_view(), name='route-delete'),

    path('assignments/', AssignmentListView.as_view(), name='assignment-list'),
    path('assignments/create/', AssignmentCreateView.as_view(), name='assignment-create'),
    path('assignments/<int:pk>/update/', AssignmentUpdateView.as_view(), name='assignment-update'),
    path('assignments/<int:pk>/delete/', AssignmentDeleteView.as_view(), name='assignment-delete'),
]
