from django.urls import path
from . import views

app_name = 'student_portfolio'

urlpatterns = [
    path('', views.PortfolioListView.as_view(), name='portfolio_list'),
    path('item/<int:pk>/', views.PortfolioDetailView.as_view(), name='portfolio_detail'),
    path('item/<int:pk>/public/', views.PublicPortfolioView.as_view(), name='portfolio_public'),
    path('create/', views.PortfolioCreateView.as_view(), name='portfolio_create'),
    path('item/<int:pk>/update/', views.PortfolioUpdateView.as_view(), name='portfolio_update'),
    path('item/<int:pk>/delete/', views.PortfolioDeleteView.as_view(), name='portfolio_delete'),
]