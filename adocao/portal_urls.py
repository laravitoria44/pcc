from django.urls import path

from . import portal_views

app_name = 'adocoes'

urlpatterns = [
    path('', portal_views.MinhasSolicitacoesView.as_view(), name='minhas'),
    path(
        'solicitar/<int:id_animal>/',
        portal_views.CriarSolicitacaoView.as_view(),
        name='criar',
    ),
    path(
        '<int:id_solicitacao>/',
        portal_views.DetalheSolicitacaoView.as_view(),
        name='detalhe',
    ),
]
