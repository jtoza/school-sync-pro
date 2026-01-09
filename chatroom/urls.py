from django.urls import path
from . import views

app_name = 'chatroom'

urlpatterns = [
    path('', views.chat_home, name='chat_home'),
    path('create/', views.create_room, name='create_room'),
    path('<int:room_id>/', views.chat_room, name='chat_room'),
    path('<int:room_id>/messages/', views.get_messages, name='get_messages'),
    path('<int:room_id>/add_user/', views.add_user_to_room, name='add_user_to_room'),
    path('<int:room_id>/remove_user/<int:user_id>/', views.remove_user_from_room, name='remove_user_from_room'),
    path('<int:room_id>/delete/', views.delete_room, name='delete_room'),
]