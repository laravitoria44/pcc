from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = 'usuarios'

urlpatterns = [
    path('entrar/', views.UsuarioLoginView.as_view(), name='login'),
    path('cadastrar/', views.cadastro, name='cadastro'),
    path('sair/', LogoutView.as_view(), name='logout'),
    path('perfil/', views.perfil, name='perfil'),
]
