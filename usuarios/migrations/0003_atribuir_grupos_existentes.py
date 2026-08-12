from django.db import migrations


def atribuir_grupos(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Usuario = apps.get_model('usuarios', 'Usuario')

    grupo_cliente, _ = Group.objects.get_or_create(name='Cliente')
    grupo_administrador, _ = Group.objects.get_or_create(name='Administrador')

    for usuario in Usuario.objects.all().iterator():
        if usuario.perfil == 'ADMINISTRADOR':
            usuario.groups.set([grupo_administrador])
            if not usuario.is_staff:
                Usuario.objects.filter(pk=usuario.pk).update(is_staff=True)
        else:
            usuario.groups.set([grupo_cliente])
            if usuario.is_staff and not usuario.is_superuser:
                Usuario.objects.filter(pk=usuario.pk).update(is_staff=False)


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0002_criar_grupos'),
    ]

    operations = [
        migrations.RunPython(atribuir_grupos, migrations.RunPython.noop),
    ]
