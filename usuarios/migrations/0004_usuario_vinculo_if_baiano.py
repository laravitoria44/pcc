from django.db import migrations, models


def marcar_vinculos_existentes(apps, schema_editor):
    Usuario = apps.get_model('usuarios', 'Usuario')
    Usuario.objects.exclude(matricula_institucional='').update(vinculo_if_baiano=True)


class Migration(migrations.Migration):
    dependencies = [
        ('usuarios', '0003_atribuir_grupos_existentes'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='vinculo_if_baiano',
            field=models.BooleanField(
                default=False,
                verbose_name='é do IF Baiano Campus Guanambi',
            ),
        ),
        migrations.RunPython(
            marcar_vinculos_existentes,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
