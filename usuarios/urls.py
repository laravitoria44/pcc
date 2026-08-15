from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views

app_name = 'usuarios'

urlpatterns = [
    path('entrar/', views.UsuarioLoginView.as_view(), name='login'),
    path('cadastrar/', views.cadastro, name='cadastro'),
    path(
        'recuperar-senha/',
        auth_views.PasswordResetView.as_view(
            template_name='usuarios/password_reset_form.html',
            email_template_name='usuarios/password_reset_email.html',
            subject_template_name='usuarios/password_reset_subject.txt',
            success_url=reverse_lazy('usuarios:password_reset_done'),
        ),
        name='password_reset',
    ),
    path(
        'recuperar-senha/enviado/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='usuarios/password_reset_done.html',
        ),
        name='password_reset_done',
    ),
    path(
        'redefinir-senha/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='usuarios/password_reset_confirm.html',
            success_url=reverse_lazy('usuarios:password_reset_complete'),
        ),
        name='password_reset_confirm',
    ),
    path(
        'redefinir-senha/concluida/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='usuarios/password_reset_complete.html',
        ),
        name='password_reset_complete',
    ),
    path('sair/', auth_views.LogoutView.as_view(), name='logout'),
    path('perfil/', views.perfil, name='perfil'),
]
