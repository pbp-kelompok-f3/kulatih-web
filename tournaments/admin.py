from django.contrib import admin
from .models import Tournament

@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = (
        'namaTournaments',
        'tipeTournaments',
        'tanggalTournaments',
        'lokasiTournaments',
        'pembuatTournaments',
        'flagTournaments'
    )
    search_fields = (
        'namaTournaments',
        'tipeTournaments',
        'lokasiTournaments',
        'pembuatTournaments__user__username'
    )
    list_filter = (
        'tipeTournaments',
        'tanggalTournaments',
        'flagTournaments'
    )
    ordering = ('-tanggalTournaments',)
    readonly_fields = (
        'namaTournaments',
        'tipeTournaments',
        'tanggalTournaments',
        'lokasiTournaments',
        'deskripsiTournaments',
        'posterTournaments',
        'pembuatTournaments',
        'pesertaTournaments',
        'flagTournaments',
        'idTournaments',
    )
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
