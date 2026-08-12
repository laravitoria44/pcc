from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html


class BotaoModificarAdminMixin:
    """Adiciona atalhos explícitos para alterar e excluir o objeto."""

    @admin.display(description='Modificar')
    def botao_modificar(self, obj):
        url = reverse(
            f'admin:{obj._meta.app_label}_{obj._meta.model_name}_change',
            args=(obj.pk,),
        )
        return format_html(
            '<a class="admin-row-action admin-row-change" href="{}">Modificar</a>',
            url,
        )

    @admin.display(description='Excluir')
    def botao_excluir(self, obj):
        url = reverse(
            f'admin:{obj._meta.app_label}_{obj._meta.model_name}_delete',
            args=(obj.pk,),
        )
        return format_html(
            '<a class="admin-row-action admin-row-delete" href="{}">Excluir</a>',
            url,
        )
