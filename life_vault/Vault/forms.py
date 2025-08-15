from django import forms
from .models import UploadedFile
from .models import Nominee
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import SecureVaultItem
from django.db.models import Q
from .models import UserProfile
class FileUploadForm(forms.ModelForm):
    class Meta:
        model = UploadedFile
        fields = ['file']

# forms.py


class NomineeForm(forms.ModelForm):
    class Meta:
        model = Nominee
        fields = ['name', 'email', 'phone', 'notifications']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class SecureVaultForm(forms.Form):
    ITEM_TYPES = (
        ('id', 'IDs & Passport'),
        ('password', 'Passwords'),
        ('crypto', 'Crypto Wallet'),
        ('bank', 'Bank Details'),
        ('atm', 'ATM Card'),
        ('other', 'Others'),
    )
    item_type = forms.ChoiceField(choices=ITEM_TYPES)
    name = forms.CharField(max_length=255)



class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    full_name = forms.CharField(required=True, max_length=100)


    class Meta:
        model = User
        fields = ("full_name","email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        names = self.cleaned_data["full_name"].split()
        user.first_name = names[0] if names else ""
        user.last_name = " ".join(names[1:]) if len(names) > 1 else ""
        
        if commit:
            user.save()
        return user
    
class NomineeAssignmentForm(forms.Form):
    documents = forms.ModelMultipleChoiceField(
        queryset = UploadedFile.objects.none(),
        widget = forms.CheckboxSelectMultiple,
        required=False
    )
    vault_items = forms.ModelMultipleChoiceField(
        queryset=SecureVaultItem.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    


    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        nominee_id = kwargs.pop('nominee_id', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['documents'].queryset = UploadedFile.objects.filter(user=user)
            self.fields['vault_items'].queryset = SecureVaultItem.objects.filter(user=user)
            #self.fields['nominees'].queryset = Nominee.objects.filter(user=user)


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_picture']

