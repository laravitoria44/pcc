from django.contrib.auth.models import Group, Permission


GRUPO_CLIENTE = 'Cliente'
GRUPO_ADMINISTRADOR = 'Administrador'

PERMISSOES_CLIENTE = {
    'animais': {
        'view_animal',
        'view_fotoanimal',
    },
    'saude': {
        'view_condicaosaude',
        'view_vacina',
        'view_vacinacao',
    },
    'adocao': {
        'add_solicitacaoadocao',
        'view_solicitacaoadocao',
    },
}

PERMISSOES_ADMINISTRADOR = {
    'animais': {
        'add_animal',
        'change_animal',
        'delete_animal',
        'view_animal',
        'add_fotoanimal',
        'change_fotoanimal',
        'delete_fotoanimal',
        'view_fotoanimal',
    },
    'saude': {
        'add_condicaosaude',
        'change_condicaosaude',
        'delete_condicaosaude',
        'view_condicaosaude',
        'add_vacina',
        'change_vacina',
        'delete_vacina',
        'view_vacina',
        'add_vacinacao',
        'change_vacinacao',
        'delete_vacinacao',
        'view_vacinacao',
    },
    'adocao': {
        'add_solicitacaoadocao',
        'change_solicitacaoadocao',
        'delete_solicitacaoadocao',
        'view_solicitacaoadocao',
        'change_contato',
        'delete_contato',
        'view_contato',
    },
    'usuarios': {
        'add_usuario',
        'change_usuario',
        'delete_usuario',
        'view_usuario',
    },
}


def _buscar_permissoes(matriz):
    consulta = Permission.objects.none()
    for app_label, codenames in matriz.items():
        consulta = consulta | Permission.objects.filter(
            content_type__app_label=app_label,
            codename__in=codenames,
        )
    return consulta


def sincronizar_grupos_e_permissoes():
    grupo_cliente, _ = Group.objects.get_or_create(name=GRUPO_CLIENTE)
    grupo_administrador, _ = Group.objects.get_or_create(name=GRUPO_ADMINISTRADOR)

    grupo_cliente.permissions.set(_buscar_permissoes(PERMISSOES_CLIENTE))
    grupo_administrador.permissions.set(_buscar_permissoes(PERMISSOES_ADMINISTRADOR))

    return grupo_cliente, grupo_administrador
