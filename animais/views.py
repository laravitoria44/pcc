from django.db.models import Q
from django.views.generic import DetailView, ListView

from usuarios.mixins import ConsultaPortalMixin
from usuarios.models import Usuario

from .models import Animal


class ListaAnimaisView(ConsultaPortalMixin, ListView):
    model = Animal
    template_name = 'animais/lista.html'
    context_object_name = 'animais'
    paginate_by = 9
    permission_required = ('animais.view_animal',)

    def get_queryset(self):
        queryset = Animal.objects.prefetch_related('fotos').all()
        busca = self.request.GET.get('q', '').strip()
        especie = self.request.GET.get('especie', '').strip()
        porte = self.request.GET.get('porte', '').strip()
        status = self.request.GET.get('status', '').strip()

        if busca:
            queryset = queryset.filter(
                Q(nome__icontains=busca)
                | Q(raca__icontains=busca)
                | Q(cor_pelagem__icontains=busca)
            )
        if especie:
            queryset = queryset.filter(especie=especie)
        if porte:
            queryset = queryset.filter(porte=porte)
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        todos = Animal.objects.all()
        parametros = self.request.GET.copy()
        parametros.pop('page', None)
        contexto.update(
            {
                'filtros': self.request.GET,
                'querystring': parametros.urlencode(),
                'especies': todos.order_by('especie').values_list('especie', flat=True).distinct(),
                'portes': todos.order_by('porte').values_list('porte', flat=True).distinct(),
                'status_disponiveis': todos.order_by('status').values_list('status', flat=True).distinct(),
            }
        )
        return contexto


class DetalheAnimalView(ConsultaPortalMixin, DetailView):
    model = Animal
    template_name = 'animais/detalhe.html'
    context_object_name = 'animal'
    pk_url_kwarg = 'id_animal'
    permission_required = (
        'animais.view_animal',
        'saude.view_vacinacao',
        'saude.view_condicaosaude',
    )

    def get_queryset(self):
        return Animal.objects.prefetch_related(
            'fotos',
            'vacinacoes__vacina',
            'condicoes_saude',
        )

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        cliente_consultando = self.request.user.perfil == Usuario.Perfil.CLIENTE
        contexto['cliente_consultando'] = cliente_consultando
        contexto['solicitacao_ativa'] = None
        if cliente_consultando:
            contexto['solicitacao_ativa'] = self.object.solicitacoes_adocao.filter(
                cliente=self.request.user,
                status__in=('PENDENTE', 'EM_AVALIACAO', 'APROVADA'),
            ).first()
        contexto['animal_disponivel'] = (
            self.object.status.casefold() == 'disponível'.casefold()
        )
        return contexto


class VacinacoesAnimalView(ConsultaPortalMixin, DetailView):
    model = Animal
    template_name = 'animais/vacinacoes.html'
    context_object_name = 'animal'
    pk_url_kwarg = 'id_animal'
    permission_required = ('animais.view_animal', 'saude.view_vacinacao')

    def get_queryset(self):
        return Animal.objects.prefetch_related('vacinacoes__vacina')


class SaudeAnimalView(ConsultaPortalMixin, DetailView):
    model = Animal
    template_name = 'animais/saude.html'
    context_object_name = 'animal'
    pk_url_kwarg = 'id_animal'
    permission_required = ('animais.view_animal', 'saude.view_condicaosaude')

    def get_queryset(self):
        return Animal.objects.prefetch_related('condicoes_saude')
