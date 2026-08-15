from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from setup.admin_utils import BotaoModificarAdminMixin

from .forms import UsuarioAdminChangeForm, UsuarioAdminCreationForm
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(BotaoModificarAdminMixin, UserAdmin):
    form = UsuarioAdminChangeForm
    add_form = UsuarioAdminCreationForm
    model = Usuario
    list_display = (
        'id_usuario',
        'nome_completo',
        'cpf',
        'email',
        'perfil',
        'vinculo_if_baiano',
        'grupo_principal',
        'is_active',
        'botao_detalhes',
        'botao_modificar',
        'botao_excluir',
    )
    list_filter = ('perfil', 'vinculo_if_baiano', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('nome_completo', 'cpf', 'email', 'matricula_institucional')
    ordering = ('nome_completo',)
    readonly_fields = ('last_login', 'date_joined')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (
            'Dados pessoais',
            {
                'fields': (
                    'nome_completo',
                    'cpf',
                    'telefone',
                    'foto_perfil',
                    'arquivo_foto_perfil',
                    'vinculo_if_baiano',
                    'matricula_institucional',
                    'cargo_funcao',
                    'perfil',
                )
            },
        ),
        (
            'Permissões',
            {
                'fields': (
                    'is_active',
                    'is_staff',
                )
            },
        ),
        ('Datas importantes', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'email',
                    'nome_completo',
                    'cpf',
                    'telefone',
                    'arquivo_foto_perfil',
                    'vinculo_if_baiano',
                    'matricula_institucional',
                    'perfil',
                    'password1',
                    'password2',
                    'is_active',
                ),
            },
        ),
    )

    @admin.display(description='Grupo')
    def grupo_principal(self, usuario):
        grupo = usuario.groups.first()
        return grupo.name if grupo else 'Sem grupo'

    def get_queryset(self, request):
        queryset = super().get_queryset(request).prefetch_related('groups')
        if request.user.is_superuser:
            return queryset
        return queryset.filter(is_superuser=False)

    def has_change_permission(self, request, obj=None):
        if obj is not None and obj.is_superuser and not request.user.is_superuser:
            return False
        return super().has_change_permission(request, obj)
