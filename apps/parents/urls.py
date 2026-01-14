from django.urls import path
from .views import parent_access

urlpatterns = [
    path('access/', parent_access, name='parent-access'),
]
