from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "coach", "reviewer", "rating", "short_comment", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = (
        "comment",
        "reviewer__user__username",   
        "coach__user__username",      
    )
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_per_page = 50
    list_select_related = ("coach", "reviewer")

    # Detail page
    readonly_fields = ("id", "created_at")
    fields = ("id", "coach", "reviewer", "rating", "comment", "created_at")

    @admin.display(description="Comment")
    def short_comment(self, obj):
        return (obj.comment or "")[:60]

    # read-only di admin
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return True
