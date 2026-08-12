from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, FormView, ListView

from animais.models import Animal
from usuarios.mixins import ClienteRequiredMixin

from .forms import SolicitacaoAdocaoForm
from .models import SolicitacaoAdocao


class MinhasSolicitacoesView(ClienteRequiredMixin, ListView):
    model = SolicitacaoAdocao
    template_name = 'adocao/minhas_solicitacoes.html'
    context_object_name = 'solicitacoes'
    paginate_by = 10
    permission_required = ('adocao.view_solicitacaoadocao',)

    def get_queryset(self):
        return SolicitacaoAdocao.objects.filter(
            cliente=self.request.user,
        ).select_related('animal', 'administrador_avaliador')


class DetalheSolicitacaoView(ClienteRequiredMixin, DetailView):
    model = SolicitacaoAdocao
    template_name = 'adocao/detalhe_solicitacao.html'
    context_object_name = 'solicitacao'
    pk_url_kwarg = 'id_solicitacao'
    permission_required = ('adocao.view_solicitacaoadocao',)

    def get_queryset(self):
        return SolicitacaoAdocao.objects.filter(
            cliente=self.request.user,
        ).select_related('animal', 'administrador_avaliador')


class CriarSolicitacaoView(ClienteRequiredMixin, FormView):
    template_name = 'adocao/criar_solicitacao.html'
    form_class = SolicitacaoAdocaoForm
    permission_required = ('adocao.add_solicitacaoadocao',)

    def get_animal(self):
        if not hasattr(self, 'animal'):
            self.animal = get_object_or_404(
                Animal,
                pk=self.kwargs['id_animal'],
            )
        return self.animal

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'cliente': self.request.user, 'animal': self.get_animal()})
        return kwargs

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['animal'] = self.get_animal()
        return contexto

    def form_valid(self, form):
        solicitacao = form.save()
        messages.success(
            self.request,
            f'Solicitação de adoção de {self.get_animal().nome} enviada com sucesso.',
        )
        return redirect('adocoes:detalhe', id_solicitacao=solicitacao.pk)
