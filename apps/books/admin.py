from django.contrib import admin
from .models import Book, BorrowRecord


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "isbn", "category", "total_copies", "available_copies", "status")
    search_fields = ("title", "author", "isbn")
    list_filter = ("status", "category")


@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display = ("book", "borrower", "borrowed_on", "due_on", "returned_on", "status")
    list_filter = ("status", "borrowed_on", "due_on")
    search_fields = ("book__title", "borrower_object_id")
