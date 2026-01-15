from django.db import models
from django.urls import reverse
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Book(models.Model):
    STATUS = (
        ('available', 'Available'),
        ('unavailable', 'Unavailable'),
    )
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=120)
    isbn = models.CharField(max_length=20, unique=True)
    category = models.CharField(max_length=100, blank=True)
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS, default='available')

    def __str__(self):
        return f"{self.title} ({self.isbn})"

    def get_absolute_url(self):
        return reverse('books:book-detail', kwargs={'pk': self.pk})


class BorrowRecord(models.Model):
    STATUS = (
        ('borrowed', 'Borrowed'),
        ('returned', 'Returned'),
    )
    borrower_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    borrower_object_id = models.PositiveIntegerField()
    borrower = GenericForeignKey('borrower_content_type', 'borrower_object_id')

    book = models.ForeignKey(Book, on_delete=models.PROTECT, related_name='borrows')
    borrowed_on = models.DateField(auto_now_add=True)
    due_on = models.DateField()
    returned_on = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS, default='borrowed')
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.book} -> {self.borrower} ({self.status})"

    def get_absolute_url(self):
        return reverse('books:borrow-list')
