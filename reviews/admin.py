from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'coach', 'reviewer', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = (
        'comment',
        'reviewer__user__username',
        'coach__user__username',
    )
    readonly_fields = ('created_at',)
