from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('usuarios', '0004_usuario_vinculo_if_baiano'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='arquivo_foto_perfil',
            field=models.ImageField(
                blank=True,
                upload_to='usuarios/perfis/',
                verbose_name='Foto de perfil',
            ),
        ),
    ]
