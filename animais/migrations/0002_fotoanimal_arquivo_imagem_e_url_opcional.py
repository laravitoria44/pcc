from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('animais', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='fotoanimal',
            options={
                'ordering': ('id_foto',),
                'verbose_name': 'foto do animal',
                'verbose_name_plural': 'fotos dos animais',
            },
        ),
        migrations.AlterField(
            model_name='fotoanimal',
            name='url_foto',
            field=models.URLField(
                blank=True,
                help_text='Informe uma URL ou envie um arquivo abaixo.',
                max_length=500,
                verbose_name='URL da imagem',
            ),
        ),
        migrations.AddField(
            model_name='fotoanimal',
            name='arquivo_imagem',
            field=models.ImageField(
                blank=True,
                help_text='Quando preenchido, o arquivo enviado tem prioridade sobre a URL.',
                upload_to='animais/',
                verbose_name='Upload da imagem',
            ),
        ),
        migrations.AddConstraint(
            model_name='fotoanimal',
            constraint=models.CheckConstraint(
                condition=models.Q(('url_foto', ''), _negated=True)
                | models.Q(('arquivo_imagem', ''), _negated=True),
                name='foto_animal_url_ou_upload',
            ),
        ),
    ]
