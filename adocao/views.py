from django.shortcuts import render, redirect

def home(request):
    return render(request, 'adocao/index.html')

def sobre(request):
    return render(request, 'adocao/sobre.html')

def vacinacao(request):
    return render(request, 'adocao/vacinacao.html')

# ADICIONE ESTA FUNÇÃO AQUI:
def quero_adotar(request):
    return render(request, 'adocao/quero_adotar.html')

from django.shortcuts import render, redirect
from .models import Contato

def contato(request):
    if request.method == "POST":
        # Captura os dados enviados pelo formulário HTML
        nome_form = request.POST.get('nome')
        email_form = request.POST.get('email')
        telefone_form = request.POST.get('telefone')
        assunto_form = request.POST.get('assunto')
        mensagem_form = request.POST.get('mensagem')

        # Cria o registo na base de dados
        Contato.objects.create(
            nome=nome_form,
            email=email_form,
            telefone=telefone_form,
            assunto=assunto_form,
            mensagem=mensagem_form
        )

        return redirect('contato')

    return render(request, 'adocao/contato.html')