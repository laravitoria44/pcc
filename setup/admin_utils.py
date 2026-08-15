from django.contrib import admin
from django.contrib.admin.utils import display_for_field, unquote
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html


class BotaoModificarAdminMixin:
    """Adiciona atalhos explícitos para detalhar, alterar e excluir o objeto."""

    @admin.display(description='Detalhes')
    def botao_detalhes(self, obj):
        url = reverse(
            f'admin:{obj._meta.app_label}_{obj._meta.model_name}_details',
            args=(obj.pk,),
        )
        return format_html(
            '<a class="admin-row-action admin-row-details" href="{}">Detalhes</a>',
            url,
        )

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

    def get_urls(self):
        urls = super().get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name
        urls_detalhes = [
            path(
                '<path:object_id>/detalhes/',
                self.admin_site.admin_view(self.detalhes_view),
                name='%s_%s_details' % info,
            ),
        ]
        return urls_detalhes + urls

    def detalhes_view(self, request, object_id):
        obj = self.get_object(request, unquote(object_id))
        if obj is None:
            raise Http404('Registro não encontrado.')
        if not self.has_view_or_change_permission(request, obj):
            raise PermissionDenied

        campos = []
        for campo in self.model._meta.fields:
            if campo.name == 'password':
                continue
            valor = getattr(obj, campo.name)
            campos.append(
                {
                    'nome': campo.name,
                    'rotulo': campo.verbose_name,
                    'valor': display_for_field(
                        valor,
                        campo,
                        self.get_empty_value_display(),
                    ),
                }
            )

        for campo in self.model._meta.many_to_many:
            if campo.name == 'user_permissions':
                continue
            valores = ', '.join(str(valor) for valor in getattr(obj, campo.name).all())
            campos.append(
                {
                    'nome': campo.name,
                    'rotulo': campo.verbose_name,
                    'valor': valores or self.get_empty_value_display(),
                }
            )

        opts = self.model._meta
        contexto = {
            **self.admin_site.each_context(request),
            'title': f'Detalhes de {obj}',
            'opts': opts,
            'original': obj,
            'registro': obj,
            'campos': campos,
            'url_lista': reverse(f'admin:{opts.app_label}_{opts.model_name}_changelist'),
            'url_modificar': reverse(
                f'admin:{opts.app_label}_{opts.model_name}_change',
                args=(obj.pk,),
            ),
            'url_excluir': reverse(
                f'admin:{opts.app_label}_{opts.model_name}_delete',
                args=(obj.pk,),
            ),
            'pode_modificar': self.has_change_permission(request, obj),
            'pode_excluir': self.has_delete_permission(request, obj),
        }
        request.current_app = self.admin_site.name
        return TemplateResponse(request, 'admin/detalhes_registro.html', contexto)
