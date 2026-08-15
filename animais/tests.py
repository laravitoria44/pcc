import tempfile
from datetime import date

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from saude.models import CondicaoSaude, Vacina, Vacinacao
from usuarios.models import Usuario

from .models import Animal, FotoAnimal


class AnimalModelTests(TestCase):
    def test_animal_possui_fotos(self):
        animal = Animal.objects.create(
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
        FotoAnimal.objects.create(
            animal=animal,
            descricao='Foto de perfil',
            url_foto='https://example.com/luna.jpg',
        )

        self.assertEqual(animal.fotos.count(), 1)

    def test_foto_exige_url_ou_arquivo(self):
        animal = Animal.objects.create(
            nome='Sem Foto',
            especie='Gato',
            raca='SRD',
            data_de_nascimento=date(2024, 1, 1),
            sexo='Fêmea',
            porte='Pequeno',
            cor_pelagem='Preta',
            peso=3.5,
            castracao=False,
            descricao_temperamento='Curiosa',
            data_entrada=date(2026, 1, 1),
            status='Disponível',
        )
        foto = FotoAnimal(animal=animal, descricao='Sem origem de imagem')

        with self.assertRaises(ValidationError):
            foto.full_clean()


class PortalAnimaisTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cliente = Usuario.objects.create_user(
            nome_completo='Cliente Teste',
            cpf='12345678901',
            email='cliente@example.com',
            telefone='71999999999',
            password='uma-senha-segura',
        )
        cls.administrador = Usuario.objects.create_user(
            nome_completo='Administrador Teste',
            cpf='10987654321',
            email='admin@example.com',
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
        FotoAnimal.objects.create(
            animal=cls.animal,
            descricao='Foto de Luna',
            url_foto='https://example.com/luna.jpg',
        )
        vacina = Vacina.objects.create(
            nome_vacina='V10',
            especie_alvo='Cachorro',
            descricao='Vacina polivalente',
        )
        Vacinacao.objects.create(
            animal=cls.animal,
            vacina=vacina,
            administrador=cls.administrador,
            data_aplicacao=date(2025, 2, 2),
            data_proxima_dose=date(2026, 2, 2),
            dose='Reforço anual',
            fabricante='PetBio',
        )
        CondicaoSaude.objects.create(
            animal=cls.animal,
            administrador=cls.administrador,
            tipo_condicao='Dermatite',
            descricao='Irritação leve',
            data_diagnostico=date(2025, 2, 3),
            gravidade='Leve',
            status='Tratada',
        )
        cls.outro_animal = Animal.objects.create(
            nome='Mia',
            especie='Gato',
            raca='Siamês',
            data_de_nascimento=date(2022, 5, 8),
            sexo='Fêmea',
            porte='Pequeno',
            cor_pelagem='Creme',
            peso=4.1,
            castracao=True,
            descricao_temperamento='Tranquila',
            data_entrada=date(2025, 3, 1),
            status='Disponível',
        )

    def setUp(self):
        self.client.force_login(self.cliente)

    def test_cliente_consulta_catalogo_perfil_vacinacao_e_saude(self):
        respostas = (
            self.client.get(reverse('animais:lista')),
            self.client.get(reverse('animais:detalhe', args=(self.animal.pk,))),
            self.client.get(reverse('animais:vacinacoes', args=(self.animal.pk,))),
            self.client.get(reverse('animais:saude', args=(self.animal.pk,))),
        )

        for resposta in respostas:
            self.assertEqual(resposta.status_code, 200)
        self.assertContains(respostas[0], 'Luna')
        self.assertContains(respostas[1], 'V10')
        self.assertContains(respostas[1], 'Dermatite')
        self.assertContains(respostas[2], 'Reforço anual')
        self.assertContains(respostas[3], 'Irritação leve')

    def test_catalogo_permite_busca_e_filtros(self):
        resposta = self.client.get(
            reverse('animais:lista'),
            {'q': 'Luna', 'especie': 'Cachorro', 'porte': 'Médio'},
        )

        self.assertContains(resposta, 'Luna')
        self.assertNotContains(resposta, 'Mia')

    def test_alterar_url_no_banco_altera_imagem_no_catalogo_e_perfil(self):
        foto = self.animal.fotos.get()
        url_anterior = foto.url_foto
        nova_url = 'https://cdn.example.com/luna-atualizada.jpg'

        foto.url_foto = nova_url
        foto.save(update_fields=('url_foto',))

        resposta_catalogo = self.client.get(reverse('animais:lista'))
        resposta_perfil = self.client.get(
            reverse('animais:detalhe', args=(self.animal.pk,))
        )
        self.assertContains(resposta_catalogo, nova_url)
        self.assertContains(resposta_perfil, nova_url)
        self.assertNotContains(resposta_catalogo, url_anterior)
        self.assertNotContains(resposta_perfil, url_anterior)

    def test_upload_tem_prioridade_sobre_url_no_site(self):
        imagem_gif = (
            b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
        )
        with tempfile.TemporaryDirectory() as media_root, self.settings(
            MEDIA_ROOT=media_root
        ):
            foto = self.animal.fotos.get()
            foto.arquivo_imagem = SimpleUploadedFile(
                'luna-upload.gif',
                imagem_gif,
                content_type='image/gif',
            )
            foto.save(update_fields=('arquivo_imagem',))

            resposta = self.client.get(reverse('animais:lista'))

            self.assertContains(resposta, foto.arquivo_imagem.url)
            self.assertNotContains(resposta, foto.url_foto)

    def test_admin_oferece_url_e_upload_para_foto(self):
        self.client.force_login(self.administrador)
        foto = self.animal.fotos.get()

        resposta = self.client.get(
            reverse('admin:animais_fotoanimal_change', args=(foto.pk,))
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'URL da imagem')
        self.assertContains(resposta, 'Upload da imagem')
        self.assertContains(resposta, 'type="file"')

    def test_anônimo_e_redirecionado_e_administrador_pode_consultar(self):
        self.client.logout()
        resposta_anonima = self.client.get(reverse('animais:lista'))
        self.assertRedirects(
            resposta_anonima,
            f"{reverse('usuarios:login')}?next={reverse('animais:lista')}",
        )

        self.client.force_login(self.administrador)
        resposta_administrador = self.client.get(reverse('animais:lista'))
        resposta_perfil = self.client.get(
            reverse('animais:detalhe', args=(self.animal.pk,))
        )
        resposta_vacinacao = self.client.get(
            reverse('animais:vacinacoes', args=(self.animal.pk,))
        )
        resposta_saude = self.client.get(
            reverse('animais:saude', args=(self.animal.pk,))
        )

        self.assertEqual(resposta_administrador.status_code, 200)
        self.assertEqual(resposta_perfil.status_code, 200)
        self.assertEqual(resposta_vacinacao.status_code, 200)
        self.assertEqual(resposta_saude.status_code, 200)
        self.assertContains(resposta_perfil, 'consultando este perfil como administrador')
        self.assertNotContains(resposta_perfil, 'Solicitar adoção')
