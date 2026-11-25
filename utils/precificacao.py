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

# Tipos de serviço (mesmas chaves do onboarding do site): na mudança o volume vem das caixas
TIPOS_SERVICO = {"organizacao": ("Organização", "Ambientes da casa"),
                 "pre": ("Pré-mudança", "Embalar e inventariar"),
                 "pos": ("Pós-mudança", "Desembalar e organizar")}

# Caixas de partida por cômodo na mudança (ajustáveis na proposta)
CAIXAS_POR_COMODO = {"Cozinha": 12, "Quarto de casal": 10, "Sala": 8, "Quarto infantil": 6, "Banheiros": 2,
                     "Área de serviço": 4, "Escritório": 5}

# Lista de materiais de partida (a organizer edita a dela em Precificação; fica em perfis.precificacao)
MATERIAIS_PADRAO = [
    {"nome": "Caixas de papelão", "preco": 6.5, "unidade": "un"},
    {"nome": "Plástico-bolha", "preco": 45.0, "unidade": "rolo"},
    {"nome": "Fita adesiva", "preco": 8.0, "unidade": "un"},
    {"nome": "Filme stretch", "preco": 35.0, "unidade": "rolo"},
    {"nome": "Cabideiro de mudança", "preco": 60.0, "unidade": "un"},
    {"nome": "Colmeias e organizadores", "preco": 0.0, "unidade": "a definir"},
]

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
    # preço de um projeto e nova proposta
    "km_valor": 1.20,            # R$ por km rodado (ida e volta), por dia de serviço
    "taxa_cartao_pct": 4.99,     # taxa da maquininha/link, repassada no preço
    "seguranca_pct": 10.0,       # margem de segurança e lucro sobre os custos do projeto
    "sinal_pct": 50.0,           # sinal pedido na aprovação
    "caixas_dia_pre": 15,        # caixas que uma pessoa embala e inventaria por dia
    "caixas_dia_pos": 20,        # caixas que uma pessoa desembala e organiza por dia
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


def materiais(p):
    """Lista de materiais da organizer (ou a de partida)."""
    lista = p.get("materiais")
    return lista if isinstance(lista, list) and lista else [dict(m) for m in MATERIAIS_PADRAO]


def caixas_por_area(m2):
    """Estimativa sem vistoria: cerca de uma caixa a cada 3 m²."""
    return int(round(max(float(m2 or 0), 0) / 3))


def orcamento_completo(p, tipo="organizacao", *, horas_ambientes=0.0, caixas=0, complexidade=1.0, assistentes=0,
                       km=0.0, outros=0.0, materiais_escolhidos=None):
    """Orçamento de um projeto com tudo o que entra no preço (tela Precificação > Preço de um projeto e
    Nova proposta). tipo: organizacao (horas dos ambientes × complexidade) ou pre/pos (horas pelas caixas:
    caixas ÷ caixas por pessoa por dia × horas do dia).

    materiais_escolhidos: [(nome, quantidade, preço unitário)]. Deslocamento = km × R$/km × dias.
    Total = (você + assistentes + materiais + deslocamento + outros) × (1 + segurança), com a taxa do cartão
    e o imposto por fora, arredondado para cima em R$ 10. O mínimo é o mesmo cálculo sem a margem."""
    import math
    horas_dia = float(p.get("horas_dia") or 0) or 6.0
    pessoas = 1 + max(int(assistentes or 0), 0)
    if tipo in ("pre", "pos"):
        por_dia = float(p.get(f"caixas_dia_{tipo}") or 0) or 15.0
        horas = max(int(caixas or 0), 0) / por_dia * horas_dia
    else:
        horas = max(float(horas_ambientes or 0), 0.0) * float(complexidade or 1)
    suas_horas = horas / pessoas
    dias = max(math.ceil(round(suas_horas / horas_dia, 6)), 1) if horas > 0 else 0
    voce = suas_horas * hora_liquida(p)
    assistente = suas_horas * (pessoas - 1) * float(p.get("valor_hora_assistente") or 0)
    mats = [(n, float(q or 0), float(v or 0)) for n, q, v in (materiais_escolhidos or [])]
    custo_mat = sum(q * v for _, q, v in mats)
    desloc = float(km or 0) * float(p.get("km_valor") or 0) * dias
    outros = float(outros or 0)
    base = voce + assistente + custo_mat + desloc + outros
    seguranca = base * float(p.get("seguranca_pct") or 0) / 100
    taxa_pct = float(p.get("taxa_cartao_pct") or 0) / 100
    imp_pct = float(p.get("imposto_pct") or 0) / 100

    def _preco(valor):
        fator = 1 - taxa_pct - imp_pct
        return valor / fator if fator > 0 else valor
    total = math.ceil(_preco(base + seguranca) / 10) * 10 if base > 0 else 0.0
    taxa = total * taxa_pct
    imposto = total * imp_pct
    fica = total - taxa - imposto - assistente - custo_mat - desloc - outros
    return {
        "tipo": tipo, "horas": horas, "pessoas": pessoas, "dias": dias, "suas_horas": suas_horas,
        "caixas": int(caixas or 0), "voce": voce, "assistente": assistente, "materiais": custo_mat,
        "itens_materiais": mats, "deslocamento": desloc, "outros": outros, "seguranca": seguranca,
        "taxa_cartao": taxa, "imposto": imposto, "total": float(total), "minimo": _preco(base),
        "sinal": float(total) * float(p.get("sinal_pct") or 0) / 100, "fica_para_voce": fica,
        "hora_no_local": (fica / suas_horas) if suas_horas > 0 else 0.0,
    }
