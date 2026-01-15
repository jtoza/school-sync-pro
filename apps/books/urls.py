from django.urls import path
from .views import (
    BookListView, BookDetailView, BookCreateView, BookUpdateView, BookDeleteView,
    BorrowListView, BorrowCreateView, BorrowUpdateView, BorrowDeleteView,
)

app_name = 'books'

urlpatterns = [
    path('books/', BookListView.as_view(), name='book-list'),
    path('books/create/', BookCreateView.as_view(), name='book-create'),
    path('books/<int:pk>/', BookDetailView.as_view(), name='book-detail'),
    path('books/<int:pk>/update/', BookUpdateView.as_view(), name='book-update'),
    path('books/<int:pk>/delete/', BookDeleteView.as_view(), name='book-delete'),

    path('borrows/', BorrowListView.as_view(), name='borrow-list'),
    path('borrows/create/', BorrowCreateView.as_view(), name='borrow-create'),
    path('borrows/<int:pk>/update/', BorrowUpdateView.as_view(), name='borrow-update'),
    path('borrows/<int:pk>/delete/', BorrowDeleteView.as_view(), name='borrow-delete'),
]
