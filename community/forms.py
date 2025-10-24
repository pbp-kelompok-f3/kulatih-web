from django import forms
<<<<<<< HEAD
=======
from django.utils.text import slugify
>>>>>>> forum-modul-izzati
from .models import Community, Message

class CommunityCreateForm(forms.ModelForm):
    class Meta:
        model = Community
        fields = ['name', 'short_description', 'full_description', 'profile_image_url']
<<<<<<< HEAD
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full rounded-full px-6 py-3 text-black focus:outline-none'
            }),
            'short_description': forms.TextInput(attrs={
                'class': 'w-full rounded-full px-6 py-3 text-black focus:outline-none'
            }),
            'full_description': forms.Textarea(attrs={
                'class': 'w-full rounded-2xl px-6 py-3 text-black focus:outline-none'
            }),
            'profile_image_url': forms.URLInput(attrs={
                'class': 'w-full rounded-full px-6 py-3 text-black focus:outline-none'
            }),
        }
=======
>>>>>>> forum-modul-izzati

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise forms.ValidationError("Nama tidak boleh kosong.")
        return name

    def save(self, commit=True, user=None):
<<<<<<< HEAD
        obj = super().save(commit=False)
=======
        obj = super().save(commit=False) 
        # buat slug sederhana dari name
        obj.slug = slugify(obj.name)
>>>>>>> forum-modul-izzati
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
<<<<<<< HEAD
            'text': forms.TextInput(attrs={
                'placeholder': 'Ketik pesan…',
                'class': 'w-full px-4 py-2 text-black rounded-lg focus:outline-none'
            })
=======
            'text': forms.TextInput(attrs={'placeholder': 'Ketik pesan…'})
>>>>>>> forum-modul-izzati
        }
