from django.contrib import admin

from setup.admin_utils import BotaoModificarAdminMixin

from .models import Animal, FotoAnimal


class FotoAnimalInline(admin.TabularInline):
    model = FotoAnimal
    extra = 0
    fields = ('descricao', 'url_foto', 'arquivo_imagem')


@admin.register(Animal)
class AnimalAdmin(BotaoModificarAdminMixin, admin.ModelAdmin):
    list_display = (
        'id_animal',
        'nome',
        'especie',
        'raca',
        'sexo',
        'porte',
        'status',
        'botao_detalhes',
        'botao_modificar',
        'botao_excluir',
    )
    list_filter = ('especie', 'sexo', 'porte', 'castracao', 'status')
    search_fields = ('nome', 'especie', 'raca', 'cor_pelagem')
    inlines = (FotoAnimalInline,)
    actions = ('marcar_como_inativo', 'marcar_como_disponivel')

    @admin.action(description='Marcar animais selecionados como inativos')
    def marcar_como_inativo(self, request, queryset):
        queryset.update(status='Inativo')

    @admin.action(description='Marcar animais selecionados como disponíveis')
    def marcar_como_disponivel(self, request, queryset):
        queryset.update(status='Disponível')


@admin.register(FotoAnimal)
class FotoAnimalAdmin(BotaoModificarAdminMixin, admin.ModelAdmin):
    list_display = (
        'id_foto',
        'animal',
        'descricao',
        'botao_detalhes',
        'botao_modificar',
        'botao_excluir',
    )
    search_fields = ('animal__nome', 'descricao')
    autocomplete_fields = ('animal',)
    list_select_related = ('animal',)
    fields = ('animal', 'descricao', 'url_foto', 'arquivo_imagem')
