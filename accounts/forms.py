from django import forms
from django.contrib.auth.forms import AuthenticationForm

from accounts.models import User


class InstitutionalLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Usuario institucional",
        widget=forms.TextInput(attrs={"autocomplete": "username", "placeholder": "usuario@uncp.edu.pe", "autofocus": True}),
    )
    password = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password", "placeholder": "Tu contraseña"}),
    )
