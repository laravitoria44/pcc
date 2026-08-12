from django.urls import path

from . import views

app_name = 'animais'

urlpatterns = [
    path('', views.ListaAnimaisView.as_view(), name='lista'),
    path('<int:id_animal>/', views.DetalheAnimalView.as_view(), name='detalhe'),
    path(
        '<int:id_animal>/vacinacoes/',
        views.VacinacoesAnimalView.as_view(),
        name='vacinacoes',
    ),
    path(
        '<int:id_animal>/saude/',
        views.SaudeAnimalView.as_view(),
        name='saude',
    ),
]
