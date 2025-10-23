import django.forms as forms
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
            'namaTournaments': forms.TextInput(attrs={'placeholder': 'Enter tournament name'}),
            'tipeTournaments': forms.Select(),
            'tanggalTournaments': forms.DateInput(attrs={'type': 'date'}),
            'lokasiTournaments': forms.TextInput(attrs={'placeholder': 'Enter location'}),
            'deskripsiTournaments': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter description'}),
            'posterTournaments': forms.URLInput(attrs={'placeholder': 'Enter poster URL'}),
        }
