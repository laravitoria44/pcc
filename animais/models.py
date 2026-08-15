from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


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
    url_foto = models.URLField(
        'URL da imagem',
        max_length=500,
        blank=True,
        help_text='Informe uma URL ou envie um arquivo abaixo.',
    )
    arquivo_imagem = models.ImageField(
        'Upload da imagem',
        upload_to='animais/',
        blank=True,
        help_text='Quando preenchido, o arquivo enviado tem prioridade sobre a URL.',
    )

    class Meta:
        db_table = 'foto_animal'
        verbose_name = 'foto do animal'
        verbose_name_plural = 'fotos dos animais'
        ordering = ('id_foto',)
        constraints = (
            models.CheckConstraint(
                condition=~Q(url_foto='') | ~Q(arquivo_imagem=''),
                name='foto_animal_url_ou_upload',
            ),
        )

    def __str__(self):
        return f'Foto de {self.animal}'

    def clean(self):
        super().clean()
        if not self.url_foto and not self.arquivo_imagem:
            raise ValidationError(
                'Informe a URL da imagem ou selecione um arquivo para upload.'
            )

    @property
    def imagem_url(self):
        if self.arquivo_imagem:
            return self.arquivo_imagem.url
        return self.url_foto
