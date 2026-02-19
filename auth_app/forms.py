from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "__all__"


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        "class": "form-control",
        "placeholder": "ایمیل"
    }))
    username = forms.CharField(required=True, widget=forms.TextInput(attrs={
        "class": "form-control",
        "placeholder": "نام کاربری"
    }))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        "class": "form-control",
        "placeholder": "رمز عبور"
    }))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        "class": "form-control",
        "placeholder": "تکرار رمز عبور"
    }))

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("این ایمیل قبلاً ثبت شده است.")
        return email


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label="ایمیل یا نام کاربری", widget=forms.TextInput(attrs={
        "class": "form-control",
        "placeholder": "ایمیل یا نام کاربری"
    }))
    password = forms.CharField(label="رمز عبور", widget=forms.PasswordInput(attrs={
        "class": "form-control",
        "placeholder": "رمز عبور"
    }))

    def clean(self):
        username_or_email = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username_or_email and password:
            try:
                user_obj = User.objects.get(email=username_or_email)
                username = user_obj.username
            except User.DoesNotExist:
                username = username_or_email

            self.user_cache = authenticate(self.request, username=username, password=password)

            if self.user_cache is None:
                raise forms.ValidationError("اطلاعات ورود اشتباه است.")

            self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data
