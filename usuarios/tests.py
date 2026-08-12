from datetime import date

from django.contrib import admin
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

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

    def test_cadastro_cria_cliente_com_senha_hasheada_e_inicia_sessao(self):
        resposta = self.client.post(reverse('usuarios:cadastro'), self.dados_cadastro)

        usuario = Usuario.objects.get(email='maria@example.com')
        self.assertRedirects(resposta, reverse('home'))
        self.assertEqual(usuario.cpf, '12345678901')
        self.assertEqual(usuario.perfil, Usuario.Perfil.CLIENTE)
        self.assertTrue(usuario.groups.filter(name=GRUPO_CLIENTE).exists())
        self.assertTrue(usuario.check_password('uma-senha-segura-123'))
        self.assertEqual(int(self.client.session['_auth_user_id']), usuario.pk)

        resposta_home = self.client.get(reverse('home'))
        self.assertContains(resposta_home, 'Olá, Maria')
        self.assertContains(resposta_home, reverse('usuarios:perfil'))

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
        self.assertTrue(administrador.has_perm('usuarios.add_usuario'))
        self.assertTrue(administrador.has_perm('usuarios.delete_usuario'))

    def test_cliente_nao_acessa_administracao(self):
        cliente = self.criar_usuario('cliente@example.com', '11122233344')
        self.client.force_login(cliente)

        resposta_home = self.client.get(reverse('home'))
        resposta_admin = self.client.get(reverse('admin:index'))

        self.assertNotContains(resposta_home, reverse('admin:index'))
        self.assertEqual(resposta_admin.status_code, 302)

    def test_administrador_visualiza_dashboard_e_cruds(self):
        administrador = self.criar_usuario(
            'admin@example.com',
            '99988877766',
            Usuario.Perfil.ADMINISTRADOR,
        )
        self.client.force_login(administrador)

        resposta_home = self.client.get(reverse('home'))
        resposta_dashboard = self.client.get(reverse('admin:index'))

        self.assertContains(resposta_home, reverse('admin:index'))
        self.assertEqual(resposta_dashboard.status_code, 200)
        self.assertContains(resposta_dashboard, 'Gestão e monitoramento')
        self.assertContains(resposta_dashboard, 'Solicitações pendentes')
        self.assertContains(resposta_dashboard, 'petadote_admin.css')
        self.assertContains(resposta_dashboard, 'Pet<strong>Adote</strong>')
        self.assertContains(resposta_dashboard, 'Ações rápidas')
        self.assertContains(resposta_dashboard, 'Avaliar solicitações')
        self.assertContains(resposta_dashboard, 'Ver catálogo no site')

        crud_urls = (
            'admin:animais_animal_changelist',
            'admin:animais_fotoanimal_changelist',
            'admin:saude_vacina_changelist',
            'admin:saude_vacinacao_changelist',
            'admin:saude_condicaosaude_changelist',
            'admin:adocao_solicitacaoadocao_changelist',
            'admin:usuarios_usuario_changelist',
        )
        for nome_url in crud_urls:
            with self.subTest(nome_url=nome_url):
                self.assertEqual(self.client.get(reverse(nome_url)).status_code, 200)

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
                self.assertIn('botao_modificar', model_admin.list_display)
                self.assertIn('botao_excluir', model_admin.list_display)

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
