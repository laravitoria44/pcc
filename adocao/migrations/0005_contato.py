import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('adocao', '0004_sincronizar_animais_adotados'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Contato',
            fields=[
                ('id_contato', models.AutoField(primary_key=True, serialize=False)),
                ('nome', models.CharField(max_length=150)),
                ('email', models.EmailField(max_length=254)),
                ('telefone', models.CharField(blank=True, max_length=20)),
                ('assunto', models.CharField(blank=True, max_length=150)),
                ('mensagem', models.TextField()),
                ('data_envio', models.DateTimeField(auto_now_add=True)),
                ('lida', models.BooleanField(default=False)),
                ('data_leitura', models.DateTimeField(blank=True, null=True)),
                (
                    'remetente',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='mensagens_contato',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'verbose_name': 'mensagem de contato',
                'verbose_name_plural': 'mensagens de contato',
                'db_table': 'contato',
                'ordering': ('lida', '-data_envio'),
            },
        ),
    ]
