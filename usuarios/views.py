from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render

from .forms import UsuarioCadastroForm, UsuarioLoginForm


class UsuarioLoginView(LoginView):
    authentication_form = UsuarioLoginForm
    template_name = 'usuarios/login.html'
    redirect_authenticated_user = True


def cadastro(request):
    if request.user.is_authenticated:
        return redirect('usuarios:perfil')

    if request.method == 'POST':
        form = UsuarioCadastroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            messages.success(request, 'Cadastro realizado com sucesso.')
            return redirect('home')
    else:
        form = UsuarioCadastroForm()

    return render(request, 'usuarios/cadastro.html', {'form': form})


@login_required
def perfil(request):
    return render(request, 'usuarios/perfil.html')
