from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model


User = get_user_model()

class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True, label='E-mail')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fields in self.fields.values():
            css = fields.widget.attrs.get('class', '')
            fields.widget.attrs['class'] = (css + ' form-control').strip()

    def clean_email(self):
        email = self.clean_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exist():
            raise forms.ValidationError('Já existe um usuário com este e-mail')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].strip().lower()
        if commit:
            user.save()
        return user