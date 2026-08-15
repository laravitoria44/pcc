import re
import tempfile
from datetime import date

from django.contrib import admin
from django.contrib.auth.models import Group
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from adocao.models import SolicitacaoAdocao
from animais.models import Animal, FotoAnimal
from saude.models import CondicaoSaude, Vacina, Vacinacao

from .group_permissions import GRUPO_ADMINISTRADOR, GRUPO_CLIENTE
from .models import Usuario


class UsuarioModelTests(TestCase):
    def test_senha_pode_ser_armazenada_com_hash(self):
        usuario = Usuario(
            nome_completo='Maria da Silva',
            cpf='12345678901',
            email='maria@example.com',
            telefone='71999999999',
            perfil=Usuario.Perfil.CLIENTE,
        )
        usuario.definir_senha('uma-senha-segura')
        usuario.save()

        self.assertNotEqual(usuario.senha, 'uma-senha-segura')
        self.assertTrue(usuario.verificar_senha('uma-senha-segura'))

    def test_manager_cria_superusuario_administrador(self):
        usuario = Usuario.objects.create_superuser(
            email='admin@example.com',
            password='uma-senha-segura',
            nome_completo='Admin PetAdote',
            cpf='98765432100',
            telefone='71988888888',
        )

        self.assertEqual(usuario.perfil, Usuario.Perfil.ADMINISTRADOR)
        self.assertTrue(usuario.is_staff)
        self.assertTrue(usuario.is_superuser)


