from django.db import models


class Contato(models.Model):
    id_contato = models.AutoField(primary_key=True)
    remetente = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        related_name='mensagens_contato',
        blank=True,
        null=True,
    )
    nome = models.CharField(max_length=150)
    email = models.EmailField()
    telefone = models.CharField(max_length=20, blank=True)
    assunto = models.CharField(max_length=150, blank=True)
    mensagem = models.TextField()
    data_envio = models.DateTimeField(auto_now_add=True)
    lida = models.BooleanField(default=False)
    data_leitura = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'contato'
        verbose_name = 'mensagem de contato'
        verbose_name_plural = 'mensagens de contato'
        ordering = ('lida', '-data_envio')

    def __str__(self):
        return self.assunto or f'Mensagem de {self.nome}'


class SolicitacaoAdocao(models.Model):

    class Status(models.TextChoices):
        PENDENTE = 'PENDENTE', 'Pendente'
        EM_AVALIACAO = 'EM_AVALIACAO', 'Em avaliação'
        APROVADA = 'APROVADA', 'Aprovada'
        REJEITADA = 'REJEITADA', 'Rejeitada'
        CANCELADA = 'CANCELADA', 'Cancelada'

    id_solicitacao = models.AutoField(primary_key=True)

    # Chave estrangeira para o usuário que está solicitando a adoção
    cliente = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.PROTECT,
        related_name='solicitacoes_adocao',
        db_column='id_cliente',
        limit_choices_to={'perfil': 'CLIENTE'},
    )

    # Chave estrangeira para o animal que está sendo solicitado para adoção
    animal = models.ForeignKey(
        'animais.Animal',
        on_delete=models.PROTECT,
        related_name='solicitacoes_adocao',
        db_column='id_animal',
    )


    data_solicitacao = models.DateTimeField(auto_now_add=True)
    data_avaliacao = models.DateTimeField(blank=True, null=True)
    motivo_rejeicao = models.TextField(blank=True)
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.PENDENTE,
    )

    administrador_avaliador = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        related_name='solicitacoes_avaliadas',
        db_column='id_adm_avaliador',
        blank=True,
        null=True,
        limit_choices_to={'perfil': 'ADMINISTRADOR'},
    )

    class Meta:
        db_table = 'solicitacao_adocao'
        verbose_name = 'solicitação de adoção'
        verbose_name_plural = 'solicitações de adoção'
        ordering = ('-data_solicitacao',)

    def __str__(self):
        return f'Solicitação #{self.id_solicitacao} - {self.animal}'
