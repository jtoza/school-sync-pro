from django.contrib import admin
from .models import PortfolioCategory, PortfolioItem

@admin.register(PortfolioCategory)
class PortfolioCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']

@admin.register(PortfolioItem)
class PortfolioItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'student', 'category', 'file_type', 'created_at', 'is_published']
    list_filter = ['category', 'file_type', 'is_published', 'created_at']
    search_fields = ['title', 'description', 'student__user__username']