from django.contrib import admin

from setup.admin_utils import BotaoModificarAdminMixin

from .models import CondicaoSaude, Vacina, Vacinacao


@admin.register(CondicaoSaude)
class CondicaoSaudeAdmin(BotaoModificarAdminMixin, admin.ModelAdmin):
    list_display = (
        'id_condicao',
        'animal',
        'tipo_condicao',
        'data_diagnostico',
        'gravidade',
        'status',
        'botao_detalhes',
        'botao_modificar',
        'botao_excluir',
    )
    list_filter = ('tipo_condicao', 'gravidade', 'status', 'data_diagnostico')
    search_fields = ('animal__nome', 'tipo_condicao', 'descricao')
    autocomplete_fields = ('animal', 'administrador')
    list_select_related = ('animal', 'administrador')


@admin.register(Vacina)
class VacinaAdmin(BotaoModificarAdminMixin, admin.ModelAdmin):
    list_display = (
        'id_vacina',
        'nome_vacina',
        'especie_alvo',
        'botao_detalhes',
        'botao_modificar',
        'botao_excluir',
    )
    list_filter = ('especie_alvo',)
    search_fields = ('nome_vacina', 'especie_alvo', 'descricao')


@admin.register(Vacinacao)
class VacinacaoAdmin(BotaoModificarAdminMixin, admin.ModelAdmin):
    list_display = (
        'id_vacinacao',
        'animal',
        'vacina',
        'data_aplicacao',
        'data_proxima_dose',
        'dose',
        'botao_detalhes',
        'botao_modificar',
        'botao_excluir',
    )
    list_filter = ('vacina', 'data_aplicacao', 'data_proxima_dose', 'fabricante')
    search_fields = ('animal__nome', 'vacina__nome_vacina', 'fabricante', 'dose')
    autocomplete_fields = ('animal', 'vacina', 'administrador')
    list_select_related = ('animal', 'vacina', 'administrador')
