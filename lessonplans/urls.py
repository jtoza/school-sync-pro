from django.urls import path
from . import views

app_name = 'lessonplans'

urlpatterns = [
    # Main lesson plan views
    path('', views.LessonPlanListView.as_view(), name='list'),
    path('my-plans/', views.MyLessonPlansView.as_view(), name='my_plans'),
    path('create/', views.LessonPlanCreateView.as_view(), name='create'),
    path('<int:pk>/', views.LessonPlanDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.LessonPlanUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.LessonPlanDeleteView.as_view(), name='delete'),
    
    # Attachments
    path('<int:pk>/add-attachment/', views.add_attachment, name='add_attachment'),
    path('attachment/<int:pk>/delete/', views.delete_attachment, name='delete_attachment'),
    
    # Comments
    path('<int:pk>/add-comment/', views.add_comment, name='add_comment'),
    path('comment/<int:pk>/toggle-resolved/', views.toggle_comment_resolved, name='toggle_comment_resolved'),
    
    # Teacher profiles
    path('teacher/<str:username>/', views.teacher_profile_view, name='teacher_profile'),
]