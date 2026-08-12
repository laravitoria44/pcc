from django.db import migrations


def sincronizar_animais_adotados(apps, schema_editor):
    Animal = apps.get_model('animais', 'Animal')
    SolicitacaoAdocao = apps.get_model('adocao', 'SolicitacaoAdocao')

    ids_animais_aprovados = SolicitacaoAdocao.objects.filter(
        status='APROVADA',
    ).values_list('animal_id', flat=True)
    Animal.objects.filter(pk__in=ids_animais_aprovados).update(status='Adotado')


class Migration(migrations.Migration):

    dependencies = [
        ('adocao', '0003_delete_contato'),
        ('animais', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            sincronizar_animais_adotados,
            migrations.RunPython.noop,
        ),
    ]
