from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from apps.students.models import Student
from apps.staffs.models import Staff
from .models import Book, BorrowRecord


# Books CRUD
class BookListView(ListView):
    model = Book
    template_name = 'books/book_list.html'


class BookDetailView(DetailView):
    model = Book
    template_name = 'books/book_detail.html'


class BookCreateView(CreateView):
    model = Book
    fields = '__all__'
    template_name = 'books/book_form.html'


class BookUpdateView(UpdateView):
    model = Book
    fields = '__all__'
    template_name = 'books/book_form.html'


class BookDeleteView(DeleteView):
    model = Book
    success_url = reverse_lazy('books:book-list')
    template_name = 'books/book_confirm_delete.html'


# Borrowing
class BorrowListView(ListView):
    model = BorrowRecord
    template_name = 'books/borrow_list.html'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().select_related('book')
        borrower_type = self.request.GET.get('type')
        if borrower_type == 'student':
            qs = qs.filter(borrower_content_type=ContentType.objects.get_for_model(Student))
        elif borrower_type == 'staff':
            qs = qs.filter(borrower_content_type=ContentType.objects.get_for_model(Staff))
        return qs


class BorrowCreateView(CreateView):
    model = BorrowRecord
    fields = ['borrower_content_type', 'borrower_object_id', 'book', 'due_on', 'notes']
    template_name = 'books/borrow_form.html'


class BorrowUpdateView(UpdateView):
    model = BorrowRecord
    fields = ['due_on', 'returned_on', 'status', 'notes']
    template_name = 'books/borrow_form.html'


class BorrowDeleteView(DeleteView):
    model = BorrowRecord
    success_url = reverse_lazy('books:borrow-list')
    template_name = 'books/borrow_confirm_delete.html'
