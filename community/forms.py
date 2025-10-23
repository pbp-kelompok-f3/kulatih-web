from django import forms
from django.utils.text import slugify
from .models import Community, Message

class CommunityCreateForm(forms.ModelForm):
    class Meta:
        model = Community
        fields = ['name', 'short_description', 'full_description', 'profile_image_url']

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise forms.ValidationError("Nama tidak boleh kosong.")
        return name

    def save(self, commit=True, user=None):
        obj = super().save(commit=False) 
        # buat slug sederhana dari name
        obj.slug = slugify(obj.name)
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
            'text': forms.TextInput(attrs={'placeholder': 'Ketik pesan…'})
        }
