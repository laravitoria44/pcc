from django.contrib.admin import AdminSite
from django.urls import reverse


class PetAdoteAdminSite(AdminSite):
    site_header = 'Administração PetAdote'
    site_title = 'PetAdote Admin'
    index_title = 'Gestão e monitoramento'
    index_template = 'admin/petadote_index.html'

    def index(self, request, extra_context=None):
        from adocao.models import SolicitacaoAdocao
        from animais.models import Animal
        from saude.models import CondicaoSaude, Vacinacao
        from usuarios.models import Usuario

        indicadores = (
            {
                'titulo': 'Animais',
                'valor': Animal.objects.count(),
                'url': reverse('admin:animais_animal_changelist'),
            },
            {
                'titulo': 'Solicitações pendentes',
                'valor': SolicitacaoAdocao.objects.filter(
                    status=SolicitacaoAdocao.Status.PENDENTE,
                ).count(),
                'url': reverse('admin:adocao_solicitacaoadocao_changelist'),
            },
            {
                'titulo': 'Vacinações',
                'valor': Vacinacao.objects.count(),
                'url': reverse('admin:saude_vacinacao_changelist'),
            },
            {
                'titulo': 'Condições de saúde',
                'valor': CondicaoSaude.objects.count(),
                'url': reverse('admin:saude_condicaosaude_changelist'),
            },
            {
                'titulo': 'Usuários ativos',
                'valor': Usuario.objects.filter(is_active=True).count(),
                'url': reverse('admin:usuarios_usuario_changelist'),
            },
        )

        atalhos = (
            {
                'titulo': 'Animais',
                'descricao': 'Cadastre e atualize os animais disponíveis.',
                'links': (
                    {'rotulo': 'Ver catálogo no site', 'url': reverse('animais:lista')},
                    {'rotulo': 'Gerenciar', 'url': reverse('admin:animais_animal_changelist')},
                    {'rotulo': 'Cadastrar', 'url': reverse('admin:animais_animal_add')},
                ),
            },
            {
                'titulo': 'Solicitações',
                'descricao': 'Aprove ou rejeite pedidos de adoção.',
                'links': (
                    {
                        'rotulo': 'Avaliar solicitações',
                        'url': reverse('admin:adocao_solicitacaoadocao_changelist'),
                    },
                ),
            },
            {
                'titulo': 'Saúde e vacinação',
                'descricao': 'Registre condições e aplicações de vacinas.',
                'links': (
                    {'rotulo': 'Nova vacinação', 'url': reverse('admin:saude_vacinacao_add')},
                    {'rotulo': 'Nova condição', 'url': reverse('admin:saude_condicaosaude_add')},
                ),
            },
            {
                'titulo': 'Usuários',
                'descricao': 'Gerencie clientes e administradores.',
                'links': (
                    {'rotulo': 'Gerenciar', 'url': reverse('admin:usuarios_usuario_changelist')},
                    {'rotulo': 'Cadastrar', 'url': reverse('admin:usuarios_usuario_add')},
                ),
            },
        )

        contexto = {'indicadores': indicadores, 'atalhos': atalhos}
        contexto.update(extra_context or {})
        return super().index(request, extra_context=contexto)