class AutenticacaoTests(TestCase):
    dados_cadastro = {
        'nome_completo': 'Maria da Silva',
        'cpf': '123.456.789-01',
        'email': 'Maria@Example.com',
        'telefone': '71999999999',
        'password1': 'uma-senha-segura-123',
        'password2': 'uma-senha-segura-123',
    }

    def test_paginas_de_login_e_cadastro_renderizam(self):
        resposta_login = self.client.get(reverse('usuarios:login'))
        resposta_cadastro = self.client.get(reverse('usuarios:cadastro'))

        self.assertEqual(resposta_login.status_code, 200)
        self.assertContains(resposta_login, 'Bem-vindo de volta')
        self.assertEqual(resposta_cadastro.status_code, 200)
        self.assertContains(resposta_cadastro, 'Crie sua conta')
        self.assertContains(resposta_cadastro, 'Foto de perfil (opcional)')
        self.assertContains(resposta_cadastro, 'enctype="multipart/form-data"')
        self.assertContains(resposta_cadastro, 'Sou do IF Baiano Campus Guanambi')
        self.assertContains(resposta_cadastro, 'id="matricula-institucional-field"')
        self.assertContains(resposta_cadastro, 'conditional-field is-hidden')

    def test_cadastro_cria_cliente_com_senha_hasheada_e_inicia_sessao(self):
        resposta = self.client.post(reverse('usuarios:cadastro'), self.dados_cadastro)

        usuario = Usuario.objects.get(email='maria@example.com')
        self.assertRedirects(resposta, reverse('home'))
        self.assertEqual(usuario.cpf, '12345678901')
        self.assertEqual(usuario.perfil, Usuario.Perfil.CLIENTE)
        self.assertFalse(usuario.vinculo_if_baiano)
        self.assertEqual(usuario.matricula_institucional, '')
        self.assertTrue(usuario.groups.filter(name=GRUPO_CLIENTE).exists())
        self.assertTrue(usuario.check_password('uma-senha-segura-123'))
        self.assertEqual(int(self.client.session['_auth_user_id']), usuario.pk)

        resposta_home = self.client.get(reverse('home'))
        self.assertContains(resposta_home, 'Olá, Maria')
        self.assertContains(resposta_home, reverse('usuarios:perfil'))

    def test_cadastro_permite_upload_opcional_de_foto_de_perfil(self):
        imagem_gif = (
            b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
        )
        with tempfile.TemporaryDirectory() as media_root, self.settings(
            MEDIA_ROOT=media_root
        ):
            dados = {
                **self.dados_cadastro,
                'arquivo_foto_perfil': SimpleUploadedFile(
                    'perfil.gif',
                    imagem_gif,
                    content_type='image/gif',
                ),
            }

            resposta = self.client.post(reverse('usuarios:cadastro'), dados)

            self.assertRedirects(resposta, reverse('home'))
            usuario = Usuario.objects.get(email='maria@example.com')
            self.assertTrue(usuario.arquivo_foto_perfil)
            self.assertIn('usuarios/perfis/', usuario.arquivo_foto_perfil.name)

            resposta_home = self.client.get(reverse('home'))
            resposta_perfil = self.client.get(reverse('usuarios:perfil'))
            self.assertContains(resposta_home, usuario.foto_perfil_url)
            self.assertContains(resposta_perfil, usuario.foto_perfil_url)

    def test_cadastro_salva_vinculo_e_matricula_do_if_baiano(self):
        dados = {
            **self.dados_cadastro,
            'vinculo_if_baiano': 'on',
            'matricula_institucional': '2026123456',
        }

        resposta = self.client.post(reverse('usuarios:cadastro'), dados)

        self.assertRedirects(resposta, reverse('home'))
        usuario = Usuario.objects.get(email='maria@example.com')
        self.assertTrue(usuario.vinculo_if_baiano)
        self.assertEqual(usuario.matricula_institucional, '2026123456')

    def test_matricula_e_obrigatoria_quando_usuario_marca_vinculo(self):
        dados = {**self.dados_cadastro, 'vinculo_if_baiano': 'on'}

        resposta = self.client.post(reverse('usuarios:cadastro'), dados)

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Informe a matrícula institucional do IF Baiano.')
        self.assertContains(resposta, 'conditional-field')
        self.assertNotContains(resposta, 'conditional-field is-hidden')
        self.assertFalse(Usuario.objects.filter(email='maria@example.com').exists())

    def test_matricula_nao_e_salva_sem_vinculo_marcado(self):
        dados = {
            **self.dados_cadastro,
            'matricula_institucional': 'VALOR-INDEVIDO',
        }

        resposta = self.client.post(reverse('usuarios:cadastro'), dados)

        self.assertRedirects(resposta, reverse('home'))
        usuario = Usuario.objects.get(email='maria@example.com')
        self.assertFalse(usuario.vinculo_if_baiano)
        self.assertEqual(usuario.matricula_institucional, '')

    def test_login_aceita_email_e_senha(self):
        usuario = Usuario.objects.create_user(
            email='cliente@example.com',
            password='uma-senha-segura-123',
            nome_completo='Cliente PetAdote',
            cpf='11122233344',
            telefone='71977777777',
        )

        resposta = self.client.post(
            reverse('usuarios:login'),
            {'username': usuario.email, 'password': 'uma-senha-segura-123'},
        )

        self.assertRedirects(resposta, reverse('home'))
        self.assertEqual(int(self.client.session['_auth_user_id']), usuario.pk)

        resposta_home = self.client.get(reverse('home'))
        self.assertContains(resposta_home, 'Olá, Cliente')

    def test_perfil_exige_autenticacao(self):
        resposta = self.client.get(reverse('usuarios:perfil'))

        self.assertRedirects(
            resposta,
            f"{reverse('usuarios:login')}?next={reverse('usuarios:perfil')}",
        )

    def test_logout_por_post_encerra_sessao(self):
        usuario = Usuario.objects.create_user(
            email='cliente@example.com',
            password='uma-senha-segura-123',
            nome_completo='Cliente PetAdote',
            cpf='11122233344',
            telefone='71977777777',
        )
        self.client.force_login(usuario)

        resposta = self.client.post(reverse('usuarios:logout'))

        self.assertRedirects(resposta, reverse('home'))
        self.assertNotIn('_auth_user_id', self.client.session)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class RecuperacaoSenhaTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email='recuperacao@example.com',
            password='senha-antiga-segura-123',
            nome_completo='Cliente Recuperação',
            cpf='44455566677',
            telefone='71977776666',
        )

    def test_tela_de_login_exibe_link_de_recuperacao(self):
        resposta = self.client.get(reverse('usuarios:login'))

        self.assertContains(resposta, 'Esqueci minha senha')
        self.assertContains(resposta, reverse('usuarios:password_reset'))

    def test_fluxo_completo_redefine_senha_e_permite_login(self):
        resposta_envio = self.client.post(
            reverse('usuarios:password_reset'),
            {'email': self.usuario.email},
        )

        self.assertRedirects(
            resposta_envio,
            reverse('usuarios:password_reset_done'),
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.usuario.email])

        correspondencia = re.search(
            r'http://testserver(?P<caminho>/usuarios/redefinir-senha/[^\s]+)',
            mail.outbox[0].body,
        )
        self.assertIsNotNone(correspondencia)

        resposta_token = self.client.get(
            correspondencia.group('caminho'),
            follow=True,
        )
        self.assertEqual(resposta_token.status_code, 200)
        self.assertContains(resposta_token, 'Crie uma nova senha')

        caminho_confirmacao = resposta_token.request['PATH_INFO']
        nova_senha = 'nova-senha-super-segura-456'
        resposta_confirmacao = self.client.post(
            caminho_confirmacao,
            {
                'new_password1': nova_senha,
                'new_password2': nova_senha,
            },
        )

        self.assertRedirects(
            resposta_confirmacao,
            reverse('usuarios:password_reset_complete'),
        )
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password(nova_senha))
        self.assertFalse(self.usuario.check_password('senha-antiga-segura-123'))

        resposta_login = self.client.post(
            reverse('usuarios:login'),
            {'username': self.usuario.email, 'password': nova_senha},
        )
        self.assertRedirects(resposta_login, reverse('home'))

    def test_email_desconhecido_nao_revela_existencia_da_conta(self):
        resposta = self.client.post(
            reverse('usuarios:password_reset'),
            {'email': 'nao-existe@example.com'},
        )

        self.assertRedirects(resposta, reverse('usuarios:password_reset_done'))
        self.assertEqual(mail.outbox, [])


