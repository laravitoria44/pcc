from django.db import models


class Animal(models.Model):
    id_animal = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    especie = models.CharField(max_length=50)
    raca = models.CharField(max_length=100)
    data_de_nascimento = models.DateField()
    sexo = models.CharField(max_length=20)
    porte = models.CharField(max_length=20)
    cor_pelagem = models.CharField(max_length=100)
    peso = models.FloatField()
    castracao = models.BooleanField()
    descricao_temperamento = models.TextField()
    data_entrada = models.DateField()
    status = models.CharField(max_length=50)

    class Meta:
        db_table = 'animal'
        verbose_name = 'animal'
        verbose_name_plural = 'animais'
        ordering = ('nome',)

    def __str__(self):
        return self.nome


class FotoAnimal(models.Model):
    id_foto = models.AutoField(primary_key=True)
    animal = models.ForeignKey(
        Animal,
        on_delete=models.CASCADE,
        related_name='fotos',
        db_column='id_animal',
    )
    descricao = models.TextField()
    url_foto = models.URLField(max_length=500)

    class Meta:
        db_table = 'foto_animal'
        verbose_name = 'foto do animal'
        verbose_name_plural = 'fotos dos animais'

    def __str__(self):
        return f'Foto de {self.animal}'
