from django.db import models
from django.urls import reverse
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Vehicle(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('maintenance', 'Under Maintenance'),
        ('inactive', 'Inactive'),
    )
    plate_number = models.CharField(max_length=20, unique=True)
    model = models.CharField(max_length=50)
    capacity = models.PositiveIntegerField()
    driver_name = models.CharField(max_length=100, blank=True)
    driver_phone = models.CharField(max_length=30, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.plate_number} ({self.model})"

    def get_absolute_url(self):
        return reverse('transport:vehicle-detail', kwargs={'pk': self.pk})


class Route(models.Model):
    name = models.CharField(max_length=100, unique=True)
    start_point = models.CharField(max_length=100)
    end_point = models.CharField(max_length=100)
    fare = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('transport:route-detail', kwargs={'pk': self.pk})


class TransportAssignment(models.Model):
    entity_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    entity_object_id = models.PositiveIntegerField()
    entity = GenericForeignKey('entity_content_type', 'entity_object_id')

    route = models.ForeignKey(Route, on_delete=models.PROTECT, related_name='assignments')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, related_name='assignments', blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.entity} -> {self.route}"

    def get_absolute_url(self):
        return reverse('transport:assignment-list')