class GruposEAdministracaoTests(TestCase):
    def criar_usuario(self, email, cpf, perfil=Usuario.Perfil.CLIENTE):
        return Usuario.objects.create_user(
            email=email,
            password='uma-senha-segura-123',
            nome_completo='Usuário de Teste',
            cpf=cpf,
            telefone='71999999999',
            perfil=perfil,
        )

    def test_grupos_sao_criados_com_as_permissoes_do_diagrama(self):
        cliente = self.criar_usuario('cliente@example.com', '11122233344')
        administrador = self.criar_usuario(
            'admin@example.com',
            '99988877766',
            Usuario.Perfil.ADMINISTRADOR,
        )
        administrador.refresh_from_db()

        self.assertTrue(Group.objects.filter(name=GRUPO_CLIENTE).exists())
        self.assertTrue(Group.objects.filter(name=GRUPO_ADMINISTRADOR).exists())
        self.assertTrue(cliente.groups.filter(name=GRUPO_CLIENTE).exists())
        self.assertTrue(cliente.has_perm('animais.view_animal'))
        self.assertTrue(cliente.has_perm('adocao.add_solicitacaoadocao'))
        self.assertFalse(cliente.has_perm('animais.add_animal'))

        self.assertTrue(administrador.groups.filter(name=GRUPO_ADMINISTRADOR).exists())
        self.assertTrue(administrador.is_staff)
        self.assertTrue(administrador.has_perm('animais.add_animal'))
        self.assertTrue(administrador.has_perm('saude.change_vacinacao'))
        self.assertTrue(administrador.has_perm('adocao.change_solicitacaoadocao'))
        self.assertTrue(administrador.has_perm('adocao.view_contato'))
        self.assertTrue(administrador.has_perm('adocao.change_contato'))
        self.assertTrue(administrador.has_perm('adocao.delete_contato'))
        self.assertTrue(administrador.has_perm('usuarios.add_usuario'))
        self.assertTrue(administrador.has_perm('usuarios.delete_usuario'))

    def test_cliente_nao_acessa_administracao(self):
        cliente = self.criar_usuario('cliente@example.com', '11122233344')
        self.client.force_login(cliente)

        resposta_home = self.client.get(reverse('home'))
        resposta_admin = self.client.get(reverse('admin:index'))

        self.assertNotContains(resposta_home, reverse('admin:index'))
        self.assertEqual(resposta_admin.status_code, 302)

    def test_administrador_visualiza_area_de_cruds(self):
        administrador = self.criar_usuario(
            'admin@example.com',
            '99988877766',
            Usuario.Perfil.ADMINISTRADOR,
        )
        self.client.force_login(administrador)

        resposta_home = self.client.get(reverse('home'))
        resposta_admin = self.client.get(reverse('admin:index'))

        self.assertContains(resposta_home, reverse('admin:index'))
        self.assertEqual(resposta_admin.status_code, 200)
        self.assertContains(resposta_admin, 'Gerenciamento do sistema')
        self.assertContains(resposta_admin, 'petadote_admin.css')
        self.assertContains(resposta_admin, 'pet<strong>adote</strong>')
        self.assertNotContains(resposta_admin, 'Dashboard de Impacto')

        crud_urls = (
            'admin:animais_animal_changelist',
            'admin:animais_fotoanimal_changelist',
            'admin:saude_vacina_changelist',
            'admin:saude_vacinacao_changelist',
            'admin:saude_condicaosaude_changelist',
            'admin:adocao_solicitacaoadocao_changelist',
            'admin:adocao_contato_changelist',
            'admin:usuarios_usuario_changelist',
        )
        for nome_url in crud_urls:
            with self.subTest(nome_url=nome_url):
                self.assertEqual(self.client.get(reverse(nome_url)).status_code, 200)

    def test_dashboard_publico_calcula_indicadores_e_graficos_com_dados_reais(self):
        administrador = self.criar_usuario(
            'admin.dashboard@example.com',
            '77788899900',
            Usuario.Perfil.ADMINISTRADOR,
        )
        cliente = self.criar_usuario('cliente.dashboard@example.com', '11133355577')
        animal_disponivel = Animal.objects.create(
            nome='Bidu',
            especie='Cachorro',
            raca='SRD',
            data_de_nascimento=date(2022, 5, 10),
            sexo='Macho',
            porte='Médio',
            cor_pelagem='Caramelo',
            peso=14.2,
            castracao=True,
            descricao_temperamento='Dócil',
            data_entrada=date(2025, 1, 20),
            status='Disponível',
        )
        animal_adotado = Animal.objects.create(
            nome='Mimi',
            especie='Gato',
            raca='SRD',
            data_de_nascimento=date(2021, 4, 8),
            sexo='Fêmea',
            porte='Pequeno',
            cor_pelagem='Cinza',
            peso=4.1,
            castracao=True,
            descricao_temperamento='Tranquila',
            data_entrada=date(2025, 2, 10),
            status='Adotado',
        )
        SolicitacaoAdocao.objects.create(
            cliente=cliente,
            animal=animal_disponivel,
            status=SolicitacaoAdocao.Status.PENDENTE,
        )
        SolicitacaoAdocao.objects.create(
            cliente=cliente,
            animal=animal_adotado,
            status=SolicitacaoAdocao.Status.APROVADA,
            administrador_avaliador=administrador,
            data_avaliacao=timezone.now(),
        )
        resposta = self.client.get(reverse('dashboard'))
        indicadores = {
            indicador['titulo']: indicador['valor']
            for indicador in resposta.context['indicadores']
        }

        self.assertEqual(indicadores['Total de adoções'], 1)
        self.assertEqual(indicadores['Total de animais'], 2)
        self.assertEqual(indicadores['Taxa de aprovação'], '100%')
        self.assertEqual(indicadores['Animais disponíveis'], 1)
        self.assertEqual(resposta.context['adocoes_mes'], 1)
        self.assertEqual(resposta.context['meses_adocoes'][-1]['valor'], 1)
        self.assertContains(resposta, 'Dashboard de Impacto')
        self.assertContains(resposta, 'Adoções nos últimos 6 meses')
        self.assertContains(resposta, 'Animais por espécie')
        self.assertContains(resposta, 'Situação dos animais')

    def test_todas_as_classes_exibem_atalho_para_modificar(self):
        models_administrados = (
            Usuario,
            Animal,
            FotoAnimal,
            Vacina,
            Vacinacao,
            CondicaoSaude,
            SolicitacaoAdocao,
        )

        for model in models_administrados:
            with self.subTest(model=model.__name__):
                model_admin = admin.site._registry[model]
                self.assertIn('botao_detalhes', model_admin.list_display)
                self.assertIn('botao_modificar', model_admin.list_display)
                self.assertIn('botao_excluir', model_admin.list_display)

    def test_administrador_visualiza_detalhes_completos_sem_expor_senha(self):
        administrador = self.criar_usuario(
            'admin.detalhes@example.com',
            '88877766655',
            Usuario.Perfil.ADMINISTRADOR,
        )
        administrador.telefone = '71912345678'
        administrador.vinculo_if_baiano = True
        administrador.matricula_institucional = '2026123456'
        administrador.save()
        self.client.force_login(administrador)

        resposta = self.client.get(
            reverse('admin:usuarios_usuario_details', args=(administrador.pk,))
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Visualização completa dos dados deste registro.')
        self.assertContains(resposta, '71912345678')
        self.assertContains(resposta, '2026123456')
        self.assertContains(resposta, 'Modificar registro')
        nomes_campos = {campo['nome'] for campo in resposta.context['campos']}
        self.assertIn('telefone', nomes_campos)
        self.assertIn('matricula_institucional', nomes_campos)
        self.assertNotIn('password', nomes_campos)

    def test_administrador_consegue_cadastrar_animal_pelo_crud(self):
        administrador = self.criar_usuario(
            'admin@example.com',
            '99988877766',
            Usuario.Perfil.ADMINISTRADOR,
        )
        self.client.force_login(administrador)

        resposta = self.client.post(
            reverse('admin:animais_animal_add'),
            {
                'nome': 'Bidu',
                'especie': 'Cachorro',
                'raca': 'Sem raça definida',
                'data_de_nascimento': date(2022, 5, 10),
                'sexo': 'Macho',
                'porte': 'Médio',
                'cor_pelagem': 'Caramelo',
                'peso': 14.2,
                'castracao': 'on',
                'descricao_temperamento': 'Dócil',
                'data_entrada': date(2025, 1, 20),
                'status': 'Disponível',
                '_save': 'Salvar',
                'fotos-TOTAL_FORMS': '0',
                'fotos-INITIAL_FORMS': '0',
                'fotos-MIN_NUM_FORMS': '0',
                'fotos-MAX_NUM_FORMS': '1000',
            },
        )

        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(Animal.objects.filter(nome='Bidu').exists())
