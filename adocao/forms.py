from django import forms

from .models import Contato, SolicitacaoAdocao


class ContatoForm(forms.ModelForm):
    class Meta:
        model = Contato
        fields = ('nome', 'email', 'telefone', 'assunto', 'mensagem')
        labels = {
            'nome': 'Nome completo',
            'email': 'E-mail',
            'telefone': 'Telefone',
            'assunto': 'Assunto',
            'mensagem': 'Mensagem',
        }
        widgets = {
            'nome': forms.TextInput(attrs={'autocomplete': 'name'}),
            'email': forms.EmailInput(
                attrs={'autocomplete': 'email', 'placeholder': 'contato@exemplo.com'}
            ),
            'telefone': forms.TextInput(
                attrs={'autocomplete': 'tel', 'placeholder': '(00) 00000-0000'}
            ),
            'assunto': forms.TextInput(
                attrs={'placeholder': 'Ex: Dúvida sobre adoção de filhote'}
            ),
            'mensagem': forms.Textarea(attrs={'rows': 6}),
        }
        error_messages = {
            'nome': {'required': 'Informe seu nome.'},
            'email': {
                'required': 'Informe seu e-mail.',
                'invalid': 'Informe um endereço de e-mail válido.',
            },
            'mensagem': {'required': 'Escreva uma mensagem.'},
        }


class SolicitacaoAdocaoForm(forms.Form):
    aceita_termo = forms.BooleanField(
        label='Li e aceito o termo de compromisso de adoção responsável.',
        required=True,
        error_messages={'required': 'Você precisa aceitar o termo para continuar.'},
    )

    def __init__(self, *args, cliente, animal, **kwargs):
        super().__init__(*args, **kwargs)
        self.cliente = cliente
        self.animal = animal

    def clean(self):
        dados = super().clean()
        if self.animal.status.casefold() != 'disponível'.casefold():
            raise forms.ValidationError('Este animal não está disponível para adoção.')

        existe_solicitacao = SolicitacaoAdocao.objects.filter(
            cliente=self.cliente,
            animal=self.animal,
            status__in=(
                SolicitacaoAdocao.Status.PENDENTE,
                SolicitacaoAdocao.Status.EM_AVALIACAO,
                SolicitacaoAdocao.Status.APROVADA,
            ),
        ).exists()
        if existe_solicitacao:
            raise forms.ValidationError(
                'Você já possui uma solicitação ativa para este animal.'
            )
        return dados

    def save(self):
        return SolicitacaoAdocao.objects.create(
            cliente=self.cliente,
            animal=self.animal,
            status=SolicitacaoAdocao.Status.PENDENTE,
        )


class RejeitarSolicitacaoAdminForm(forms.Form):
    motivo_rejeicao = forms.CharField(
        label='Motivo da rejeição',
        widget=forms.Textarea(
            attrs={
                'rows': 4,
                'placeholder': 'Explique de forma objetiva por que a solicitação foi rejeitada.',
            }
        ),
        error_messages={'required': 'Informe o motivo da rejeição.'},
    )
