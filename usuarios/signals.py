from django.contrib.auth.models import Group
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver

from .group_permissions import (
    GRUPO_ADMINISTRADOR,
    GRUPO_CLIENTE,
    sincronizar_grupos_e_permissoes,
)
from .models import Usuario


@receiver(post_migrate)
def criar_grupos_e_permissoes(**kwargs):
    sincronizar_grupos_e_permissoes()


@receiver(post_save, sender=Usuario)
def atribuir_grupo_do_perfil(sender, instance, **kwargs):
    if instance.perfil == Usuario.Perfil.ADMINISTRADOR:
        nome_grupo = GRUPO_ADMINISTRADOR
        deve_ser_staff = True
    else:
        nome_grupo = GRUPO_CLIENTE
        deve_ser_staff = False

    grupo, _ = Group.objects.get_or_create(name=nome_grupo)
    instance.groups.set([grupo])

    if not instance.is_superuser and instance.is_staff != deve_ser_staff:
        sender.objects.filter(pk=instance.pk).update(is_staff=deve_ser_staff)
