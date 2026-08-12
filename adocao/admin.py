from django.contrib import admin
from django.contrib import messages
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html, format_html_join

from animais.models import Animal
from setup.admin_utils import BotaoModificarAdminMixin

from .forms import RejeitarSolicitacaoAdminForm
from .models import SolicitacaoAdocao
from .services import (
    STATUS_ANIMAL_DISPONIVEL,
    SolicitacaoNaoPodeSerAprovada,
    SolicitacaoNaoPodeSerRejeitada,
    aprovar_solicitacao,
    rejeitar_solicitacao,
)


@admin.register(SolicitacaoAdocao)
class SolicitacaoAdocaoAdmin(BotaoModificarAdminMixin, admin.ModelAdmin):
    list_display = (
        'id_solicitacao',
        'cliente',
        'animal',
        'data_solicitacao',
        'status',
        'administrador_avaliador',
        'acoes_visiveis',
        'botao_modificar',
        'botao_excluir',
    )
    list_filter = ('status', 'data_solicitacao', 'data_avaliacao')
    search_fields = (
        'cliente__nome_completo',
        'cliente__cpf',
        'animal__nome',
        'motivo_rejeicao',
    )
    autocomplete_fields = ('cliente', 'animal', 'administrador_avaliador')
    readonly_fields = (
        'status',
        'administrador_avaliador',
        'data_avaliacao',
        'motivo_rejeicao',
    )
    date_hierarchy = 'data_solicitacao'
    actions = ('aprovar_solicitacoes', 'rejeitar_solicitacoes')

    @staticmethod
    def _liberar_animais_sem_aprovacao(ids_animais):
        for id_animal in ids_animais:
            possui_aprovacao = SolicitacaoAdocao.objects.filter(
                animal_id=id_animal,
                status=SolicitacaoAdocao.Status.APROVADA,
            ).exists()
            if not possui_aprovacao:
                Animal.objects.filter(pk=id_animal).update(
                    status=STATUS_ANIMAL_DISPONIVEL
                )

    @transaction.atomic
    def delete_model(self, request, obj):
        ids_animais = (
            {obj.animal_id}
            if obj.status == SolicitacaoAdocao.Status.APROVADA
            else set()
        )
        super().delete_model(request, obj)
        self._liberar_animais_sem_aprovacao(ids_animais)

    @transaction.atomic
    def delete_queryset(self, request, queryset):
        ids_animais = set(
            queryset.filter(status=SolicitacaoAdocao.Status.APROVADA).values_list(
                'animal_id',
                flat=True,
            )
        )
        super().delete_queryset(request, queryset)
        self._liberar_animais_sem_aprovacao(ids_animais)

    @admin.action(description='Aprovar solicitações selecionadas')
    def aprovar_solicitacoes(self, request, queryset):
        aprovadas = 0
        concorrentes_encerradas = 0
        erros = []
        for solicitacao in queryset.select_related('animal'):
            try:
                _, encerradas = aprovar_solicitacao(solicitacao, request.user)
                aprovadas += 1
                concorrentes_encerradas += encerradas
                self.log_change(
                    request,
                    solicitacao,
                    'Solicitação aprovada; animal marcado como adotado.',
                )
            except SolicitacaoNaoPodeSerAprovada as erro:
                erros.extend(erro.messages)

        self.message_user(
            request,
            f'{aprovadas} solicitação(ões) aprovada(s). '
            f'{concorrentes_encerradas} solicitação(ões) concorrente(s) encerrada(s).',
        )
        for erro in erros:
            self.message_user(request, erro, level=messages.WARNING)

    @admin.action(description='Rejeitar solicitações selecionadas')
    def rejeitar_solicitacoes(self, request, queryset):
        form = RejeitarSolicitacaoAdminForm(request.POST or None)
        confirmando = request.POST.get('confirmar_rejeicao') == '1'

        if confirmando and form.is_valid():
            solicitacoes = list(queryset)
            motivo = form.cleaned_data['motivo_rejeicao']
            quantidade = 0
            animais_liberados = 0
            erros = []
            for solicitacao in solicitacoes:
                try:
                    solicitacao, animal_liberado = rejeitar_solicitacao(
                        solicitacao,
                        request.user,
                        motivo,
                    )
                    quantidade += 1
                    animais_liberados += int(animal_liberado)
                    self.log_change(
                        request,
                        solicitacao,
                        'Solicitação rejeitada por ação em lote.',
                    )
                except SolicitacaoNaoPodeSerRejeitada as erro:
                    erros.extend(erro.messages)
            self.message_user(
                request,
                f'{quantidade} solicitação(ões) rejeitada(s) com sucesso. '
                f'{animais_liberados} animal(is) voltou(aram) a ficar disponível(is).',
            )
            for erro in erros:
                self.message_user(request, erro, level=messages.WARNING)
            return None

        if not confirmando:
            form = RejeitarSolicitacaoAdminForm()

        contexto = {
            **self.admin_site.each_context(request),
            'title': 'Rejeitar solicitações selecionadas',
            'opts': self.model._meta,
            'solicitacoes': queryset,
            'form': form,
            'action_checkbox_name': ACTION_CHECKBOX_NAME,
            'select_across': request.POST.get('select_across', '0'),
        }
        request.current_app = self.admin_site.name
        return TemplateResponse(
            request,
            'admin/adocao/confirmar_rejeicao_lote.html',
            contexto,
        )

    @admin.display(description='Ações')
    def acoes_visiveis(self, solicitacao):
        botoes = []
        pode_aprovar = (
            solicitacao.status
            in (
                SolicitacaoAdocao.Status.PENDENTE,
                SolicitacaoAdocao.Status.EM_AVALIACAO,
            )
            and solicitacao.animal.status.casefold()
            == STATUS_ANIMAL_DISPONIVEL.casefold()
        )
        if pode_aprovar:
            botoes.append(
                format_html(
                    '<a class="admin-row-action admin-row-approve" href="{}">Aprovar</a>',
                    reverse(
                        'admin:adocao_solicitacaoadocao_aprovar',
                        args=(solicitacao.pk,),
                    ),
                )
            )
        if solicitacao.status in (
            SolicitacaoAdocao.Status.PENDENTE,
            SolicitacaoAdocao.Status.EM_AVALIACAO,
            SolicitacaoAdocao.Status.APROVADA,
        ):
            botoes.append(
                format_html(
                    '<a class="admin-row-action admin-row-reject" href="{}">Rejeitar</a>',
                    reverse(
                        'admin:adocao_solicitacaoadocao_rejeitar',
                        args=(solicitacao.pk,),
                    ),
                )
            )
        return format_html(
            '<div class="admin-row-actions">{}</div>',
            format_html_join('', '{}', ((botao,) for botao in botoes)),
        )

    def get_urls(self):
        urls = super().get_urls()
        urls_personalizadas = [
            path(
                '<path:object_id>/aprovar/',
                self.admin_site.admin_view(self.aprovar_view),
                name='adocao_solicitacaoadocao_aprovar',
            ),
            path(
                '<path:object_id>/rejeitar/',
                self.admin_site.admin_view(self.rejeitar_view),
                name='adocao_solicitacaoadocao_rejeitar',
            ),
        ]
        return urls_personalizadas + urls

    def aprovar_view(self, request, object_id):
        return self._alterar_status_view(
            request,
            object_id,
            novo_status=SolicitacaoAdocao.Status.APROVADA,
        )

    def rejeitar_view(self, request, object_id):
        return self._alterar_status_view(
            request,
            object_id,
            novo_status=SolicitacaoAdocao.Status.REJEITADA,
        )

    def _alterar_status_view(self, request, object_id, novo_status):
        solicitacao = self.get_object(request, object_id)
        if solicitacao is None:
            raise Http404('Solicitação não encontrada.')
        if not self.has_change_permission(request, solicitacao):
            raise PermissionDenied

        rejeitando = novo_status == SolicitacaoAdocao.Status.REJEITADA
        form = None
        if rejeitando:
            form = RejeitarSolicitacaoAdminForm(
                request.POST or None,
                initial={'motivo_rejeicao': solicitacao.motivo_rejeicao},
            )

        formulario_valido = not rejeitando or form.is_valid()
        if request.method == 'POST' and formulario_valido:
            status_anterior = solicitacao.get_status_display()
            if rejeitando:
                try:
                    solicitacao, animal_liberado = rejeitar_solicitacao(
                        solicitacao,
                        request.user,
                        form.cleaned_data['motivo_rejeicao'],
                    )
                except SolicitacaoNaoPodeSerRejeitada as erro:
                    for mensagem in erro.messages:
                        self.message_user(request, mensagem, level=messages.ERROR)
                    return HttpResponseRedirect(
                        reverse('admin:adocao_solicitacaoadocao_changelist')
                    )
                if animal_liberado:
                    self.message_user(
                        request,
                        f'{solicitacao.animal.nome} voltou a ficar disponível para adoção.',
                    )
            else:
                try:
                    solicitacao, encerradas = aprovar_solicitacao(
                        solicitacao,
                        request.user,
                    )
                except SolicitacaoNaoPodeSerAprovada as erro:
                    for mensagem in erro.messages:
                        self.message_user(request, mensagem, level=messages.ERROR)
                    return HttpResponseRedirect(
                        reverse('admin:adocao_solicitacaoadocao_changelist')
                    )
                if encerradas:
                    self.message_user(
                        request,
                        f'{encerradas} outra(s) solicitação(ões) para o mesmo animal '
                        'foram rejeitadas automaticamente.',
                    )
            self.log_change(
                request,
                solicitacao,
                f'Status alterado de {status_anterior} para '
                f'{solicitacao.get_status_display()}.',
            )
            self.message_user(
                request,
                f'Solicitação #{solicitacao.pk} marcada como '
                f'{solicitacao.get_status_display().lower()}.',
            )
            return HttpResponseRedirect(
                reverse('admin:adocao_solicitacaoadocao_changelist')
            )

        contexto = {
            **self.admin_site.each_context(request),
            'title': f'{"Rejeitar" if rejeitando else "Aprovar"} solicitação',
            'opts': self.model._meta,
            'original': solicitacao,
            'solicitacao': solicitacao,
            'form': form,
            'rejeitando': rejeitando,
            'botao': 'Confirmar rejeição' if rejeitando else 'Confirmar aprovação',
        }
        request.current_app = self.admin_site.name
        return TemplateResponse(
            request,
            'admin/adocao/confirmar_status.html',
            contexto,
        )
