from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id","coach","reviewer","rating","created_at")
    list_filter = ("rating","created_at")
    search_fields = ("comment","coach__username","reviewer__username")
