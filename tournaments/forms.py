from django import forms
from .models import Tournament

class TournamentForm(forms.ModelForm):
    class Meta:
        model = Tournament
        fields = [
            'tipeTournaments',
            'namaTournaments',
            'tanggalTournaments',
            'lokasiTournaments',
            'deskripsiTournaments',
            'posterTournaments',
        ]
        widgets = {
            'tanggalTournaments': forms.DateInput(attrs={'type': 'date'}),
            'deskripsiTournaments': forms.Textarea(attrs={'rows': 3}),
        }
