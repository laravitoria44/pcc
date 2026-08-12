from datetime import date

from django.test import TestCase

from animais.models import Animal
from usuarios.models import Usuario

from .models import CondicaoSaude, Vacina, Vacinacao


class SaudeModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.administrador = Usuario.objects.create_user(
            nome_completo='Ana Souza',
            cpf='98765432100',
            email='ana@example.com',
            telefone='71988888888',
            password='uma-senha-segura',
            perfil=Usuario.Perfil.ADMINISTRADOR,
        )
        cls.animal = Animal.objects.create(
            nome='Luna',
            especie='Cachorro',
            raca='Sem raça definida',
            data_de_nascimento=date(2023, 1, 10),
            sexo='Fêmea',
            porte='Médio',
            cor_pelagem='Caramelo',
            peso=12.5,
            castracao=True,
            descricao_temperamento='Dócil',
            data_entrada=date(2025, 2, 1),
            status='Disponível',
        )

    def test_animal_recebe_condicao_e_vacinacao(self):
        CondicaoSaude.objects.create(
            animal=self.animal,
            administrador=self.administrador,
            tipo_condicao='Alergia',
            descricao='Alergia alimentar',
            data_diagnostico=date(2025, 2, 2),
            gravidade='Leve',
            status='Em tratamento',
        )
        vacina = Vacina.objects.create(
            nome_vacina='V10',
            especie_alvo='Cachorro',
            descricao='Vacina polivalente',
        )
        Vacinacao.objects.create(
            animal=self.animal,
            vacina=vacina,
            administrador=self.administrador,
            data_aplicacao=date(2025, 2, 3),
            data_proxima_dose=date(2026, 2, 3),
            dose='1ª dose',
            fabricante='Fabricante exemplo',
        )

        self.assertEqual(self.animal.condicoes_saude.count(), 1)
        self.assertEqual(self.animal.vacinacoes.count(), 1)
