from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from apps.students.models import Student
from apps.staffs.models import Staff
from .models import Vehicle, Route, TransportAssignment


# Vehicles
class VehicleListView(ListView):
    model = Vehicle
    template_name = 'transport/vehicle_list.html'


class VehicleDetailView(DetailView):
    model = Vehicle
    template_name = 'transport/vehicle_detail.html'


class VehicleCreateView(CreateView):
    model = Vehicle
    fields = '__all__'
    template_name = 'transport/vehicle_form.html'


class VehicleUpdateView(UpdateView):
    model = Vehicle
    fields = '__all__'
    template_name = 'transport/vehicle_form.html'


class VehicleDeleteView(DeleteView):
    model = Vehicle
    success_url = reverse_lazy('transport:vehicle-list')
    template_name = 'transport/vehicle_confirm_delete.html'


# Routes
class RouteListView(ListView):
    model = Route
    template_name = 'transport/route_list.html'


class RouteDetailView(DetailView):
    model = Route
    template_name = 'transport/route_detail.html'


class RouteCreateView(CreateView):
    model = Route
    fields = '__all__'
    template_name = 'transport/route_form.html'


class RouteUpdateView(UpdateView):
    model = Route
    fields = '__all__'
    template_name = 'transport/route_form.html'


class RouteDeleteView(DeleteView):
    model = Route
    success_url = reverse_lazy('transport:route-list')
    template_name = 'transport/route_confirm_delete.html'


# Assignments
class AssignmentListView(ListView):
    model = TransportAssignment
    template_name = 'transport/assignment_list.html'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().select_related('route', 'vehicle')
        entity_type = self.request.GET.get('type')
        if entity_type == 'student':
            qs = qs.filter(entity_content_type=ContentType.objects.get_for_model(Student))
        elif entity_type == 'staff':
            qs = qs.filter(entity_content_type=ContentType.objects.get_for_model(Staff))
        return qs


class AssignmentCreateView(CreateView):
    model = TransportAssignment
    fields = ['entity_content_type', 'entity_object_id', 'route', 'vehicle', 'start_date', 'end_date', 'is_active', 'notes']
    template_name = 'transport/assignment_form.html'


class AssignmentUpdateView(UpdateView):
    model = TransportAssignment
    fields = ['entity_content_type', 'entity_object_id', 'route', 'vehicle', 'start_date', 'end_date', 'is_active', 'notes']
    template_name = 'transport/assignment_form.html'


class AssignmentDeleteView(DeleteView):
    model = TransportAssignment
    success_url = reverse_lazy('transport:assignment-list')
    template_name = 'transport/assignment_confirm_delete.html'
