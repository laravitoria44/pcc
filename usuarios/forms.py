import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserChangeForm, UserCreationForm

from .models import Usuario


class UsuarioCadastroForm(UserCreationForm):
    password1 = forms.CharField(
        label='Senha',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )
    password2 = forms.CharField(
        label='Confirme a senha',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )

    class Meta:
        model = Usuario
        fields = ('nome_completo', 'cpf', 'email', 'telefone')
        labels = {
            'nome_completo': 'Nome completo',
            'cpf': 'CPF',
            'email': 'E-mail',
            'telefone': 'Telefone',
        }
        widgets = {
            'nome_completo': forms.TextInput(attrs={'autocomplete': 'name'}),
            'cpf': forms.TextInput(attrs={'autocomplete': 'off', 'inputmode': 'numeric'}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email'}),
            'telefone': forms.TextInput(attrs={'autocomplete': 'tel'}),
        }

    def clean_cpf(self):
        cpf = re.sub(r'\D', '', self.cleaned_data['cpf'])
        if len(cpf) != 11:
            raise forms.ValidationError('Informe um CPF com 11 dígitos.')
        return cpf

    def clean_email(self):
        return Usuario.objects.normalize_email(self.cleaned_data['email']).lower()

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.perfil = Usuario.Perfil.CLIENTE
        if commit:
            usuario.save()
        return usuario


class UsuarioLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'autofocus': True, 'autocomplete': 'email'}),
    )
    password = forms.CharField(
        label='Senha',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
    )


class UsuarioAdminCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = (
            'email',
            'nome_completo',
            'cpf',
            'telefone',
            'perfil',
            'is_active',
        )


class UsuarioAdminChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = Usuario
        fields = '__all__'
