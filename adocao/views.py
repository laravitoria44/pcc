from django.shortcuts import redirect, render

def home(request):
    return render(request, 'adocao/index.html')

def sobre(request):
    return render(request, 'adocao/sobre.html')

def vacinacao(request):
    return render(request, 'adocao/vacinacao.html')

def quero_adotar(request):
    return redirect('animais:lista')

def contato(request):
    return render(request, 'adocao/contato.html')
