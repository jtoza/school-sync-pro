from django.contrib import admin
from .models import Vehicle, Route, TransportAssignment


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("plate_number", "model", "capacity", "driver_name", "status")
    search_fields = ("plate_number", "model", "driver_name")
    list_filter = ("status",)


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ("name", "start_point", "end_point", "fare")
    search_fields = ("name", "start_point", "end_point")


@admin.register(TransportAssignment)
class TransportAssignmentAdmin(admin.ModelAdmin):
    list_display = ("entity", "route", "vehicle", "start_date", "end_date", "is_active")
    list_filter = ("is_active", "route")
    search_fields = ("entity_object_id",)
