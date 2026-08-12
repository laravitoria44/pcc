from django.db import models


class CondicaoSaude(models.Model):
    id_condicao = models.AutoField(primary_key=True)
    animal = models.ForeignKey(
        'animais.Animal',
        on_delete=models.CASCADE,
        related_name='condicoes_saude',
        db_column='id_animal',
    )
    administrador = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.PROTECT,
        related_name='condicoes_saude_registradas',
        db_column='id_adm',
        limit_choices_to={'perfil': 'ADMINISTRADOR'},
    )
    tipo_condicao = models.CharField(max_length=100)
    descricao = models.TextField()
    data_diagnostico = models.DateField()
    gravidade = models.CharField(max_length=50)
    status = models.CharField(max_length=50)

    class Meta:
        db_table = 'condicao_saude'
        verbose_name = 'condição de saúde'
        verbose_name_plural = 'condições de saúde'
        ordering = ('-data_diagnostico',)

    def __str__(self):
        return f'{self.tipo_condicao} - {self.animal}'


class Vacina(models.Model):
    id_vacina = models.AutoField(primary_key=True)
    nome_vacina = models.CharField(max_length=100)
    especie_alvo = models.CharField(max_length=100)
    descricao = models.TextField()

    class Meta:
        db_table = 'vacina'
        verbose_name = 'vacina'
        verbose_name_plural = 'vacinas'
        ordering = ('nome_vacina',)

    def __str__(self):
        return self.nome_vacina


class Vacinacao(models.Model):
    id_vacinacao = models.AutoField(primary_key=True)
    animal = models.ForeignKey(
        'animais.Animal',
        on_delete=models.CASCADE,
        related_name='vacinacoes',
        db_column='id_animal',
    )
    vacina = models.ForeignKey(
        Vacina,
        on_delete=models.PROTECT,
        related_name='aplicacoes',
        db_column='id_vacina',
    )
    administrador = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.PROTECT,
        related_name='vacinacoes_registradas',
        db_column='id_adm',
        limit_choices_to={'perfil': 'ADMINISTRADOR'},
    )
    data_aplicacao = models.DateField()
    data_proxima_dose = models.DateField()
    dose = models.CharField(max_length=50)
    fabricante = models.CharField(max_length=100)

    class Meta:
        db_table = 'vacinacao'
        verbose_name = 'vacinação'
        verbose_name_plural = 'vacinações'
        ordering = ('-data_aplicacao',)

    def __str__(self):
        return f'{self.vacina} - {self.animal} ({self.data_aplicacao:%d/%m/%Y})'
