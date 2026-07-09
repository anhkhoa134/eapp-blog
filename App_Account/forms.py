from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .password_validation import validate_strong_password

class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "password1", "password2"]

    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        username = self.cleaned_data.get("username")
        if password1:
            validate_strong_password(password1, username=username)
        return password1

class CustomPasswordChangeForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput())
    password1 = forms.CharField(widget=forms.PasswordInput())
    password2 = forms.CharField(widget=forms.PasswordInput())

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_old_password(self):
        old_password = self.cleaned_data.get("old_password")
        if not self.user.check_password(old_password):
            raise forms.ValidationError("Mật khẩu cũ không chính xác.")
        return old_password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Mật khẩu mới không khớp.")
        
        if password1:
            validate_strong_password(password1, user=self.user)
        
        return cleaned_data

    def save(self):
        new_password = self.cleaned_data.get("password1")
        self.user.set_password(new_password)
        self.user.save()
        return self.user

