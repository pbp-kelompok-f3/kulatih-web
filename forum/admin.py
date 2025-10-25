# forum/admin.py
from django.contrib import admin
from django.db.models import Count, Sum
from .models import ForumPost, Vote, Comment


# ========= Inlines (read-only) =========
class ReadOnlyInlineBase:
    can_delete = False
    extra = 0
    show_change_link = True

    def has_add_permission(self, request, obj=None): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False


class CommentInline(ReadOnlyInlineBase, admin.TabularInline):
    model = Comment
    fk_name = "post"
    fields = ("author", "name", "parent", "content", "is_active", "created_at")
    readonly_fields = fields


class VoteInline(ReadOnlyInlineBase, admin.TabularInline):
    model = Vote
    fk_name = "post"
    fields = ("user", "value", "created_at")
    readonly_fields = fields


# ========= ForumPost =========
@admin.register(ForumPost)
class ForumPostAdmin(admin.ModelAdmin):
    list_display  = ("short_content", "author", "score_total", "comments_total", "created_at")
    list_filter   = ("created_at",)
    search_fields = ("content", "author__username")
    ordering      = ("-created_at",)
    readonly_fields = ("id", "author", "content", "created_at")
    inlines = [CommentInline, VoteInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            comments_total=Count("comments", distinct=True),
            score_sum=Sum("votes__value"),
        )

    @admin.display(description="Content")
    def short_content(self, obj):
        return (obj.content or "")[:60]

    @admin.display(description="Comments")
    def comments_total(self, obj):
        return getattr(obj, "comments_total", 0)

    @admin.display(description="Score")
    def score_total(self, obj):
        return getattr(obj, "score_sum", 0) or 0

    # READ-ONLY
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
    def has_view_permission(self, request, obj=None): return True


# ========= Comment (no vote) =========
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display  = ("short_content", "post", "author_or_name", "parent", "is_active", "created_at")
    list_filter   = ("is_active", "created_at")
    search_fields = ("content", "author__username", "name", "post__content")
    ordering      = ("-created_at",)
    readonly_fields = ("id", "post", "author", "name", "parent", "content", "is_active", "created_at")

    @admin.display(description="Content")
    def short_content(self, obj):
        return (obj.content or "")[:60]

    @admin.display(description="Author")
    def author_or_name(self, obj):
        return obj.author or obj.name or "Anon"

    # READ-ONLY
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
    def has_view_permission(self, request, obj=None): return True


# ========= Vote (post) =========
@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display  = ("post", "user", "value", "created_at")
    list_filter   = ("value", "created_at")
    search_fields = ("post__content", "user__username")
    ordering      = ("-created_at",)
    readonly_fields = ("id", "post", "user", "value", "created_at")

    # READ-ONLY
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
    def has_view_permission(self, request, obj=None): return True
