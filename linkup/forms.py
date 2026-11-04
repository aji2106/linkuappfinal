from django import forms
from django.contrib.auth.models import User
from .models import Profile  # This is required to enable the user to update their profile information


class UserUpdateForm(forms.ModelForm):
	email = forms.EmailField()

	class Meta:
		model = User
		fields = ['username', 'email']

class ProfileUpdateForm(forms.ModelForm):
	class Meta:
		model = Profile
		fields = ['image']


from django.contrib.auth.forms import UserCreationForm

class RegistrationForm(UserCreationForm):
    email = forms.EmailField()

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account already uses this email address.")
        return email
