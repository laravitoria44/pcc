from datetime import date

from django.test import TestCase
from django.urls import reverse

from animais.models import Animal
from usuarios.models import Usuario

from .models import SolicitacaoAdocao


class SolicitacaoAdocaoModelTests(TestCase):
    def test_cliente_solicita_adocao_de_animal(self):
        cliente = Usuario.objects.create_user(
            nome_completo='João Santos',
            cpf='11122233344',
            email='joao@example.com',
            telefone='71977777777',
            password='uma-senha-segura',
            perfil=Usuario.Perfil.CLIENTE,
        )
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

        solicitacao = SolicitacaoAdocao.objects.create(cliente=cliente, animal=animal)

        self.assertEqual(solicitacao.status, SolicitacaoAdocao.Status.PENDENTE)
        self.assertEqual(cliente.solicitacoes_adocao.get(), solicitacao)
        self.assertEqual(animal.solicitacoes_adocao.get(), solicitacao)


class PortalSolicitacoesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cliente = Usuario.objects.create_user(
            nome_completo='João Santos',
            cpf='11122233344',
            email='joao@example.com',
            telefone='71977777777',
            password='uma-senha-segura',
        )
        cls.outro_cliente = Usuario.objects.create_user(
            nome_completo='Maria Santos',
            cpf='55566677788',
            email='maria@example.com',
            telefone='71966666666',
            password='uma-senha-segura',
        )
        cls.animal = cls.criar_animal('Luna', 'Disponível')
        cls.animal_indisponivel = cls.criar_animal('Mel', 'Adotada')

    @staticmethod
    def criar_animal(nome, status):
        return Animal.objects.create(
            nome=nome,
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
            status=status,
        )

    def setUp(self):
        self.client.force_login(self.cliente)

    def test_cliente_cria_e_visualiza_solicitacao(self):
        resposta = self.client.post(
            reverse('adocoes:criar', args=(self.animal.pk,)),
            {'aceita_termo': 'on'},
        )

        solicitacao = SolicitacaoAdocao.objects.get(
            cliente=self.cliente,
            animal=self.animal,
        )
        self.assertRedirects(
            resposta,
            reverse('adocoes:detalhe', args=(solicitacao.pk,)),
        )
        self.assertEqual(solicitacao.status, SolicitacaoAdocao.Status.PENDENTE)

        resposta_lista = self.client.get(reverse('adocoes:minhas'))
        self.assertContains(resposta_lista, self.animal.nome)

    def test_cliente_ve_somente_as_proprias_solicitacoes(self):
        solicitacao_alheia = SolicitacaoAdocao.objects.create(
            cliente=self.outro_cliente,
            animal=self.animal,
        )

        resposta_lista = self.client.get(reverse('adocoes:minhas'))
        resposta_detalhe = self.client.get(
            reverse('adocoes:detalhe', args=(solicitacao_alheia.pk,))
        )

        self.assertNotContains(resposta_lista, f'Solicitação #{solicitacao_alheia.pk}')
        self.assertEqual(resposta_detalhe.status_code, 404)

    def test_termo_e_obrigatorio(self):
        resposta = self.client.post(
            reverse('adocoes:criar', args=(self.animal.pk,)),
            {},
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Você precisa aceitar o termo')
        self.assertFalse(SolicitacaoAdocao.objects.exists())

    def test_nao_permite_solicitacao_duplicada_ou_animal_indisponivel(self):
        SolicitacaoAdocao.objects.create(cliente=self.cliente, animal=self.animal)

        resposta_duplicada = self.client.post(
            reverse('adocoes:criar', args=(self.animal.pk,)),
            {'aceita_termo': 'on'},
        )
        resposta_indisponivel = self.client.post(
            reverse('adocoes:criar', args=(self.animal_indisponivel.pk,)),
            {'aceita_termo': 'on'},
        )

        self.assertContains(resposta_duplicada, 'solicitação ativa')
        self.assertContains(resposta_indisponivel, 'não está disponível')
        self.assertEqual(SolicitacaoAdocao.objects.count(), 1)


class PaginasPublicasDesignTests(TestCase):
    def test_paginas_publicas_usam_o_mesmo_design_system(self):
        urls = ('home', 'sobre', 'vacinacao', 'contato')

        for nome_url in urls:
            with self.subTest(nome_url=nome_url):
                resposta = self.client.get(reverse(nome_url))
                self.assertEqual(resposta.status_code, 200)
                self.assertContains(resposta, 'design-system.css')
                self.assertContains(resposta, 'class="site-header"')
                self.assertContains(resposta, 'class="site-footer"')


class AdminSolicitacaoActionsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cliente = Usuario.objects.create_user(
            nome_completo='Cliente Avaliação',
            cpf='22233344455',
            email='cliente.avaliacao@example.com',
            telefone='71955555555',
            password='uma-senha-segura',
        )
        cls.administrador = Usuario.objects.create_user(
            nome_completo='Administrador Avaliação',
            cpf='55544433322',
            email='admin.avaliacao@example.com',
            telefone='71944444444',
            password='uma-senha-segura',
            perfil=Usuario.Perfil.ADMINISTRADOR,
        )
        cls.animal = Animal.objects.create(
            nome='Nina',
            especie='Cachorro',
            raca='Sem raça definida',
            data_de_nascimento=date(2023, 2, 4),
            sexo='Fêmea',
            porte='Médio',
            cor_pelagem='Marrom',
            peso=11.0,
            castracao=True,
            descricao_temperamento='Dócil',
            data_entrada=date(2025, 4, 1),
            status='Disponível',
        )
        cls.solicitacao = SolicitacaoAdocao.objects.create(
            cliente=cls.cliente,
            animal=cls.animal,
        )

    def setUp(self):
        self.client.force_login(self.administrador)

    def test_lista_exibe_botoes_visiveis_de_aprovar_e_rejeitar(self):
        resposta = self.client.get(
            reverse('admin:adocao_solicitacaoadocao_changelist')
        )

        self.assertContains(resposta, 'Aprovar')
        self.assertContains(resposta, 'Rejeitar')
        self.assertContains(resposta, 'Aprovar selecionadas')
        self.assertContains(resposta, 'Rejeitar selecionadas')
        self.assertContains(
            resposta,
            reverse(
                'admin:adocao_solicitacaoadocao_aprovar',
                args=(self.solicitacao.pk,),
            ),
        )

    def test_administrador_aprova_solicitacao_com_confirmacao(self):
        url = reverse(
            'admin:adocao_solicitacaoadocao_aprovar',
            args=(self.solicitacao.pk,),
        )
        confirmacao = self.client.get(url)
        resposta = self.client.post(url)

        self.solicitacao.refresh_from_db()
        self.assertContains(confirmacao, 'Confirmar aprovação')
        self.assertRedirects(
            resposta,
            reverse('admin:adocao_solicitacaoadocao_changelist'),
        )
        self.assertEqual(
            self.solicitacao.status,
            SolicitacaoAdocao.Status.APROVADA,
        )
        self.assertEqual(
            self.solicitacao.administrador_avaliador,
            self.administrador,
        )
        self.assertIsNotNone(self.solicitacao.data_avaliacao)
        self.animal.refresh_from_db()
        self.assertEqual(self.animal.status, 'Adotado')

    def test_rejeicao_exige_e_registra_motivo(self):
        url = reverse(
            'admin:adocao_solicitacaoadocao_rejeitar',
            args=(self.solicitacao.pk,),
        )

        resposta_invalida = self.client.post(url, {'motivo_rejeicao': ''})
        self.solicitacao.refresh_from_db()
        self.assertContains(resposta_invalida, 'Informe o motivo da rejeição')
        self.assertEqual(self.solicitacao.status, SolicitacaoAdocao.Status.PENDENTE)

        resposta = self.client.post(
            url,
            {'motivo_rejeicao': 'Ambiente sem proteção adequada.'},
        )
        self.solicitacao.refresh_from_db()
        self.assertRedirects(
            resposta,
            reverse('admin:adocao_solicitacaoadocao_changelist'),
        )
        self.assertEqual(
            self.solicitacao.status,
            SolicitacaoAdocao.Status.REJEITADA,
        )
        self.assertEqual(
            self.solicitacao.motivo_rejeicao,
            'Ambiente sem proteção adequada.',
        )

    def test_rejeitar_aprovacao_libera_animal_novamente(self):
        self.client.post(
            reverse(
                'admin:adocao_solicitacaoadocao_aprovar',
                args=(self.solicitacao.pk,),
            )
        )

        resposta = self.client.post(
            reverse(
                'admin:adocao_solicitacaoadocao_rejeitar',
                args=(self.solicitacao.pk,),
            ),
            {'motivo_rejeicao': 'A aprovação precisou ser revertida.'},
        )

        self.solicitacao.refresh_from_db()
        self.animal.refresh_from_db()
        self.assertRedirects(
            resposta,
            reverse('admin:adocao_solicitacaoadocao_changelist'),
        )
        self.assertEqual(
            self.solicitacao.status,
            SolicitacaoAdocao.Status.REJEITADA,
        )
        self.assertEqual(self.animal.status, 'Disponível')

    def test_nao_aprova_solicitacao_cancelada(self):
        self.solicitacao.status = SolicitacaoAdocao.Status.CANCELADA
        self.solicitacao.save(update_fields=('status',))

        resposta = self.client.post(
            reverse(
                'admin:adocao_solicitacaoadocao_aprovar',
                args=(self.solicitacao.pk,),
            )
        )

        self.solicitacao.refresh_from_db()
        self.animal.refresh_from_db()
        self.assertRedirects(
            resposta,
            reverse('admin:adocao_solicitacaoadocao_changelist'),
        )
        self.assertEqual(
            self.solicitacao.status,
            SolicitacaoAdocao.Status.CANCELADA,
        )
        self.assertEqual(self.animal.status, 'Disponível')

    def test_nao_aprova_solicitacao_de_animal_indisponivel(self):
        self.animal.status = 'Em tratamento'
        self.animal.save(update_fields=('status',))

        resposta = self.client.post(
            reverse(
                'admin:adocao_solicitacaoadocao_aprovar',
                args=(self.solicitacao.pk,),
            )
        )

        self.solicitacao.refresh_from_db()
        self.animal.refresh_from_db()
        self.assertRedirects(
            resposta,
            reverse('admin:adocao_solicitacaoadocao_changelist'),
        )
        self.assertEqual(
            self.solicitacao.status,
            SolicitacaoAdocao.Status.PENDENTE,
        )
        self.assertEqual(self.animal.status, 'Em tratamento')

    def test_status_nao_pode_ser_alterado_pelo_formulario_comum(self):
        resposta = self.client.get(
            reverse(
                'admin:adocao_solicitacaoadocao_change',
                args=(self.solicitacao.pk,),
            )
        )

        self.assertContains(resposta, 'field-status')
        self.assertNotContains(resposta, 'name="status"')

    def test_lista_exibe_botoes_modificar_e_excluir(self):
        resposta = self.client.get(
            reverse('admin:adocao_solicitacaoadocao_changelist')
        )

        self.assertContains(resposta, 'Modificar')
        self.assertContains(resposta, 'Excluir')
        self.assertContains(
            resposta,
            reverse(
                'admin:adocao_solicitacaoadocao_change',
                args=(self.solicitacao.pk,),
            ),
        )
        self.assertContains(
            resposta,
            reverse(
                'admin:adocao_solicitacaoadocao_delete',
                args=(self.solicitacao.pk,),
            ),
        )

    def test_excluir_solicitacao_aprovada_libera_animal(self):
        self.client.post(
            reverse(
                'admin:adocao_solicitacaoadocao_aprovar',
                args=(self.solicitacao.pk,),
            )
        )

        resposta = self.client.post(
            reverse(
                'admin:adocao_solicitacaoadocao_delete',
                args=(self.solicitacao.pk,),
            ),
            {'post': 'yes'},
        )

        self.animal.refresh_from_db()
        self.assertRedirects(
            resposta,
            reverse('admin:adocao_solicitacaoadocao_changelist'),
        )
        self.assertFalse(
            SolicitacaoAdocao.objects.filter(pk=self.solicitacao.pk).exists()
        )
        self.assertEqual(self.animal.status, 'Disponível')

    def test_aprova_solicitacao_marcada_pela_barra_de_selecao(self):
        resposta = self.client.post(
            reverse('admin:adocao_solicitacaoadocao_changelist'),
            {
                'action': 'aprovar_solicitacoes',
                'index': '0',
                '_selected_action': [str(self.solicitacao.pk)],
            },
        )

        self.solicitacao.refresh_from_db()
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(
            self.solicitacao.status,
            SolicitacaoAdocao.Status.APROVADA,
        )
        self.animal.refresh_from_db()
        self.assertEqual(self.animal.status, 'Adotado')

    def test_aprovacao_rejeita_outras_solicitacoes_do_mesmo_animal(self):
        outra_solicitacao = SolicitacaoAdocao.objects.create(
            cliente=Usuario.objects.create_user(
                nome_completo='Outro Cliente',
                cpf='88877766655',
                email='outro.cliente@example.com',
                telefone='71933333333',
                password='uma-senha-segura',
            ),
            animal=self.animal,
        )

        self.client.post(
            reverse(
                'admin:adocao_solicitacaoadocao_aprovar',
                args=(self.solicitacao.pk,),
            )
        )

        outra_solicitacao.refresh_from_db()
        self.assertEqual(
            outra_solicitacao.status,
            SolicitacaoAdocao.Status.REJEITADA,
        )
        self.assertIn('Outra solicitação', outra_solicitacao.motivo_rejeicao)

    def test_rejeita_solicitacao_marcada_apos_informar_motivo(self):
        url = reverse('admin:adocao_solicitacaoadocao_changelist')
        confirmacao = self.client.post(
            url,
            {
                'action': 'rejeitar_solicitacoes',
                'index': '0',
                '_selected_action': [str(self.solicitacao.pk)],
            },
        )
        self.assertContains(confirmacao, 'O mesmo motivo será registrado')

        resposta = self.client.post(
            url,
            {
                'action': 'rejeitar_solicitacoes',
                'confirmar_rejeicao': '1',
                'select_across': '0',
                '_selected_action': [str(self.solicitacao.pk)],
                'motivo_rejeicao': 'Requisitos da adoção não atendidos.',
            },
        )

        self.solicitacao.refresh_from_db()
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(
            self.solicitacao.status,
            SolicitacaoAdocao.Status.REJEITADA,
        )
        self.assertEqual(
            self.solicitacao.motivo_rejeicao,
            'Requisitos da adoção não atendidos.',
        )
