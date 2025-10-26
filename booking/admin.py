from django.contrib import admin
from django.utils.html import format_html
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Read-only admin for Booking model with colored status display."""

    # Kolom yang tampil di list view
    list_display = (
        "id",
        "member",
        "coach",
        "date",
        "start_time",
        "end_time",
        "colored_status",
        "location",
        "created_at",
    )

    # Filter dan pencarian
    list_filter = ("status", "date", "coach")
    search_fields = (
        "member__user__username",
        "member__user__first_name",
        "coach__user__username",
        "location",
    )

    ordering = ("-date", "-start_time")
    list_per_page = 20

    # 🔹 Warna status biar cepat dibedain
    def colored_status(self, obj):
        color = {
            "pending": "#eab308",     # kuning
            "confirmed": "#22c55e",   # hijau
            "cancelled": "#6b7280",   # abu
            "completed": "#3b82f6",   # biru
            "rescheduled": "#a855f7", # ungu
        }.get(obj.status, "#ffffff")
        return format_html(f"<strong style='color:{color}'>{obj.get_status_display()}</strong>")

    colored_status.short_description = "Status"

    # 🔒 Biar cuma bisa lihat, gak bisa edit / hapus / tambah
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return True
