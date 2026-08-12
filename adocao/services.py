from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from animais.models import Animal

from .models import SolicitacaoAdocao


class SolicitacaoNaoPodeSerAprovada(ValidationError):
    pass


class SolicitacaoNaoPodeSerRejeitada(ValidationError):
    pass


STATUS_ANIMAL_DISPONIVEL = 'Disponível'
STATUS_ANIMAL_ADOTADO = 'Adotado'


@transaction.atomic
def aprovar_solicitacao(solicitacao, administrador):
    """Aprova a solicitação e sincroniza o animal e pedidos concorrentes."""
    solicitacao = (
        SolicitacaoAdocao.objects.select_for_update()
        .select_related('animal')
        .get(pk=solicitacao.pk)
    )
    animal = Animal.objects.select_for_update().get(pk=solicitacao.animal_id)

    status_permitidos = (
        SolicitacaoAdocao.Status.PENDENTE,
        SolicitacaoAdocao.Status.EM_AVALIACAO,
    )
    if solicitacao.status not in status_permitidos:
        raise SolicitacaoNaoPodeSerAprovada(
            f'A solicitação #{solicitacao.pk} não pode ser aprovada porque está '
            f'{solicitacao.get_status_display().lower()}.'
        )

    if animal.status.casefold() != STATUS_ANIMAL_DISPONIVEL.casefold():
        raise SolicitacaoNaoPodeSerAprovada(
            f'{animal.nome} não está disponível para adoção.'
        )

    outra_aprovada = SolicitacaoAdocao.objects.filter(
        animal=animal,
        status=SolicitacaoAdocao.Status.APROVADA,
    ).exclude(pk=solicitacao.pk)
    if outra_aprovada.exists():
        raise SolicitacaoNaoPodeSerAprovada(
            f'{animal.nome} já possui outra solicitação aprovada.'
        )

    agora = timezone.now()
    solicitacao.status = SolicitacaoAdocao.Status.APROVADA
    solicitacao.administrador_avaliador = administrador
    solicitacao.data_avaliacao = agora
    solicitacao.motivo_rejeicao = ''
    solicitacao.save(
        update_fields=(
            'status',
            'administrador_avaliador',
            'data_avaliacao',
            'motivo_rejeicao',
        )
    )

    animal.status = STATUS_ANIMAL_ADOTADO
    animal.save(update_fields=('status',))

    outras_encerradas = SolicitacaoAdocao.objects.filter(
        animal=animal,
        status__in=(
            SolicitacaoAdocao.Status.PENDENTE,
            SolicitacaoAdocao.Status.EM_AVALIACAO,
        ),
    ).exclude(pk=solicitacao.pk).update(
        status=SolicitacaoAdocao.Status.REJEITADA,
        administrador_avaliador=administrador,
        data_avaliacao=agora,
        motivo_rejeicao='Outra solicitação de adoção para este animal foi aprovada.',
    )

    return solicitacao, outras_encerradas


@transaction.atomic
def rejeitar_solicitacao(solicitacao, administrador, motivo):
    """Rejeita a solicitação e libera o animal caso a adoção fosse aprovada."""
    solicitacao = (
        SolicitacaoAdocao.objects.select_for_update()
        .select_related('animal')
        .get(pk=solicitacao.pk)
    )
    animal = Animal.objects.select_for_update().get(pk=solicitacao.animal_id)

    status_permitidos = (
        SolicitacaoAdocao.Status.PENDENTE,
        SolicitacaoAdocao.Status.EM_AVALIACAO,
        SolicitacaoAdocao.Status.APROVADA,
    )
    if solicitacao.status not in status_permitidos:
        raise SolicitacaoNaoPodeSerRejeitada(
            f'A solicitação #{solicitacao.pk} não pode ser rejeitada porque está '
            f'{solicitacao.get_status_display().lower()}.'
        )

    era_aprovada = solicitacao.status == SolicitacaoAdocao.Status.APROVADA
    solicitacao.status = SolicitacaoAdocao.Status.REJEITADA
    solicitacao.administrador_avaliador = administrador
    solicitacao.data_avaliacao = timezone.now()
    solicitacao.motivo_rejeicao = motivo
    solicitacao.save(
        update_fields=(
            'status',
            'administrador_avaliador',
            'data_avaliacao',
            'motivo_rejeicao',
        )
    )

    animal_liberado = False
    if era_aprovada:
        existe_outra_aprovada = SolicitacaoAdocao.objects.filter(
            animal=animal,
            status=SolicitacaoAdocao.Status.APROVADA,
        ).exclude(pk=solicitacao.pk).exists()
        if not existe_outra_aprovada:
            animal.status = STATUS_ANIMAL_DISPONIVEL
            animal.save(update_fields=('status',))
            animal_liberado = True

    return solicitacao, animal_liberado
