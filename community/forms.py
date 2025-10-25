from django import forms
from .models import Community, Message

class CommunityCreateForm(forms.ModelForm):
    class Meta:
        model = Community
        fields = ['name', 'short_description', 'full_description', 'profile_image_url']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full rounded-full px-6 py-3 text-black focus:outline-none'
            }),
            'short_description': forms.TextInput(attrs={
                'class': 'w-full rounded-full px-6 py-3 text-black focus:outline-none'
            }),
            'full_description': forms.Textarea(attrs={
                'class': 'w-full rounded-2xl px-6 py-3 text-black focus:outline-none resize-none'
            }),
            'profile_image_url': forms.URLInput(attrs={
                'class': 'w-full rounded-full px-6 py-3 text-black focus:outline-none',
                'placeholder': 'URL HTTP/S'
            }),
        }

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise forms.ValidationError("Nama tidak boleh kosong.")
        return name
    
    def clean_profile_image_url(self):
        url = self.cleaned_data.get('profile_image_url')

        # Jika kosong, kembalikan None tanpa error
        if not url:
            return None

        url = url.strip()
        if not (url.startswith('http://') or url.startswith('https://') or url.startswith('data:image/')):
            raise forms.ValidationError(
                "URL harus dimulai dengan http://, https://, atau data:image/ untuk base64"
            )
        return url


    def save(self, commit=True, user=None):
        obj = super().save(commit=False)
        if user is not None:
            obj.created_by = user
        if commit:
            obj.save()
        return obj


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['text']
        widgets = {
            'text': forms.TextInput(attrs={
                'placeholder': 'Ketik pesan…',
                'class': 'w-full px-4 py-2 text-black rounded-lg focus:outline-none'
            })
        }