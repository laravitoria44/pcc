from django.db.models import Count
from django.utils import timezone

from animais.models import Animal

from .models import SolicitacaoAdocao


CORES_GRAFICOS = ('#1f7a50', '#3b82f6', '#f59e0b', '#8b5cf6', '#dc5b5b')
NOMES_MESES = (
    'Jan',
    'Fev',
    'Mar',
    'Abr',
    'Mai',
    'Jun',
    'Jul',
    'Ago',
    'Set',
    'Out',
    'Nov',
    'Dez',
)


def inicio_mes_deslocado(data_referencia, deslocamento):
    indice_mes = data_referencia.year * 12 + data_referencia.month - 1 + deslocamento
    ano, mes_zero = divmod(indice_mes, 12)
    return data_referencia.replace(year=ano, month=mes_zero + 1, day=1)


def montar_contexto_dashboard():
    hoje = timezone.localdate()
    inicio_mes_atual = hoje.replace(day=1)
    inicio_proximo_mes = inicio_mes_deslocado(hoje, 1)

    total_animais = Animal.objects.count()
    animais_disponiveis = Animal.objects.filter(status__iexact='Disponível').count()
    adocoes_aprovadas = SolicitacaoAdocao.objects.filter(
        status=SolicitacaoAdocao.Status.APROVADA,
    )
    total_adocoes = adocoes_aprovadas.count()
    adocoes_mes = adocoes_aprovadas.filter(
        data_avaliacao__date__gte=inicio_mes_atual,
        data_avaliacao__date__lt=inicio_proximo_mes,
    ).count()
    total_avaliadas = SolicitacaoAdocao.objects.filter(
        status__in=(
            SolicitacaoAdocao.Status.APROVADA,
            SolicitacaoAdocao.Status.REJEITADA,
        ),
    ).count()
    taxa_aprovacao = round(total_adocoes / total_avaliadas * 100) if total_avaliadas else 0

    indicadores = (
        {
            'titulo': 'Total de adoções',
            'valor': total_adocoes,
            'descricao': 'solicitações aprovadas',
            'classe': 'success',
        },
        {
            'titulo': 'Total de animais',
            'valor': total_animais,
            'descricao': 'cadastrados na plataforma',
            'classe': 'success',
        },
        {
            'titulo': 'Taxa de aprovação',
            'valor': f'{taxa_aprovacao}%',
            'descricao': 'entre as solicitações avaliadas',
            'classe': 'info',
        },
        {
            'titulo': 'Animais disponíveis',
            'valor': animais_disponiveis,
            'descricao': 'aguardando um lar',
            'classe': 'warning',
        },
    )

    meses = []
    for deslocamento in range(-5, 1):
        inicio = inicio_mes_deslocado(hoje, deslocamento)
        fim = inicio_mes_deslocado(hoje, deslocamento + 1)
        quantidade = adocoes_aprovadas.filter(
            data_avaliacao__date__gte=inicio,
            data_avaliacao__date__lt=fim,
        ).count()
        meses.append(
            {
                'rotulo': NOMES_MESES[inicio.month - 1],
                'ano': inicio.year,
                'valor': quantidade,
            }
        )
    maior_valor_mensal = max((mes['valor'] for mes in meses), default=0) or 1
    for mes in meses:
        mes['percentual'] = max(4, round(mes['valor'] / maior_valor_mensal * 100))

    especies = list(
        Animal.objects.values('especie')
        .annotate(total=Count('pk'))
        .order_by('-total', 'especie')
    )
    partes_grafico = []
    acumulado = 0
    for indice, especie in enumerate(especies):
        especie['cor'] = CORES_GRAFICOS[indice % len(CORES_GRAFICOS)]
        especie['percentual'] = round(especie['total'] / total_animais * 100) if total_animais else 0
        inicio_fatia = acumulado / total_animais * 100 if total_animais else 0
        acumulado += especie['total']
        fim_fatia = acumulado / total_animais * 100 if total_animais else 100
        partes_grafico.append(f"{especie['cor']} {inicio_fatia:.2f}% {fim_fatia:.2f}%")

    situacoes = list(
        Animal.objects.values('status')
        .annotate(total=Count('pk'))
        .order_by('-total', 'status')
    )
    for indice, situacao in enumerate(situacoes):
        situacao['cor'] = CORES_GRAFICOS[indice % len(CORES_GRAFICOS)]
        situacao['percentual'] = (
            round(situacao['total'] / total_animais * 100) if total_animais else 0
        )

    return {
        'indicadores': indicadores,
        'total_animais': total_animais,
        'meses_adocoes': meses,
        'especies': especies,
        'grafico_especies': ', '.join(partes_grafico) or '#dce3ea 0% 100%',
        'situacoes_animais': situacoes,
        'adocoes_mes': adocoes_mes,
        'periodo_dashboard': 'Últimos 6 meses',
    }
