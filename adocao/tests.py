from datetime import date

from django.test import TestCase
from django.urls import reverse

from animais.models import Animal, FotoAnimal
from usuarios.models import Usuario

from .models import Contato, SolicitacaoAdocao


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
        urls = ('home', 'sobre', 'vacinacao', 'contato', 'dashboard')

        for nome_url in urls:
            with self.subTest(nome_url=nome_url):
                resposta = self.client.get(reverse(nome_url))
                self.assertEqual(resposta.status_code, 200)
                self.assertContains(resposta, 'design-system.css')
                self.assertContains(resposta, 'class="site-header"')
                self.assertContains(resposta, 'class="site-footer"')

    def test_dashboard_esta_disponivel_no_menu_e_no_rodape_sem_login(self):
        resposta = self.client.get(reverse('dashboard'))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Dashboard de Impacto')
        self.assertContains(resposta, reverse('dashboard'), count=2)
        self.assertContains(resposta, 'Dashboard de impacto')


class HomeCarrosselTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.luna = Animal.objects.create(
            nome='Luna Carrossel',
            especie='Cachorro',
            raca='SRD',
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
        cls.mia = Animal.objects.create(
            nome='Mia Carrossel',
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
        cls.foto_luna = FotoAnimal.objects.create(
            animal=cls.luna,
            descricao='Luna no carrossel',
            url_foto='https://cdn.example.com/luna-carrossel.jpg',
        )
        FotoAnimal.objects.create(
            animal=cls.mia,
            descricao='Mia no carrossel',
            url_foto='https://cdn.example.com/mia-carrossel.jpg',
        )

    def test_index_exibe_carrossel_com_animais_e_fotos_do_banco(self):
        resposta = self.client.get(reverse('home'))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'data-hero-carousel')
        self.assertContains(resposta, 'Luna Carrossel')
        self.assertContains(resposta, 'Mia Carrossel')
        self.assertContains(resposta, self.foto_luna.url_foto)
        self.assertContains(
            resposta,
            reverse('animais:detalhe', args=(self.luna.pk,)),
        )
        self.assertContains(resposta, 'data-carousel-next')
        self.assertNotContains(resposta, 'Pet-Hero-Image.png')

    def test_alterar_foto_no_banco_atualiza_carrossel(self):
        url_antiga = self.foto_luna.url_foto
        nova_url = 'https://cdn.example.com/luna-nova-home.jpg'
        self.foto_luna.url_foto = nova_url
        self.foto_luna.save(update_fields=('url_foto',))

        resposta = self.client.get(reverse('home'))

        self.assertContains(resposta, nova_url)
        self.assertNotContains(resposta, url_antiga)

    def test_index_sem_animais_exibe_estado_vazio(self):
        Animal.objects.all().delete()

        resposta = self.client.get(reverse('home'))

        self.assertContains(resposta, 'Novos amigos chegarão em breve')
        self.assertNotContains(resposta, 'data-hero-carousel')


class ContatoTests(TestCase):
    dados_validos = {
        'nome': 'Mariana Souza',
        'email': 'mariana@example.com',
        'telefone': '71999998888',
        'assunto': 'Dúvida sobre adoção',
        'mensagem': 'Gostaria de saber quais documentos são necessários.',
    }

    def test_visitante_envia_mensagem_e_dados_sao_salvos(self):
        resposta = self.client.post(reverse('contato'), self.dados_validos)

        self.assertRedirects(
            resposta,
            reverse('contato'),
            fetch_redirect_response=False,
        )
        contato = Contato.objects.get()
        self.assertEqual(contato.nome, 'Mariana Souza')
        self.assertEqual(contato.email, 'mariana@example.com')
        self.assertEqual(contato.telefone, '71999998888')
        self.assertEqual(contato.assunto, 'Dúvida sobre adoção')
        self.assertFalse(contato.lida)
        self.assertIsNone(contato.remetente)

        resposta_confirmacao = self.client.get(reverse('contato'))
        self.assertContains(resposta_confirmacao, 'Mensagem enviada com sucesso')

    def test_formulario_invalido_exibe_erros_e_nao_salva(self):
        dados = {**self.dados_validos, 'email': 'email-invalido', 'mensagem': ''}

        resposta = self.client.post(reverse('contato'), dados)

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Informe um endereço de e-mail válido.')
        self.assertContains(resposta, 'Escreva uma mensagem.')
        self.assertFalse(Contato.objects.exists())

    def test_mensagem_de_usuario_logado_guarda_relacao_com_remetente(self):
        usuario = Usuario.objects.create_user(
            nome_completo='Cliente Contato',
            cpf='10120230344',
            email='cliente.contato@example.com',
            telefone='71988887777',
            password='senha-segura-123',
        )
        self.client.force_login(usuario)

        resposta_get = self.client.get(reverse('contato'))
        self.assertContains(resposta_get, usuario.nome_completo)
        self.assertContains(resposta_get, usuario.email)

        self.client.post(reverse('contato'), self.dados_validos)

        self.assertEqual(Contato.objects.get().remetente, usuario)


class AdminContatoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.administrador = Usuario.objects.create_user(
            nome_completo='Administrador Contato',
            cpf='91982873746',
            email='admin.contato@example.com',
            telefone='71977776666',
            password='senha-segura-123',
            perfil=Usuario.Perfil.ADMINISTRADOR,
        )
        cls.contato = Contato.objects.create(
            nome='Pessoa Interessada',
            email='pessoa@example.com',
            telefone='71966665555',
            assunto='Parceria com a instituição',
            mensagem='Quero conversar sobre uma parceria para adoções.',
        )

    def setUp(self):
        self.client.force_login(self.administrador)

    def test_caixa_de_entrada_exibe_mensagem_e_botao_de_leitura(self):
        resposta = self.client.get(reverse('admin:adocao_contato_changelist'))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Parceria com a instituição')
        self.assertContains(resposta, 'Pessoa Interessada')
        self.assertContains(resposta, 'Ler mensagem')

    def test_pagina_de_leitura_exibe_conteudo_e_marca_como_lida(self):
        resposta = self.client.get(
            reverse('admin:adocao_contato_ler', args=(self.contato.pk,))
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Parceria com a instituição')
        self.assertContains(resposta, 'pessoa@example.com')
        self.assertContains(resposta, 'Quero conversar sobre uma parceria')
        self.assertContains(resposta, 'Responder por e-mail')
        self.contato.refresh_from_db()
        self.assertTrue(self.contato.lida)
        self.assertIsNotNone(self.contato.data_leitura)


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
