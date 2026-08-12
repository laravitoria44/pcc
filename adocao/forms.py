from django import forms

from .models import SolicitacaoAdocao


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
