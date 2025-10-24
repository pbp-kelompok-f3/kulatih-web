from django.contrib import admin
from .models import Community, Membership, Message


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'short_description',
        'created_by',
        'created_at',
    )
    search_fields = (
        'name',
        'short_description',
        'created_by__username',
    )
    list_filter = ('created_at',)
    ordering = ('-created_at',)
    readonly_fields = (
        'name',
        'short_description',
        'full_description',
        'profile_image_url',
        'created_by',
        'created_at',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = (
        'community',
        'user',
        'role',
        'joined_at',
    )
    search_fields = (
        'community__name',
        'user__username',
        'role',
    )
    list_filter = ('role', 'joined_at')
    ordering = ('-joined_at',)
    readonly_fields = (
        'community',
        'user',
        'role',
        'joined_at',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        'community',
        'sender',
        'text',
        'created_at',
    )
    search_fields = (
        'community__name',
        'sender__username',
        'text',
    )
    list_filter = ('created_at',)
    ordering = ('-created_at',)
    readonly_fields = (
        'community',
        'sender',
        'text',
        'created_at',
        'updated_at',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
