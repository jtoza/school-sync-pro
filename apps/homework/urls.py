from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.HomeworkListView.as_view(), name='homework_list'),
    path('create/', views.HomeworkCreateView.as_view(), name='homework_create'),
    path('update/<int:pk>/', views.HomeworkUpdateView.as_view(), name='homework_update'),
    path('delete/<int:pk>/', views.HomeworkDeleteView.as_view(), name='homework_delete'),
    path('student/', views.student_homework_view, name='student_homework'),
]
