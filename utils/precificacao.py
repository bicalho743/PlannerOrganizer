"""
Precificação da personal organizer: valor da hora e preço de um projeto.

Hora mínima = (quanto quer ganhar + custos fixos do mês) ÷ horas vendidas no mês,
corrigida pelo imposto sobre a venda. Hora sugerida = mínima + margem de lucro.

Projeto: as horas de trabalho somam os ambientes (× complexidade). Com assistentes, o trabalho
se divide entre a equipe: você fica (horas ÷ pessoas) no local e cada assistente também.
Preço = suas horas × sua hora + custo das assistentes + deslocamento e outros custos, com a
margem sobre os custos e o imposto por fora. Produtos vendidos à cliente ficam em Vendas.
"""

# Horas de partida por ambiente (a organizer ajusta pela própria experiência; são só sugestões)
AMBIENTES_PADRAO = {
    "Cozinha": 6.0,
    "Closet / guarda-roupa": 5.0,
    "Quarto de casal": 4.0,
    "Quarto infantil": 5.0,
    "Banheiro": 2.0,
    "Área de serviço": 3.0,
    "Despensa": 3.0,
    "Home office": 4.0,
    "Sala / estante": 3.0,
    "Mudança (por cômodo)": 6.0,
}

COMPLEXIDADE = {"Leve": 0.8, "Média": 1.0, "Pesada (muito acúmulo)": 1.3}

PADROES = {
    "renda_desejada": 5000.0,
    "custo_impostos_fixos": 80.0,
    "custo_transporte": 400.0,
    "custo_ferramentas": 150.0,
    "custo_outros": 0.0,
    "imposto_pct": 0.0,
    "dias_mes": 12,
    "horas_dia": 6.0,
    "margem_pct": 20.0,
    "valor_hora_assistente": 30.0,
}


def custos_fixos(p):
    return sum(float(p.get(k) or 0) for k in
               ("custo_impostos_fixos", "custo_transporte", "custo_ferramentas", "custo_outros"))


def horas_vendidas(p):
    return max(float(p.get("dias_mes") or 0) * float(p.get("horas_dia") or 0), 0.0)


def _sem_imposto(valor, imposto_pct):
    """Valor a cobrar para, depois do imposto sobre a venda, sobrar `valor`."""
    fator = 1 - float(imposto_pct or 0) / 100
    return valor / fator if fator > 0 else valor


def hora_liquida(p):
    """O que cada hora vendida precisa deixar no seu bolso (renda + custos fixos), antes do imposto."""
    h = horas_vendidas(p)
    return (float(p.get("renda_desejada") or 0) + custos_fixos(p)) / h if h > 0 else 0.0


def hora_minima(p):
    """Abaixo disso a conta do mês não fecha: cobre renda desejada, custos fixos e imposto."""
    return _sem_imposto(hora_liquida(p), p.get("imposto_pct"))


def hora_sugerida(p):
    """Hora mínima com a margem de lucro."""
    return hora_minima(p) * (1 + float(p.get("margem_pct") or 0) / 100)


def preco_projeto(p, horas_ambientes, complexidade=1.0, assistentes=0, deslocamento=0.0, outros_custos=0.0):
    """Preço de um projeto. horas_ambientes: horas somadas dos ambientes (antes da complexidade).

    Devolve um dict com horas, divisão da equipe, custos, preço mínimo, preço sugerido, lucro e a
    hora efetiva que você recebe no projeto."""
    horas = max(float(horas_ambientes or 0), 0.0) * float(complexidade or 1)
    pessoas = 1 + max(int(assistentes or 0), 0)
    suas_horas = horas / pessoas
    horas_assistentes = suas_horas * (pessoas - 1)
    custo_equipe = horas_assistentes * float(p.get("valor_hora_assistente") or 0)
    custos_diretos = custo_equipe + float(deslocamento or 0) + float(outros_custos or 0)
    margem = float(p.get("margem_pct") or 0) / 100

    trabalho = suas_horas * hora_liquida(p)
    minimo = _sem_imposto(trabalho + custos_diretos, p.get("imposto_pct"))
    sugerido = _sem_imposto((trabalho + custos_diretos) * (1 + margem), p.get("imposto_pct"))
    imposto = sugerido * float(p.get("imposto_pct") or 0) / 100
    lucro = sugerido - imposto - custos_diretos
    horas_dia = float(p.get("horas_dia") or 0)
    return {
        "horas_trabalho": horas,
        "pessoas": pessoas,
        "suas_horas": suas_horas,
        "horas_assistentes": horas_assistentes,
        "dias_no_local": (suas_horas / horas_dia) if horas_dia > 0 else 0.0,
        "custo_equipe": custo_equipe,
        "custos_diretos": custos_diretos,
        "preco_minimo": minimo,
        "preco_sugerido": sugerido,
        "imposto": imposto,
        "lucro": lucro,
        "hora_efetiva": (lucro / suas_horas) if suas_horas > 0 else 0.0,
    }
