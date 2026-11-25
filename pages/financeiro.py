"""
Financeiro: o dinheiro do negócio, em duas abas (desenho aprovado: protótipos financeiro e impostos).

- Lançamentos: o que sobrou no mês (entrou, gastou, retirado para você), a lista de lançamentos com filtros
  (tudo, a receber, a pagar, recebido, pago e o mês), o que está atrasado ou vencendo (com cobrança pelo
  WhatsApp), para onde foi o dinheiro e os próximos 30 dias. Cada lançamento abre os detalhes para receber,
  pagar, editar ou excluir. Embaixo, a tabela completa com busca.
- Impostos e MEI: limite do MEI com projeção, DAS de cada mês (marcar como pago), impostos do ano, declaração
  anual (DASN-SIMEI) e faturamento por mês. Para Simples Nacional e outros regimes, a mesma aba muda junto.
"""
import html as html_module
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

from utils.currency_formatter import fmt_brl
from utils.indicadores import (descricao_legivel, CATEGORIA_IMPOSTO, CATEGORIA_RETIRADA, DAS_MEI, LIMITE_MEI, REALIZADO, das_do_ano,
                               eh_retirada, entrou_gastou, faturamento_ano, impostos_pagos_no_mes, movimentos,
                               prazo_dasn, recebido_no_mes, retirado, simples_do_ano)
from utils.ui import botao_editar, botao_excluir, cartao_clicavel, input_moeda
from utils.visual import esc, icone_whatsapp
from utils import visual

LINK_PGMEI = "https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/pgmei.app/Identificacao"
LINK_DASN = "https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/dasnsimei.app/Identificacao"
LINK_PGDASD = "https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/pgdasd2018.app/Identificacao"
AVISO_CONTADOR = "O Planner organiza, mas não substitui o seu contador. Em dúvida, procure um contador."
REGIME_ROTULO = {"MEI": "MEI", "Simples Nacional": "Simples Nacional (ME)", "Outro": "Outro regime ou autônoma"}

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
         "setembro", "outubro", "novembro", "dezembro"]
MES_ABREV = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]

CATEGORIAS_RECEITA = ["Serviços de Organização", "Venda de Produtos", "Comissão sobre Fornecedores", "Serviços Adicionais"]
CATEGORIAS_DESPESA = ["Pagamento Equipe/Assistentes", "Pagamento Parceiros/Fornecedores", "Custos Operacionais",
                      "Custos Administrativos", CATEGORIA_IMPOSTO, CATEGORIA_RETIRADA]

MAX_LISTA = 12          # lançamentos do mês à vista; o resto abre em "Mostrar todos"
DIAS_VENCENDO = 7       # pendentes que vencem até daqui a N dias aparecem em "Atrasado e vencendo"
DIAS_DAS_AVISO = 30     # DAS que vence até daqui a N dias aparece na lista de lançamentos

# ícones de traço (mesma família de utils.visual.icone)
_SVG = {
    "entra": '<path d="M12 5v14"/><path d="m6 13 6 6 6-6"/>',
    "sai": '<path d="M12 19V5"/><path d="m6 11 6-6 6 6"/>',
    "ok": '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
    "relogio": '<circle cx="12" cy="12" r="8"/><path d="M12 8v4.5l3 2"/>',
    "alerta": '<path d="M12 4 3 20h18z"/><path d="M12 10v4"/><path d="M12 17v.5"/>',
    "fora": '<path d="M14 4h6v6"/><path d="M20 4 11 13"/><path d="M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
}


def _ic(nome, tam=16, larg=2):
    return (f'<svg width="{tam}" height="{tam}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="{larg}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{_SVG[nome]}</svg>')


CSS = """
<style>
.fn-eyebrow { font-size: .74rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: #9C7A22; margin: 0 0 4px; }
h1.fn-titulo { margin: 0 !important; padding: 0 !important; font-family: 'Cormorant Garamond', Georgia, serif !important;
               font-size: 2.75rem !important; font-weight: 600 !important; color: var(--navy) !important; line-height: 1.15 !important; }
h1.fn-titulo::after { content: ""; display: block; width: 40px; height: 3px; border-radius: 2px; background: var(--gold); margin-top: 8px; }
.fn-sub { color: #5B6B80; font-size: 1rem; margin: 12px 0 2px; }
.st-key-fn_acoes [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: nowrap !important; gap: 10px !important; }
.st-key-fn_acoes [data-testid="stColumn"] { min-width: 0 !important; width: auto !important; flex: 1 1 0 !important; }
.st-key-fn_acoes .stButton > button { min-height: 48px !important; border-radius: 10px !important; }
.st-key-fn_acoes .stButton > button p { font-weight: 700 !important; font-size: 1rem !important; white-space: nowrap; }
.st-key-fn_gasto .stButton > button { background: #fff !important; color: var(--navy) !important; border: 1px solid #E6E1D6 !important; }
.st-key-fn_gasto .stButton > button:hover { border-color: var(--gold) !important; }
.st-key-fn_gasto .stButton > button * { color: var(--navy) !important; }

/* abas: trilho bege, a aberta branca com o traço dourado */
.st-key-fin_abas [role="tablist"] { background: #ECE7DC !important; border-radius: 14px !important; padding: 5px !important; margin: 14px 0 4px !important; }
.st-key-fin_abas [role="tab"] { padding: 9px 18px !important; border-radius: 10px !important; }
.st-key-fin_abas [role="tab"] p { font-size: 1rem !important; }
.st-key-fin_abas [role="tab"][aria-selected="true"] { border-color: transparent !important;
    box-shadow: inset 0 -3px 0 var(--gold), 0 1px 3px rgba(0,0,0,.08) !important; }

.fn-kpis { display: grid; grid-template-columns: 1.2fr 1fr 1fr 1fr; gap: 12px; margin: 4px 0 6px; }
.fn-kpis.tres { grid-template-columns: repeat(3, minmax(0, 1fr)); margin: 14px 0 0; }
.fn-k { background: #fff; border: 1px solid #E7E2D6; border-radius: 16px; padding: 16px 18px; min-width: 0; }
.fn-k .l { font-size: .74rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: #5B6B80; }
.fn-k .v { font-size: 1.62rem; font-weight: 700; color: var(--navy); margin-top: 6px; font-variant-numeric: tabular-nums;
           white-space: nowrap; overflow: hidden; text-overflow: ellipsis; line-height: 1.25; }
.fn-k .s { font-size: .8rem; color: #5B6B80; margin-top: 4px; line-height: 1.4; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.fn-k .s .atr { color: #9B2C2C; font-weight: 600; }
.fn-k.hero { background: var(--navy); border-color: var(--navy); }
.fn-k.hero .l { color: var(--gold); }
.fn-k.hero .v { color: #fff; }
.fn-k.hero .s { color: #C7CED8; }
.fn-alerta { background: #FBE9E7; border: 1px solid #F3C9C2; border-radius: 12px; padding: 10px 14px; font-size: .88rem;
             color: #7A2620; margin: 8px 0 4px; }

.st-key-fn_filtros [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: wrap !important; gap: 8px !important; align-items: center !important; }
.st-key-fn_filtros [data-testid="stColumn"] { min-width: 0 !important; width: auto !important; flex: 0 1 auto !important; }
.st-key-fin_filtro [data-testid="stButtonGroup"] > div { flex-wrap: wrap !important; row-gap: 6px !important; }
.st-key-fin_filtro button { border-radius: 999px !important; background: #fff !important; border: 1px solid #E7E2D6 !important;
    min-height: 32px !important; padding: 2px 12px !important; }
.st-key-fin_filtro button p { font-size: .84rem !important; font-weight: 600 !important; color: #5B6B80 !important; }
.st-key-fin_filtro button[aria-checked="true"] { background: var(--navy) !important; border-color: var(--navy) !important; }
.st-key-fin_filtro button[aria-checked="true"] p { color: #fff !important; }
.st-key-fn_mes [role="group"] { border-radius: 999px !important; min-height: 34px !important; height: 34px !important;
    background: #fff !important; border: 1px solid #E7E2D6 !important; padding-left: 6px !important; }
.st-key-fn_mes input { font-size: .84rem !important; font-weight: 600 !important; color: #5B6B80 !important; -webkit-text-fill-color: #5B6B80 !important; }
.st-key-fn_mes { width: 150px; }

.fn-sec { font-size: .74rem; font-weight: 700; letter-spacing: .16em; text-transform: uppercase; color: #5B6B80;
          margin: 18px 0 8px; display: flex; justify-content: space-between; align-items: baseline; gap: 10px; }
.fn-sec span, .fn-sec a { letter-spacing: 0; text-transform: none; font-size: .86rem; color: #9C7A22 !important; font-weight: 700;
          text-decoration: none !important; white-space: nowrap; }
.fn-sec a:hover { text-decoration: underline !important; }
.fn-row { display: flex; align-items: center; gap: 12px; background: #fff; border: 1px solid #E7E2D6; border-radius: 12px;
          padding: 12px 14px; min-width: 0; transition: border-color .12s ease, box-shadow .12s ease; }
.fn-row.quente { background: #FFFCF3; border-color: #EBD9A6; }
.fn-row .ic { flex: none; width: 34px; height: 34px; border-radius: 10px; display: grid; place-items: center; }
.fn-row .ic.entra, .fn-row .ic.ok { background: #E3F1E8; color: #2F6B4F; }
.fn-row .ic.sai { background: #F7E8E4; color: #8A3B2B; }
.fn-row .ic.espera { background: #F6EDD3; color: #9C7A22; }
.fn-row .ic.atrasado { background: #FBE9E7; color: #9B2C2C; }
.fn-row .t { min-width: 0; flex: 1 1 auto; }
.fn-row .t b { color: var(--navy); font-size: .92rem; display: block; overflow-wrap: anywhere; }
.fn-row .t .d { font-size: .8rem; color: #5B6B80; display: block; overflow-wrap: anywhere; }
.fn-row .t .d .atr { color: #9B2C2C; font-weight: 600; }
.fn-row .v { margin-left: auto; font-weight: 700; font-size: .92rem; white-space: nowrap; font-variant-numeric: tabular-nums; }
.fn-row .v.in { color: #2F6B4F; } .fn-row .v.out { color: #8A3B2B; } .fn-row .v.nt { color: var(--navy); }
.fn-row .v.cancel { color: #98A2B3; text-decoration: line-through; }
.fn-wa { position: relative; z-index: 3; flex: none; display: inline-flex; align-items: center; gap: 7px; padding: 3px 10px; border-radius: 999px;
         border: 1.5px solid var(--gold); color: #7A5F0B !important; background: #fff; font-size: .76rem; font-weight: 700;
         text-decoration: none !important; white-space: nowrap; }
.fn-wa:hover { background: #F6EDD3; }
[class*="st-key-kcard_fnr_"] { margin-bottom: 8px; }
[class*="st-key-kcard_fnr_"]:hover .fn-row { border-color: #C9B98A; box-shadow: 0 2px 8px rgba(16,24,40,.07); }
[class*="st-key-kcard_fnr_"]:has(button:focus-visible) .fn-row { outline: 2px solid var(--navy); outline-offset: 2px; }
.fn-vazio { background: #fff; border: 1px solid #E7E2D6; border-radius: 12px; padding: 16px; color: #5B6B80; font-size: .9rem; }
.st-key-fn_mais button, .st-key-fn_das_mais button { color: #9C7A22 !important; }
.st-key-fn_mais button p, .st-key-fn_das_mais button p { color: #9C7A22 !important; font-weight: 700 !important; }

.fn-card { background: #fff; border: 1px solid #E7E2D6; border-radius: 16px; padding: 18px; margin-bottom: 14px; }
.fn-card h4 { font-size: .98rem !important; font-weight: 700 !important; color: var(--navy) !important; margin: 0 0 10px !important; padding: 0 !important; }
.fn-li { display: flex; justify-content: space-between; gap: 10px; font-size: .9rem; padding: 9px 0; border-top: 1px solid #F0ECE3; }
.fn-li span { color: #5B6B80; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fn-li b { color: var(--navy); white-space: nowrap; font-variant-numeric: tabular-nums; }
.fn-li b.in { color: #2F6B4F; } .fn-li b.out { color: #8A3B2B; }
.fn-bar { height: 10px; border-radius: 6px; background: #EFEBE2; overflow: hidden; margin: 2px 0 6px; }
.fn-bar i { display: block; height: 100%; background: var(--gold); border-radius: 6px; }
.fn-card .nota { font-size: .84rem; color: #5B6B80; line-height: 1.5; }
.fn-card .vz { color: #5B6B80; font-size: .88rem; }

.fn-lim .top { display: flex; justify-content: space-between; align-items: baseline; gap: 10px; font-size: .9rem; color: #5B6B80; flex-wrap: wrap; }
.fn-lim .top b { color: var(--navy); font-size: 1.4rem; font-variant-numeric: tabular-nums; }
.fn-lim .trilho { height: 14px; border-radius: 7px; background: #EFEBE2; overflow: hidden; margin: 12px 0 6px; }
.fn-lim .trilho i { display: block; height: 100%; border-radius: 7px; background: linear-gradient(90deg, #C9A84C, #B8943D); }
.fn-lim .det { font-size: .82rem; color: #5B6B80; line-height: 1.5; }
.fn-lim .det b { color: var(--navy); }
.fn-lim .det .ok { color: #2F6B4F; font-weight: 600; white-space: nowrap; }
.fn-lim .det .ok svg { vertical-align: -2px; }
.fn-lim .det .alto { color: #9B2C2C; font-weight: 600; }

.fn-cht { display: flex; align-items: flex-end; gap: 10px; height: 150px; margin: 8px 0 12px; padding: 0 4px; }
.fn-cht div { flex: 1; display: flex; flex-direction: column; justify-content: flex-end; align-items: center; gap: 4px;
              font-size: .7rem; color: #5B6B80; height: 100%; min-width: 0; }
.fn-cht i { width: 100%; border-radius: 6px 6px 0 0; display: block; background: #EFE3BE; min-height: 2px; }
.fn-cht i.on { background: var(--gold); }

.fn-solta { margin-bottom: 8px; }
.st-key-fn_regime { margin-top: 0; background: #fff; border: 1px solid #E7E2D6 !important; border-radius: 16px !important; padding: 18px !important; gap: 10px !important; }
.fn-h4 { font-size: .98rem; font-weight: 700; color: var(--navy); }
.fn-pill { pointer-events: none; }
.fn-gap { height: 8px; }

/* corpo em duas colunas: lista à esquerda, resumo à direita */
.st-key-fn_lado, .st-key-fn_lado_imp { padding-top: 8px; gap: 0 !important; }
.st-key-fn_lado .fn-card, .st-key-fn_lado_imp .fn-card { margin-bottom: 14px; }
.st-key-fn_lado_imp > [data-testid="stElementContainer"]:first-child { margin-bottom: 14px; }
/* tela média: os botões do cabeçalho descem, os números ficam 2 por linha e o resumo vai para cima da lista,
   com os dois cartões lado a lado */
@media (max-width: 1280px) {
  .fn-kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .st-key-fn_cab > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: wrap !important; }
  .st-key-fn_cab > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { flex: 1 1 100% !important; width: 100% !important; }
  .st-key-fn_acoes { max-width: 420px; margin-top: 12px; }
  .st-key-fn_corpo > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"],
  .st-key-fn_imp > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: wrap !important; }
  .st-key-fn_corpo > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"],
  .st-key-fn_imp > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { flex: 1 1 100% !important; width: 100% !important; }
  .st-key-fn_corpo > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child { order: -1; }
  .st-key-fn_lado { display: grid !important; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px !important; padding-top: 4px; }
  .st-key-fn_lado .fn-card { margin-bottom: 0; height: 100%; }
  .st-key-fn_lado_imp { display: grid !important; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px !important; align-items: start; }
  .st-key-fn_lado_imp > * { min-width: 0; margin-bottom: 0 !important; }
  .st-key-fn_lado_imp .fn-card { margin-bottom: 0; }
}
@media (max-width: 640px) {
  .st-key-fn_lado, .st-key-fn_lado_imp { grid-template-columns: 1fr; }
  h1.fn-titulo { font-size: 2.2rem !important; }
  .fn-kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
  .fn-kpis .fn-k.hero { grid-column: 1 / -1; }
  .fn-kpis.tres { grid-template-columns: 1fr; }
  .fn-k .v { font-size: 1.3rem; }
  .fn-k { padding: 14px; }
  .fn-row { flex-wrap: wrap; row-gap: 6px; }
  .fn-row .t { flex: 1 1 calc(100% - 140px); }
  .fn-wa { order: 5; margin-left: 46px; }
  .st-key-fin_abas [role="tab"] { padding: 8px 12px !important; }
  .st-key-fn_mes { width: 150px; }
}
</style>
"""


# ───────────────────────────── utilidades ─────────────────────────────

def _brl(v):
    """R$ sem os centavos quando são zero (R$ 5.180), com eles quando existem (R$ 86,05)."""
    s = fmt_brl(v)
    return s[:-3] if s.endswith(",00") else s


def _dm(d):
    return f"{d.day:02d}/{d.month:02d}"


def _quando(d, hoje):
    n = (d - hoje).days
    if n == 0:
        return "vence hoje"
    if n == 1:
        return "vence amanhã"
    if n < 0:
        return f'<span class="atr">venceu há {-n} dia{"s" if n < -1 else ""}</span>'
    return f"vence {_dm(d)}"


def _plural(n, um, varios):
    return f"{n} {um if n == 1 else varios}"


def _safe_float(val, default=0.0):
    try:
        if val is None or pd.isna(val):
            return default
        return float(val)
    except (ValueError, TypeError):
        return default


def _fmt_date(d):
    if d is None:
        return ""
    if isinstance(d, str):
        try:
            return datetime.strptime(d[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
        except Exception:
            return d
    try:
        return d.strftime("%d/%m/%Y")
    except Exception:
        return str(d)


def _data(v):
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(v, datetime) or hasattr(v, "to_pydatetime"):
        return v.date()
    if isinstance(v, date):
        return v
    try:
        return datetime.fromisoformat(str(v)[:10]).date()
    except ValueError:
        return None


def _formatar_tipo(tipo):
    if tipo in ['receita_a_receber', 'receita', 'Receita']:
        return 'Receita'
    elif tipo in ['despesa_a_pagar', 'despesa', 'Despesa']:
        return 'Despesa'
    return str(tipo).title() if tipo else ''


def _is_receita(row):
    return row.get('tipo', '') in ['receita', 'receita_a_receber', 'Receita'] or row.get('classificacao', '') == 'contas_a_receber'


def _is_despesa(row):
    return row.get('tipo', '') in ['despesa', 'despesa_a_pagar', 'Despesa'] or row.get('classificacao', '') == 'contas_a_pagar'


def _mov(financeiro_df):
    return movimentos(financeiro_df.assign(data=financeiro_df["data"].dt.date) if not financeiro_df.empty else financeiro_df)


def _regime():
    try:
        return st.session_state.db.get_regime()
    except Exception as e:
        print(f"[financeiro] regime: {e}")
        return {"regime": "MEI", "aliquota": None}


def _dedup_transacoes(df):
    if df.empty:
        return df
    dedup_cols = ['descricao', 'valor', 'data', 'proposta_id', 'categoria', 'status']
    available = [c for c in dedup_cols if c in df.columns]
    if available:
        df = df.drop_duplicates(subset=available, keep='first')

    if 'categoria' not in df.columns:
        return df
    equipe = df[df['categoria'] == 'Pagamento Equipe/Assistentes']
    assistente = df[df['categoria'] == 'Pagamento de Assistente']
    if equipe.empty or assistente.empty:
        return df
    dup_ids = []
    for _, row in assistente.iterrows():
        if 'proposta_id' in row and pd.notna(row.get('proposta_id')):
            dups = equipe[
                (equipe['proposta_id'] == row['proposta_id']) &
                (equipe['valor'] == row['valor'])
            ]
            if not dups.empty:
                dup_ids.append(row['id'])
    if dup_ids:
        return df[~df['id'].isin(dup_ids)]
    return df


def _contatos():
    """{proposta_id: (numero, cliente_id)} e {cliente_id: (nome, telefone)} para a linha e a cobrança."""
    props, clis = {}, {}
    db = st.session_state.db
    try:
        p = db.get_propostas()
        if p is not None and not p.empty:
            for _, r in p.iterrows():
                props[int(r["id"])] = (r.get("numero"), r.get("cliente_id"))
    except Exception as e:
        print(f"[financeiro] propostas: {e}")
    try:
        c = db.get_clientes()
        if c is not None and not c.empty:
            for _, r in c.iterrows():
                clis[int(r["id"])] = (r.get("nome") or "", r.get("telefone") or "")
    except Exception as e:
        print(f"[financeiro] clientes: {e}")
    return props, clis


def _itens(financeiro_df, props):
    """Cada lançamento com lado (entra/sai), vencimento (d), quando entrou/saiu e se já foi realizado."""
    itens = []
    if financeiro_df.empty:
        return itens
    for _, r in financeiro_df.iterrows():
        if _is_receita(r):
            lado = "entra"
        elif _is_despesa(r):
            lado = "sai"
        else:
            continue
        d = _data(r.get("data"))
        realizado = r.get("status") in REALIZADO
        quando = (_data(r.get("data_recebimento")) or d) if realizado else d
        pid = r.get("proposta_id")
        pid = int(pid) if pid is not None and not pd.isna(pid) else None
        numero, cli_id = props.get(pid, (None, None)) if pid else (None, None)
        if cli_id is None and str(r.get("origem_tipo") or "") == "cliente" and not pd.isna(r.get("origem_id")):
            cli_id = r.get("origem_id")
        itens.append({"id": r["id"], "lado": lado, "d": d, "quando": quando, "realizado": realizado,
                      "cancelado": str(r.get("status") or "").lower() == "cancelado",
                      "valor": _safe_float(r.get("valor")), "descricao": descricao_legivel(r.get("descricao")),
                      "categoria": str(r.get("categoria") or ""), "numero": numero,
                      "cliente_id": int(cli_id) if cli_id is not None and not pd.isna(cli_id) else None})
    return itens


def _no_mes(d, ano, mes):
    return bool(d) and d.year == ano and d.month == mes


# ───────────────────────────── cabeçalho ─────────────────────────────

def _cabecalho(com_botoes=True):
    c_tit, c_btn = st.container(key="fn_cab").columns([3, 1.6], vertical_alignment="bottom")
    c_tit.markdown('<div class="fn-eyebrow">O dinheiro do seu negócio</div><h1 class="fn-titulo">Financeiro</h1>'
                   '<div class="fn-sub">O que entrou, o que saiu e o que ainda vai entrar, sem planilha.</div>',
                   unsafe_allow_html=True)
    if not com_botoes:
        return
    with c_btn, st.container(key="fn_acoes"):
        b1, b2 = st.columns([1, 1.1])
        with b1, st.container(key="fn_gasto"):
            if st.button("Lançar gasto", icon=":material/remove:", key="fn_btn_gasto", use_container_width=True):
                _dialogo_lancamento("despesa")
        with b2, st.container(key="cta_fn_entrada"):
            if st.button("Lançar entrada", icon=":material/add:", key="btn_nova_transacao", use_container_width=True):
                _dialogo_lancamento("receita")


# ───────────────────────────── novo lançamento ─────────────────────────────

@st.dialog("Novo lançamento")
def _dialogo_lancamento(tipo_inicial):
    tipo = st.segmented_control("Tipo", ["receita", "despesa"], default=tipo_inicial, key="fin_tipo_transacao",
                                format_func={"receita": "Entrada", "despesa": "Gasto"}.get) or tipo_inicial
    descricao = st.text_input("Descrição", key=f"fin_desc_{tipo}")
    valor = input_moeda("Valor (R$)", f"fin_valor_{tipo}", value=0.0, step=10.0)
    if tipo == "receita":
        c1, c2 = st.columns(2)
        tipo_receita = c1.selectbox("Tipo de receita", ["organização", "comissão", "venda"], key="fin_tipo_rec")
        origem_tipo = c2.selectbox("Origem", ["cliente", "fornecedor"], key="fin_origem_tipo")
        origem_id = None
        if origem_tipo == "cliente":
            origens = st.session_state.db.get_clientes()
            if not origens.empty:
                origem = st.selectbox("Cliente", origens['nome'].tolist(), index=None,
                                      placeholder="Selecione uma cliente", key="fin_origem_cli")
                if origem:
                    origem_id = origens[origens['nome'] == origem]['id'].iloc[0]
            else:
                st.warning("Nenhuma cliente cadastrada.")
        else:
            fornecedores = st.session_state.db.get_fornecedores()
            if not fornecedores.empty:
                origem = st.selectbox("Fornecedor", fornecedores['descricao'].tolist(), index=None,
                                      placeholder="Selecione um fornecedor", key="fin_origem_forn")
                if origem:
                    origem_id = fornecedores[fornecedores['descricao'] == origem]['id'].iloc[0]
            else:
                st.warning("Nenhum fornecedor cadastrado.")
        categoria = st.selectbox("Categoria", CATEGORIAS_RECEITA, key="fin_cat_rec")
        if st.button("Registrar entrada", type="primary", use_container_width=True, key="fin_reg_rec"):
            if not descricao or valor <= 0:
                st.warning("Preencha a descrição e um valor maior que zero.")
            elif origem_id is None:
                st.error(f"Selecione {'uma cliente' if origem_tipo == 'cliente' else 'um fornecedor'} antes de registrar.")
            else:
                try:
                    st.session_state.db.add_transacao(
                        tipo="receita", descricao=descricao, valor=valor, categoria=categoria,
                        tipo_receita=tipo_receita, origem_id=origem_id, origem_tipo=origem_tipo)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao registrar a entrada: {e}")
    else:
        categoria = st.selectbox("Categoria", CATEGORIAS_DESPESA, key="fin_cat_desp")
        if st.button("Registrar gasto", type="primary", use_container_width=True, key="fin_reg_desp"):
            if descricao and valor > 0:
                try:
                    st.session_state.db.add_transacao(
                        tipo="despesa", descricao=descricao, valor=valor, categoria=categoria,
                        tipo_receita=None, origem_id=None, origem_tipo=None)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao registrar o gasto: {e}")
            else:
                st.warning("Preencha a descrição e um valor maior que zero.")
    st.caption("O lançamento entra como pendente, com a data de hoje. Quando o dinheiro entrar ou sair, "
               "abra o lançamento e marque como recebido ou pago.")


# ───────────────────────────── detalhes de um lançamento ─────────────────────────────

def _render_detail_panel(transacao, financeiro_df, numero=None):
    tid = transacao['id']
    descricao = esc(transacao.get('descricao', ''))
    tipo_label = _formatar_tipo(transacao.get('tipo', ''))
    categoria = esc(transacao.get('categoria', ''))
    status = str(transacao.get('status', ''))
    data_str = _fmt_date(transacao.get('data'))
    valor = _safe_float(transacao.get('valor'))
    is_rec = _is_receita(transacao)
    cor = "#2F6B4F" if is_rec else "#8A3B2B"
    fundo = "#E3F1E8" if is_rec else "#F7E8E4"

    meta_parts = [tipo_label, categoria]
    if data_str:
        meta_parts.append(data_str)
    if numero is not None and not pd.isna(numero):
        meta_parts.append(f"proposta nº {int(numero):03d}")
    meta_str = " · ".join(p for p in meta_parts if p)

    st.markdown(f"""
    <div class="fn-row" style="margin-bottom:6px">
      <span class="ic {'entra' if is_rec else 'sai'}">{_ic('entra' if is_rec else 'sai')}</span>
      <div class="t"><b>{descricao}
        <span style="display:inline-block;padding:2px 8px;border-radius:999px;font-size:.7rem;font-weight:700;
                     background:{fundo};color:{cor};margin-left:6px;vertical-align:1px">{esc(status)}</span></b>
        <span class="d">{meta_str}</span></div>
      <span class="v" style="color:{cor};font-size:1.05rem">{fmt_brl(valor)}</span>
    </div>""", unsafe_allow_html=True)

    is_pendente = status == 'Pendente'
    if is_pendente:
        acao_label = "Marcar como recebido" if is_rec else "Marcar como pago"
        acao_key = f"fin_receber_{tid}" if is_rec else f"fin_pagar_{tid}"
        confirm_key = f"fin_confirm_receber_{tid}" if is_rec else f"fin_confirm_pagar_{tid}"
        col_act1, col_act2, col_act3 = st.columns([2.2, 1.6, 1.3])
        with col_act1:
            if st.button(acao_label, key=acao_key, type="primary", icon=":material/check:", use_container_width=True):
                st.session_state[confirm_key] = True
                st.rerun()
        with col_act2:
            if botao_editar("Editar", key=f"fin_edit_{tid}", use_container_width=True):
                st.session_state["fin_editando"] = tid
                st.rerun()
        with col_act3:
            if botao_excluir("Excluir", f"fin_del_{tid}"):
                st.session_state[f"fin_confirm_del_{tid}"] = True
                st.rerun()
    else:
        col_del, _ = st.columns([1.3, 4])
        with col_del:
            if botao_excluir("Excluir", f"fin_del_{tid}"):
                st.session_state[f"fin_confirm_del_{tid}"] = True
                st.rerun()

    for chave, novo, rotulo in ((f"fin_confirm_receber_{tid}", "Recebido", "recebimento"),
                                (f"fin_confirm_pagar_{tid}", "Pago", "pagamento")):
        if not st.session_state.get(chave, False):
            continue
        st.success(f"Confirmar {rotulo} de **{fmt_brl(valor)}** · {transacao['descricao']}?")
        quando = st.date_input("Em", value=visual.hoje(), format="DD/MM/YYYY", key=f"fin_quando_{tid}")
        c1, c2, _ = st.columns([1, 1, 2])
        with c1:
            if st.button("Confirmar", key=f"conf_{novo}_{tid}", type="primary", use_container_width=True):
                try:
                    st.session_state.db.atualizar_status_transacao(tid, novo, quando)
                    st.session_state.pop(chave, None)
                    st.session_state["fin_selecionada"] = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")
        with c2:
            if st.button("Voltar", key=f"cancel_{novo}_{tid}", use_container_width=True):
                st.session_state.pop(chave, None)
                st.rerun()

    if st.session_state.get(f"fin_confirm_del_{tid}", False):
        st.warning(f"Excluir **{transacao['descricao']}** ({fmt_brl(valor)}) de vez?")
        c1, c2, _ = st.columns([1, 1, 2])
        with c1:
            if botao_excluir("Excluir de vez", f"conf_del_{tid}"):
                try:
                    st.session_state.db.delete_transacao(tid)
                    st.session_state.pop(f"fin_confirm_del_{tid}", None)
                    st.session_state["fin_selecionada"] = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")
        with c2:
            if st.button("Voltar", key=f"cancel_del_{tid}", use_container_width=True):
                st.session_state.pop(f"fin_confirm_del_{tid}", None)
                st.rerun()

    if st.session_state.get("fin_editando") == tid:
        _render_edit_form(transacao)


def _render_edit_form(transacao):
    tid = transacao['id']
    st.markdown('<div class="fn-gap"></div>', unsafe_allow_html=True)
    with st.form(key=f"edit_form_{tid}"):
        tipo_exibido = "receita" if transacao['tipo'] in ["receita", "receita_a_receber", "Receita"] else "despesa"
        tipo = st.selectbox("Tipo", ["receita", "despesa"], index=0 if tipo_exibido == "receita" else 1,
                            format_func={"receita": "Entrada", "despesa": "Gasto"}.get)
        descricao = st.text_input("Descrição", value=transacao['descricao'])
        valor = input_moeda("Valor (R$)", f"fin_valor_edit_{tid}", value=_safe_float(transacao.get('valor')), step=10.0)

        tipo_receita = None
        if tipo == "receita":
            tr_val = transacao.get('tipo_receita') if pd.notna(transacao.get('tipo_receita')) else "organização"
            tr_options = ["organização", "comissão", "venda"]
            tipo_receita = st.selectbox("Tipo de receita", tr_options,
                                        index=tr_options.index(tr_val) if tr_val in tr_options else 0)

        cat_val = transacao.get('categoria', '')
        if tipo == "receita":
            cats = CATEGORIAS_RECEITA
            if cat_val == "Serviço":
                cat_idx = 0
            elif cat_val in ["Venda de Produtos", "Produto"]:
                cat_idx = 1
            elif cat_val in ["Fornecedor", "Comissão", "Comissão sobre Fornecedores"]:
                cat_idx = 2
            elif cat_val in cats:
                cat_idx = cats.index(cat_val)
            else:
                cat_idx = 3
        else:
            cats = CATEGORIAS_DESPESA
            if cat_val in ["Assistente", "Pagamento Equipe/Assistentes", "Pagamento de Assistente"]:
                cat_idx = 0
            elif cat_val in ["Fornecedor", "Pagamento Parceiros/Fornecedores"]:
                cat_idx = 1
            elif cat_val in cats:
                cat_idx = cats.index(cat_val)
            else:
                cat_idx = 3
        categoria = st.selectbox("Categoria", cats, index=min(cat_idx, len(cats) - 1))

        col1, col2 = st.columns(2)
        with col1:
            salvar = st.form_submit_button("Salvar", type="primary", use_container_width=True)
        with col2:
            cancelar = st.form_submit_button("Cancelar", use_container_width=True)

    if salvar:
        try:
            st.session_state.db.update_transacao(tid, tipo=tipo, descricao=descricao, valor=valor,
                                                 categoria=categoria, tipo_receita=tipo_receita)
            st.session_state.pop("fin_editando", None)
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao atualizar: {e}")
    if cancelar:
        st.session_state.pop("fin_editando", None)
        st.rerun()


def _fechar_detalhes():
    st.session_state["fin_selecionada"] = None
    st.session_state.pop("fin_editando", None)
    for k in [k for k in st.session_state if str(k).startswith("fin_confirm_")]:
        st.session_state.pop(k, None)


@st.dialog("Detalhes do lançamento", width="large", on_dismiss=_fechar_detalhes)
def _modal_detalhes(transacao_sel, financeiro_df):
    numero = None
    pid = transacao_sel.get("proposta_id")
    if pid is not None and not pd.isna(pid):
        numero = _contatos()[0].get(int(pid), (None, None))[0]
    _render_detail_panel(transacao_sel, financeiro_df, numero)
    if st.button("Fechar", key=f"fin_fechar_modal_{transacao_sel['id']}", type="tertiary"):
        _fechar_detalhes()
        st.rerun()


# ───────────────────────────── DAS: marcar como pago ─────────────────────────────

@st.dialog("Marcar DAS como pago")
def _dialogo_das(ano, mes, valor_padrao, guia):
    st.markdown(f"**DAS de {MESES[mes - 1]} de {ano}**")
    c1, c2 = st.columns(2)
    pago_em = c1.date_input("Pago em", value=visual.hoje(), format="DD/MM/YYYY", key="fin_das_pago_em")
    with c2:
        valor = input_moeda("Valor (R$)", "fin_das_valor", value=round(valor_padrao, 2), step=1.0)
    if st.button("Lançar pagamento", type="primary", use_container_width=True, key="fin_das_lancar"):
        if valor <= 0:
            st.warning("Informe o valor pago.")
        elif st.session_state.db.lancar_das(ano, mes, valor, pago_em):
            st.rerun()
        else:
            st.error("Não consegui lançar agora. Tente de novo.")
    nome, link = guia
    st.link_button(nome, link, icon=":material/open_in_new:", use_container_width=True)
    st.caption(f"O pagamento entra no Financeiro como gasto pago, na categoria “{CATEGORIA_IMPOSTO}”.")


def _das_proximo(mov, regime, hoje):
    """DAS em aberto que vence nos próximos dias (ou já venceu), para aparecer na lista de lançamentos."""
    if regime["regime"] == "MEI":
        meses = das_do_ano(mov, hoje.year, hoje)
        if hoje.month == 1:
            meses = das_do_ano(mov, hoje.year - 1, hoje)[-1:] + meses
        ano_de = lambda m: m["vencimento"].year - (1 if m["mes"] == 12 else 0)
        valor = lambda m: DAS_MEI
        rot, guia = "DAS do MEI", ("Gerar a guia do DAS (PGMEI)", LINK_PGMEI)
    elif regime["regime"] == "Simples Nacional":
        meses = simples_do_ano(mov, hoje.year, hoje, regime.get("aliquota"))
        ano_de = lambda m: hoje.year
        valor = lambda m: m["das_estimado"]
        rot, guia = "DAS do Simples", ("Calcular e gerar o DAS (PGDAS-D)", LINK_PGDASD)
    else:
        return []
    out = []
    for m in meses:
        if m["situacao"] in ("atrasado", "a vencer") and m["vencimento"] <= hoje + timedelta(days=DIAS_DAS_AVISO):
            out.append({"ano": ano_de(m), "mes": m["mes"], "venc": m["vencimento"], "valor": valor(m),
                        "rotulo": rot, "guia": guia})
    return out


# ───────────────────────────── aba Lançamentos ─────────────────────────────

def _linha_html(it, hoje, props, clis, quente=False, secao_pendente=False):
    lado = it["lado"]
    partes = []
    if it["realizado"]:
        partes.append(_dm(it["quando"]) if it["quando"] else "")
    elif it["cancelado"]:
        partes.append("cancelado")
    elif it["d"]:
        partes.append(_quando(it["d"], hoje))
    if it["categoria"]:
        partes.append(esc(it["categoria"]))
    if it["numero"] is not None and not pd.isna(it["numero"]):
        try:
            partes.append(f"proposta nº {int(it['numero']):03d}")
        except (TypeError, ValueError):
            pass
    if not it["realizado"] and not it["cancelado"] and not secao_pendente:
        partes.append("a receber" if lado == "entra" else "a pagar")
    det = " · ".join(p for p in partes if p)
    if it["cancelado"]:
        cls_v, sinal = "cancel", ""
    else:
        cls_v = "in" if lado == "entra" else "out"
        sinal = ("+ " if lado == "entra" else "− ") if it["realizado"] else ""
    wa = ""
    if lado == "entra" and not it["realizado"] and not it["cancelado"] and it["d"] and it["d"] <= hoje + timedelta(days=DIAS_VENCENDO):
        nome, tel = clis.get(it["cliente_id"], ("", "")) if it["cliente_id"] else ("", "")
        from utils.whatsapp_helper import whatsapp_link
        primeiro = str(nome).split(" ")[0] if nome else ""
        msg = (f"Oi{', ' + primeiro if primeiro else ''}! Tudo bem? Passando para lembrar do pagamento de "
               f"{fmt_brl(it['valor'])} ({it['descricao']}), com vencimento em {it['d'].strftime('%d/%m')}. "
               "Qualquer dúvida, estou à disposição!")
        url = whatsapp_link(tel, msg) if tel else ""
        if url:
            wa = (f'<a class="fn-wa" href="{esc(url)}" target="_blank" rel="noopener">{icone_whatsapp(16)}'
                  '<span>Cobrar no WhatsApp</span></a>')
    return (f'<div class="fn-row{" quente" if quente else ""}"><span class="ic {lado}">{_ic(lado)}</span>'
            f'<div class="t"><b>{esc(it["descricao"]) or "Sem descrição"}</b><span class="d">{det}</span></div>'
            f'{wa}<span class="v {cls_v}">{sinal}{_brl(it["valor"])}</span></div>')


def _linha(it, hoje, props, clis, quente=False, secao_pendente=False):
    if cartao_clicavel(_linha_html(it, hoje, props, clis, quente, secao_pendente), key=f"fnr_{it['id']}",
                       rotulo=f"Abrir {it['descricao']}"):
        st.session_state["fin_selecionada"] = it["id"]


def _linha_das(item, hoje):
    atrasado = item["venc"] < hoje
    det = (f'<span class="atr">venceu {_dm(item["venc"])}</span>' if atrasado else f'vence {_dm(item["venc"])}')
    html = (f'<div class="fn-row"><span class="ic sai">{_ic("sai")}</span>'
            f'<div class="t"><b>{item["rotulo"]}</b><span class="d">{det} · imposto de {MESES[item["mes"] - 1]}</span></div>'
            f'<span class="v out">{_brl(item["valor"])}</span></div>')
    if cartao_clicavel(html, key=f"fnr_das_{item['ano']}_{item['mes']}", rotulo=f"Marcar {item['rotulo']} como pago"):
        _dialogo_das(item["ano"], item["mes"], item["valor"], item["guia"])


def _sec(titulo, direita=""):
    st.markdown(f'<div class="fn-sec">{titulo}<span>{direita}</span></div>', unsafe_allow_html=True)


def _vazio(txt):
    st.markdown(f'<div class="fn-vazio">{txt}</div>', unsafe_allow_html=True)


def _lista(itens, hoje, props, clis, chave, quente=None, secao_pendente=False):
    todos = st.session_state.get(f"fin_todos_{chave}")
    for it in (itens if todos else itens[:MAX_LISTA]):
        _linha(it, hoje, props, clis, quente=bool(quente and quente(it)), secao_pendente=secao_pendente)
    if len(itens) > MAX_LISTA:
        with st.container(key="fn_mais"):
            if st.button("Mostrar menos" if todos else f"Mostrar todos ({len(itens)})", key=f"fin_mais_{chave}",
                         type="tertiary"):
                st.session_state[f"fin_todos_{chave}"] = not todos
                st.rerun()


def _conteudo_lancamentos(financeiro_df, regime):
    hoje = visual.hoje()
    mov = _mov(financeiro_df)
    props, clis = _contatos()
    itens = _itens(financeiro_df, props)

    # mês escolhido (o seletor fica na linha dos filtros, mas vale também para os números de cima)
    opcoes = []
    a, m = hoje.year, hoje.month
    for _ in range(12):
        opcoes.append((a, m))
        a, m = (a - 1, 12) if m == 1 else (a, m - 1)
    if st.session_state.get("fin_mes_painel") not in opcoes:
        st.session_state["fin_mes_painel"] = opcoes[0]
    ano, mes = st.session_state["fin_mes_painel"]

    entrou, gastou = entrou_gastou(mov, ano, mes)
    sobrou = entrou - gastou
    retirou = retirado(mov, ano, mes)
    n_rec = sum(1 for it in itens if it["realizado"] and it["lado"] == "entra" and _no_mes(it["quando"], ano, mes))
    cats = _categorias_gasto(itens, ano, mes)
    sub_gasto = (" · ".join(f"{esc(c).lower()} {v / gastou:.0%}" for c, v in cats[:2]) if gastou and cats
                 else "nenhum gasto pago")
    nome_mes = MESES[mes - 1]
    st.markdown(
        '<div class="fn-kpis">'
        f'<div class="fn-k hero"><div class="l">{"Sobrou" if sobrou >= 0 else "Faltou"} em {nome_mes}</div>'
        f'<div class="v">{_brl(sobrou)}</div><div class="s">entrou {_brl(entrou)} · gastou {_brl(gastou)}</div></div>'
        f'<div class="fn-k"><div class="l">Entrou</div><div class="v">{_brl(entrou)}</div>'
        f'<div class="s">{_plural(n_rec, "recebimento", "recebimentos")}</div></div>'
        f'<div class="fn-k"><div class="l">Gastou</div><div class="v">{_brl(gastou)}</div><div class="s">{sub_gasto}</div></div>'
        f'<div class="fn-k"><div class="l">Retirado para você</div><div class="v">{_brl(retirou)}</div>'
        f'<div class="s">{"pró-labore do mês" if retirou else "lance como “" + CATEGORIA_RETIRADA + "”"}</div></div>'
        '</div>', unsafe_allow_html=True)
    if retirou and retirou > sobrou > -1:
        st.markdown(f'<div class="fn-alerta">Você retirou {fmt_brl(retirou - sobrou)} a mais do que a empresa lucrou em '
                    f'{nome_mes}. Separe o dinheiro da empresa do pessoal para o caixa não ficar no vermelho.</div>',
                    unsafe_allow_html=True)

    pend = [it for it in itens if not it["realizado"] and not it["cancelado"]]
    a_receber = sorted([it for it in pend if it["lado"] == "entra"], key=lambda i: i["d"] or date.max)
    a_pagar = sorted([it for it in pend if it["lado"] == "sai"], key=lambda i: i["d"] or date.max)
    rot_filtro = {"tudo": "Tudo", "receber": f"A receber ({len(a_receber)})", "pagar": f"A pagar ({len(a_pagar)})",
                  "recebido": "Recebido", "pago": "Pago"}

    corpo = st.container(key="fn_corpo")
    col_lista, col_lado = corpo.columns([1.9, 1], gap="medium")
    with col_lista:
        with st.container(key="fn_filtros"):
            c_f, c_m = st.columns([5, 1.3], vertical_alignment="center")
            with c_f:
                filtro = st.pills("Mostrar", list(rot_filtro), default="tudo", format_func=rot_filtro.get,
                                  key="fin_filtro", label_visibility="collapsed") or "tudo"
            with c_m, st.container(key="fn_mes"):
                st.selectbox("Mês", opcoes, key="fin_mes_painel", label_visibility="collapsed",
                             format_func=lambda am: (MESES[am[1] - 1].capitalize() if am[0] == hoje.year
                                                     else f"{MESES[am[1] - 1].capitalize()} de {am[0]}"))

        do_mes = [it for it in itens if (_no_mes(it["quando"], ano, mes) if it["realizado"] else _no_mes(it["d"], ano, mes))]
        do_mes.sort(key=lambda i: (i["quando"] or i["d"] or date.min), reverse=True)
        if filtro == "tudo":
            mostrados = set()
            atual = (ano, mes) == (hoje.year, hoje.month)
            if atual:
                quentes = [it for it in pend if it["d"] and it["d"] <= hoje + timedelta(days=DIAS_VENCENDO)]
                quentes.sort(key=lambda i: (i["lado"] != "entra", i["d"]))
                das = _das_proximo(mov, regime, hoje)
                if quentes or das:
                    _sec("Atrasado e vencendo")
                    for it in quentes:
                        _linha(it, hoje, props, clis, quente=(it["lado"] == "entra"), secao_pendente=True)
                    for item in das:
                        _linha_das(item, hoje)
                    mostrados = {it["id"] for it in quentes}
            resto = [it for it in do_mes if it["id"] not in mostrados]
            _sec(f"{nome_mes}{'' if ano == hoje.year else ' de ' + str(ano)}",
                 _plural(len(resto), "lançamento", "lançamentos") if resto else "")
            if resto:
                _lista(resto, hoje, props, clis, f"mes_{ano}_{mes}")
            else:
                _vazio(f"Nenhum lançamento em {nome_mes}. Use “Lançar entrada” ou “Lançar gasto” no alto da tela.")
        elif filtro in ("receber", "pagar"):
            lista = a_receber if filtro == "receber" else a_pagar
            _sec("A receber" if filtro == "receber" else "A pagar", _brl(sum(i["valor"] for i in lista)) if lista else "")
            if lista:
                _lista(lista, hoje, props, clis, filtro,
                       quente=(lambda i: i["d"] and i["d"] <= hoje + timedelta(days=DIAS_VENCENDO)) if filtro == "receber" else None,
                       secao_pendente=True)
            else:
                _vazio("Nada pendente por aqui.")
        else:
            lado = "entra" if filtro == "recebido" else "sai"
            lista = [it for it in do_mes if it["realizado"] and it["lado"] == lado]
            _sec(f"{'Recebido' if lado == 'entra' else 'Pago'} em {nome_mes}",
                 _brl(sum(i["valor"] for i in lista)) if lista else "")
            if lista:
                _lista(lista, hoje, props, clis, filtro)
            else:
                _vazio(f"Nada {'recebido' if lado == 'entra' else 'pago'} em {nome_mes}.")

    with col_lado, st.container(key="fn_lado"):
        st.markdown(_card_para_onde(cats, gastou), unsafe_allow_html=True)
        lim = hoje + timedelta(days=30)
        vai_entrar = sum(it["valor"] for it in a_receber if it["d"] and it["d"] <= lim)
        vai_sair = sum(it["valor"] for it in a_pagar if it["d"] and it["d"] <= lim)
        st.markdown('<div class="fn-card"><h4>Próximos 30 dias</h4>'
                    f'<div class="fn-li"><span>Vai entrar</span><b class="in">{_brl(vai_entrar)}</b></div>'
                    f'<div class="fn-li"><span>Vai sair</span><b class="out">{_brl(vai_sair)}</b></div>'
                    f'<div class="fn-li"><span>Saldo previsto</span><b>{_brl(vai_entrar - vai_sair)}</b></div>'
                    '<div class="nota" style="margin-top:6px">Conta o que está pendente, inclusive o que já venceu.</div>'
                    '</div>', unsafe_allow_html=True)

    _historico(financeiro_df)


def _categorias_gasto(itens, ano, mes):
    """[(categoria, valor)] dos gastos pagos no mês (sem retiradas), do maior para o menor."""
    soma = {}
    for it in itens:
        if it["realizado"] and it["lado"] == "sai" and _no_mes(it["quando"], ano, mes) and not eh_retirada(it["categoria"]):
            nome = it["categoria"].strip() or "Sem categoria"
            soma[nome] = soma.get(nome, 0.0) + it["valor"]
    return sorted(((k, v) for k, v in soma.items() if v), key=lambda kv: -kv[1])


def _card_para_onde(cats, total):
    if not cats or not total:
        return ('<div class="fn-card"><h4>Para onde foi o dinheiro</h4>'
                '<div class="vz">Nenhum gasto pago neste mês.</div></div>')
    linhas = cats[:3] + ([("Outros", sum(v for _, v in cats[3:]))] if len(cats) > 4 else cats[3:4])
    h = '<div class="fn-card"><h4>Para onde foi o dinheiro</h4>'
    for nome, v in linhas:
        h += (f'<div class="fn-li"><span title="{esc(nome)}">{esc(nome)}</span><b>{_brl(v)}</b></div>'
              f'<div class="fn-bar"><i style="width:{max(v / total * 100, 1.5):.0f}%"></i></div>')
    return h + '</div>'


def _historico(financeiro_df):
    """Todos os lançamentos em tabela, com busca, tipo e período (e excluir pela lista)."""
    st.markdown('<div class="fn-gap"></div>', unsafe_allow_html=True)
    with st.expander("Ver todos os lançamentos em tabela", expanded=False, icon=":material/table_view:"):
        historico = financeiro_df.copy() if not financeiro_df.empty else pd.DataFrame()
        if historico.empty:
            st.info("Ainda não há lançamentos.")
            return
        h1, h2, h3, h4 = st.columns([2, 1.3, 1.3, 1.3])
        busca = h1.text_input("Buscar por descrição", key="fin_hist_busca")
        tipo_filtro = h2.multiselect("Tipo", ["receita", "despesa"], key="fin_hist_tipo",
                                     format_func={"receita": "Entrada", "despesa": "Gasto"}.get)
        status_filtro = h3.multiselect("Situação", sorted(historico['status'].dropna().astype(str).unique()),
                                       key="fin_hist_status")
        meses_disponiveis = sorted(historico['data'].dt.to_period('M').dropna().unique(), reverse=True)
        mes_filtro = h4.selectbox("Período", ["Todos"] + [str(m) for m in meses_disponiveis], key="fin_hist_mes",
                                  format_func=lambda s: s if s == "Todos" else f"{MES_ABREV[int(s[5:]) - 1]}/{s[:4]}")
        tipo_map = {"receita": ["receita", "receita_a_receber", "Receita"], "despesa": ["despesa", "despesa_a_pagar", "Despesa"]}
        if busca:
            historico = historico[historico['descricao'].str.contains(busca, case=False, na=False, regex=False)]
        if tipo_filtro:
            historico = historico[historico['tipo'].isin([t for k in tipo_filtro for t in tipo_map[k]])]
        if status_filtro:
            historico = historico[historico['status'].astype(str).isin(status_filtro)]
        if mes_filtro != "Todos":
            historico = historico[historico['data'].dt.to_period('M').astype(str) == mes_filtro]
        if historico.empty:
            st.info("Nenhum lançamento com esses filtros.")
            return
        rec_total = historico[historico.apply(_is_receita, axis=1)]['valor'].sum()
        desp_total = historico[historico.apply(_is_despesa, axis=1)]['valor'].sum()
        st.markdown('<div class="fn-kpis" style="margin:6px 0 12px">'
                    f'<div class="fn-k"><div class="l">Entradas</div><div class="v">{_brl(rec_total)}</div></div>'
                    f'<div class="fn-k"><div class="l">Gastos</div><div class="v">{_brl(desp_total)}</div></div>'
                    f'<div class="fn-k"><div class="l">Saldo</div><div class="v">{_brl(rec_total - desp_total)}</div></div>'
                    f'<div class="fn-k"><div class="l">Lançamentos</div><div class="v">{len(historico)}</div></div>'
                    '</div>', unsafe_allow_html=True)
        df_disp = pd.DataFrame({
            "Data": historico['data'].dt.strftime('%d/%m/%Y'),
            "Tipo": historico['tipo'].apply(_formatar_tipo),
            "Descrição": historico['descricao'],
            "Valor": historico['valor'].apply(fmt_brl),
            "Categoria": historico['categoria'].fillna(''),
            "Situação": historico['status'],
        })
        st.dataframe(df_disp, use_container_width=True, hide_index=True)
        st.download_button("Baixar em planilha (CSV)", data=df_disp.to_csv(index=False, sep=";").encode("utf-8-sig"),
                           file_name="lancamentos.csv", mime="text/csv", icon=":material/download:", key="fin_hist_csv")

        opcoes = [f"{r['data'].strftime('%d/%m/%Y') if pd.notna(r['data']) else ''} · {r['descricao']} · "
                  f"{fmt_brl(r['valor'])} · {r['status']}" for _, r in historico.iterrows()]
        col_sel, col_abrir = st.columns([5, 1.2], vertical_alignment="bottom")
        idx = col_sel.selectbox("Abrir um lançamento", range(len(opcoes)), format_func=lambda x: opcoes[x],
                                key="fin_hist_select")
        with col_abrir:
            if st.button("Abrir", key="fin_hist_abrir", use_container_width=True):
                st.session_state["fin_selecionada"] = historico.iloc[idx]['id']


# ───────────────────────────── aba Impostos ─────────────────────────────

def _grafico_faturamento(mov, ano, hoje):
    ultimo = hoje.month if ano == hoje.year else 12
    meses = list(range(max(1, ultimo - 5), ultimo + 1))
    vals = [recebido_no_mes(mov, ano, m) for m in meses]
    topo = max(vals) or 1
    barras = "".join(f'<div title="{MESES[m - 1]}: {fmt_brl(v)}"><i class="{"on" if m == ultimo else ""}" '
                     f'style="height:{v / topo * 125:.0f}px"></i>{MES_ABREV[m - 1]}</div>' for m, v in zip(meses, vals))
    return f'<div class="fn-cht">{barras}</div>'


def _card_faturamento(mov, ano, hoje, linhas):
    h = f'<div class="fn-card"><h4>Faturamento por mês</h4>{_grafico_faturamento(mov, ano, hoje)}'
    for rot, val in linhas:
        h += f'<div class="fn-li"><span>{rot}</span><b>{val}</b></div>'
    return h + '</div>'


def _bloco_regime(regime, chave_ano):
    """Cartão com o tipo de empresa (MEI, Simples, outro), o ano e, no Simples, a alíquota da contadora."""
    hoje = visual.hoje()
    with st.container(border=True, key="fn_regime"):
        st.markdown('<div class="fn-h4">Tipo de empresa</div>', unsafe_allow_html=True)
        opcoes = list(REGIME_ROTULO)
        escolha = st.selectbox("Sua empresa é", opcoes, index=opcoes.index(regime["regime"]),
                               format_func=REGIME_ROTULO.get, key="fin_regime",
                               help="Passou do limite do MEI ou abriu uma ME? Troque aqui e a aba muda junto.")
        aliquota = regime.get("aliquota")
        if escolha == "Simples Nacional":
            aliquota = st.number_input("Alíquota informada pela contadora (%) · opcional", 0.0, 40.0,
                                       value=float(aliquota) if aliquota else None, step=0.01, format="%.2f",
                                       key="fin_aliquota", placeholder="em branco: calculo pelo Anexo III")
        ano = st.selectbox("Ano", [hoje.year, hoje.year - 1], key=chave_ano)
    if escolha != regime["regime"] or (escolha == "Simples Nacional" and aliquota != regime.get("aliquota")):
        if st.session_state.db.salvar_regime(escolha, aliquota if escolha == "Simples Nacional" else None):
            st.session_state["fin_abrir_impostos"] = True
            st.rerun()
    return escolha, aliquota, ano


def _linhas_das(meses, ano, hoje, valor_padrao, guia, extra=None):
    """DAS de cada mês, do mais novo para o mais antigo: pago (com a data) ou em aberto (com o botão)."""
    devidos = [m for m in meses if m["situacao"] not in ("futuro", "sem receita")][::-1]
    if not devidos:
        _vazio("Nenhum DAS devido ainda neste ano.")
        return
    todos = st.session_state.get("fin_das_todos")
    for m in (devidos if todos else devidos[:6]):
        nome = MESES[m["mes"] - 1].capitalize()
        complemento = f" · {extra(m)}" if extra else ""
        if m["situacao"] == "pago":
            valor = m.get("valor_pago") or valor_padrao(m)
            st.markdown(f'<div class="fn-row fn-solta"><span class="ic ok">{_ic("ok")}</span>'
                        f'<div class="t"><b>{nome}</b><span class="d">pago {_dm(m["pago_em"])}{complemento}</span></div>'
                        f'<span class="v nt">{_brl(valor)}</span></div>', unsafe_allow_html=True)
            continue
        atrasado = m["situacao"] == "atrasado"
        quando = (f'<span class="atr">atrasado · venceu {_dm(m["vencimento"])}</span>' if atrasado
                  else f'vence {_dm(m["vencimento"])}')
        html = (f'<div class="fn-row"><span class="ic {"atrasado" if atrasado else "espera"}">'
                f'{_ic("alerta" if atrasado else "relogio")}</span><div class="t"><b>{nome}</b>'
                f'<span class="d">{quando}{complemento}</span></div><span class="fn-wa fn-pill">Marcar como pago</span>'
                f'<span class="v nt">{_brl(valor_padrao(m))}</span></div>')
        if cartao_clicavel(html, key=f"fnr_das_{ano}_{m['mes']}_aba", rotulo=f"Marcar o DAS de {nome} como pago"):
            _dialogo_das(ano, m["mes"], valor_padrao(m), guia)
    if len(devidos) > 6:
        with st.container(key="fn_das_mais"):
            if st.button("Mostrar menos" if todos else f"Ver o ano todo ({len(devidos)} meses)", key="fin_das_mais_btn",
                         type="tertiary"):
                st.session_state["fin_das_todos"] = not todos
                st.rerun()


def _aba_impostos(financeiro_df, regime):
    mov = _mov(financeiro_df)
    hoje = visual.hoje()
    corpo = st.container(key="fn_imp")
    col_e, col_d = corpo.columns([1.9, 1], gap="medium")
    with col_d, st.container(key="fn_lado_imp"):
        lugar_grafico = st.empty()
        escolha, aliquota, ano = _bloco_regime(regime, "fin_imp_ano")
        lugar_decl = st.container()
        st.markdown(f'<div class="fn-card" style="margin-top:14px"><div class="nota">{AVISO_CONTADOR}</div></div>',
                    unsafe_allow_html=True)
    with col_e:
        st.markdown('<div class="fn-gap"></div>', unsafe_allow_html=True)
        if escolha == "MEI":
            _aba_mei(mov, ano, hoje, lugar_grafico, lugar_decl)
        elif escolha == "Simples Nacional":
            _aba_simples(mov, ano, hoje, aliquota, lugar_grafico)
        else:
            _aba_outro(mov, ano, hoje, lugar_grafico)


def _impostos_do_ano(mov, ano, hoje):
    ultimo = hoje.month if ano == hoje.year else 12
    return sum(impostos_pagos_no_mes(mov, ano, m) for m in range(1, ultimo + 1))


def _peso(imp, total):
    return (f"{imp / total:.1%} do que entrou".replace(".", ",")) if total else "nada recebido ainda"


def _aba_mei(mov, ano, hoje, lugar_grafico, lugar_decl):
    """MEI: limite do ano com projeção, DAS de cada mês, impostos do ano e a declaração anual (DASN-SIMEI)."""
    fat = faturamento_ano(mov, ano)
    uso = fat["total"] / LIMITE_MEI
    if ano == hoje.year:
        dia = hoje.timetuple().tm_yday
        proj = fat["total"] / dia * (366 if ano % 4 == 0 else 365) if fat["total"] else 0.0
    else:
        proj = fat["total"]
    das = das_do_ano(mov, ano, hoje)
    devidos = [m for m in das if m["situacao"] != "futuro"]
    pagos = sum(m["situacao"] == "pago" for m in devidos)
    atrasados = [m for m in devidos if m["situacao"] == "atrasado"]
    abertos = [m for m in devidos if m["situacao"] != "pago"]
    ano_decl, limite_decl, faltam = prazo_dasn(hoje)
    imp = _impostos_do_ano(mov, ano, hoje)
    peso_imp = _peso(imp, fat["total"])

    if ano == hoje.year:
        ritmo = (f'no ritmo atual você termina o ano em <b>{_brl(proj)}</b>, '
                 + (f'<span class="ok">dentro do limite {_ic("ok", 13, 2.4)}</span>' if proj <= LIMITE_MEI
                    else '<span class="alto">acima do limite: converse com sua contadora</span>'))
    else:
        ritmo = (f'o ano fechou em <b>{_brl(proj)}</b>'
                 + ('' if proj <= LIMITE_MEI else ', <span class="alto">acima do limite</span>'))
    st.markdown(f'<div class="fn-card fn-lim"><h4>Limite do MEI em {ano}</h4>'
                f'<div class="top"><span><b>{_brl(fat["total"])}</b> faturados</span><span>limite {_brl(LIMITE_MEI)}</span></div>'
                f'<div class="trilho"><i style="width:{min(uso, 1) * 100:.0f}%"></i></div>'
                f'<div class="det">{uso:.0%} usado · {ritmo}</div></div>', unsafe_allow_html=True)

    if atrasados:
        sub_das = f'<span class="atr">{_plural(len(atrasados), "em atraso", "em atraso")}</span>'
    elif abertos:
        sub_das = f'próximo: {_dm(abertos[0]["vencimento"])} · {_brl(DAS_MEI)}'
    else:
        sub_das = "nenhum em aberto"
    st.markdown('<div class="fn-kpis tres">'
                f'<div class="fn-k"><div class="l">DAS pagos</div><div class="v">{pagos} de {len(devidos)}</div>'
                f'<div class="s">{sub_das}</div></div>'
                f'<div class="fn-k"><div class="l">Impostos no ano</div><div class="v">{_brl(imp)}</div>'
                f'<div class="s">{peso_imp}</div></div>'
                f'<div class="fn-k"><div class="l">Declaração anual</div><div class="v">até {limite_decl:%d/%m}</div>'
                f'<div class="s">DASN-SIMEI de {ano_decl}</div></div>'
                '</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="fn-sec">DAS de cada mês<a href="{LINK_PGMEI}" target="_blank" rel="noopener">'
                f'Gerar a guia (PGMEI) {_ic("fora", 13)}</a></div>', unsafe_allow_html=True)
    _linhas_das(das, ano, hoje, lambda m: DAS_MEI, ("Gerar a guia do DAS (PGMEI)", LINK_PGMEI))
    st.caption(f"O DAS de cada mês vence no dia 20 do mês seguinte. Em 2026 o valor para serviços é {fmt_brl(DAS_MEI).replace('$', '&#36;')}. "
               f"Pagou por fora? Marque aqui ou lance como “{CATEGORIA_IMPOSTO}”. O limite conta só o que já foi "
               f"recebido; se o MEI foi aberto em {ano}, ele é de {fmt_brl(LIMITE_MEI / 12).replace('$', '&#36;')} por mês de atividade. "
               "Passar até 20% do limite: paga a diferença e vira microempresa no ano seguinte; acima disso, o "
               "desenquadramento volta ao início do ano.")

    ultimo = hoje.month if ano == hoje.year else 12
    media = fat["total"] / ultimo if ultimo else 0
    resta = LIMITE_MEI - fat["total"]
    lugar_grafico.markdown(_card_faturamento(mov, ano, hoje, [
        ("Média por mês", _brl(media)),
        ("Pode faturar até dezembro" if resta >= 0 else "Passou do limite", _brl(abs(resta)))]), unsafe_allow_html=True)

    with lugar_decl:
        ant = faturamento_ano(mov, ano_decl)
        st.markdown(f'<div class="fn-card" style="margin-top:14px"><h4>Declaração anual · DASN-SIMEI {ano_decl}</h4>'
                    f'<div class="fn-li"><span>Receita bruta de {ano_decl}</span><b>{_brl(ant["total"])}</b></div>'
                    f'<div class="fn-li"><span>Serviços</span><b>{_brl(ant["servicos"])}</b></div>'
                    f'<div class="fn-li"><span>Venda de produtos (comércio)</span><b>{_brl(ant["comercio"])}</b></div>'
                    f'<div class="nota" style="margin-top:6px">Prazo: até {limite_decl:%d/%m/%Y} (faltam {faltam} dias). São esses números que '
                    'a declaração pede. Confira com seus extratos antes de enviar.</div></div>', unsafe_allow_html=True)
        st.link_button("Fazer a declaração", LINK_DASN, icon=":material/open_in_new:", use_container_width=True)


def _aba_simples(mov, ano, hoje, aliquota_informada, lugar_grafico):
    """Simples Nacional: receita de 12 meses, alíquota efetiva e DAS estimado de cada mês."""
    meses = simples_do_ano(mov, ano, hoje, aliquota_informada)
    atual = meses[hoje.month - 1] if ano == hoje.year else meses[-1]
    devidos = [m for m in meses if m["situacao"] not in ("futuro", "sem receita")]
    atrasados = [m for m in devidos if m["situacao"] == "atrasado"]
    abertos = [m for m in devidos if m["situacao"] != "pago"]
    fat = faturamento_ano(mov, ano)
    aliq = f"{atual['aliquota'] * 100:.2f}%".replace(".", ",")
    st.markdown(f'<div class="fn-card fn-lim"><h4>Simples Nacional em {ano}</h4>'
                f'<div class="top"><span><b>{_brl(fat["total"])}</b> faturados</span>'
                f'<span>receita de 12 meses {_brl(atual["rbt12"])}</span></div>'
                f'<div class="det" style="margin-top:8px">Alíquota efetiva de <b>{aliq}</b> '
                f'({"informada pela contadora" if aliquota_informada else "Anexo III, serviços"}). '
                'É a receita dos últimos 12 meses que define a alíquota.</div></div>', unsafe_allow_html=True)
    imp = _impostos_do_ano(mov, ano, hoje)
    peso_imp = _peso(imp, fat["total"])
    if atrasados:
        sub_das = f'<span class="atr">{_plural(len(atrasados), "em atraso", "em atraso")}</span>'
    elif abertos:
        sub_das = f'próximo: {_dm(abertos[0]["vencimento"])} · {_brl(abertos[0]["das_estimado"])}'
    else:
        sub_das = "nenhum em aberto"
    st.markdown('<div class="fn-kpis tres">'
                f'<div class="fn-k"><div class="l">DAS pagos</div><div class="v">{sum(m["situacao"] == "pago" for m in devidos)} de {len(devidos)}</div>'
                f'<div class="s">{sub_das}</div></div>'
                f'<div class="fn-k"><div class="l">Impostos no ano</div><div class="v">{_brl(imp)}</div>'
                f'<div class="s">{peso_imp}</div></div>'
                f'<div class="fn-k"><div class="l">Declaração anual</div><div class="v">até 31/03</div>'
                f'<div class="s">DEFIS do Simples</div></div>'
                '</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="fn-sec">DAS de cada mês<a href="{LINK_PGDASD}" target="_blank" rel="noopener">'
                f'Calcular e gerar (PGDAS-D) {_ic("fora", 13)}</a></div>', unsafe_allow_html=True)
    _linhas_das(meses, ano, hoje, lambda m: m["das_estimado"], ("Calcular e gerar o DAS (PGDAS-D)", LINK_PGDASD),
                extra=lambda m: f"recebido {_brl(m['receita'])}")
    st.caption("Estimativa pelo que foi recebido em cada mês. O valor oficial é o calculado no PGDAS-D. Organização "
               "costuma ficar no Anexo III; algumas atividades vão para o Anexo V conforme o fator R: confirme com "
               "a sua contadora e, se ela passar a alíquota, informe ao lado. O DAS vence no dia 20 do mês seguinte "
               "e o limite do Simples é de R$ 4,8 milhões por ano.")
    ultimo = hoje.month if ano == hoje.year else 12
    lugar_grafico.markdown(_card_faturamento(mov, ano, hoje, [
        ("Média por mês", _brl(fat["total"] / ultimo if ultimo else 0)),
        ("DAS estimado do mês", _brl(atual["das_estimado"]))]), unsafe_allow_html=True)


def _aba_outro(mov, ano, hoje, lugar_grafico):
    """Outro regime (Lucro Presumido) ou autônoma: recebido e impostos pagos mês a mês, para a contadora."""
    ultimo = hoje.month if ano == hoje.year else 12
    linhas = [(m, recebido_no_mes(mov, ano, m), impostos_pagos_no_mes(mov, ano, m)) for m in range(1, ultimo + 1)]
    rec = sum(l[1] for l in linhas)
    imp = sum(l[2] for l in linhas)
    st.markdown(f'<div class="fn-card fn-lim"><h4>Recebido em {ano}</h4>'
                f'<div class="top"><span><b>{_brl(rec)}</b> recebidos</span><span>impostos pagos {_brl(imp)}</span></div>'
                f'<div class="det" style="margin-top:8px">Lance os impostos como “{CATEGORIA_IMPOSTO}” para eles '
                'aparecerem aqui.</div></div>', unsafe_allow_html=True)
    peso = f"{imp / rec:.1%}".replace(".", ",") if rec else "0%"
    st.markdown('<div class="fn-kpis tres">'
                f'<div class="fn-k"><div class="l">Impostos pagos</div><div class="v">{_brl(imp)}</div>'
                f'<div class="s">no ano de {ano}</div></div>'
                f'<div class="fn-k"><div class="l">Peso dos impostos</div><div class="v">{peso}</div>'
                '<div class="s">impostos ÷ recebido</div></div>'
                f'<div class="fn-k"><div class="l">Sobra depois dos impostos</div><div class="v">{_brl(rec - imp)}</div>'
                '<div class="s">antes dos outros custos</div></div>'
                '</div>', unsafe_allow_html=True)
    _sec("Mês a mês")
    h = ""
    for m, r, i in linhas[::-1]:
        h += (f'<div class="fn-row" style="margin-bottom:8px"><span class="ic {"ok" if i else "espera"}">'
              f'{_ic("ok" if i else "relogio")}</span><div class="t"><b>{MESES[m - 1].capitalize()}</b>'
              f'<span class="d">recebido {_brl(r)}</span></div><span class="v nt">{_brl(i)} de impostos</span></div>')
    st.markdown(h, unsafe_allow_html=True)
    st.caption("Use estes números com a sua contadora. Autônoma (pessoa física) paga o imposto de renda pelo "
               "Carnê-Leão todo mês; no Lucro Presumido, os impostos são calculados por ela.")
    lugar_grafico.markdown(_card_faturamento(mov, ano, hoje, [
        ("Média por mês", _brl(rec / ultimo if ultimo else 0)), ("Impostos pagos no ano", _brl(imp))]),
        unsafe_allow_html=True)


# ───────────────────────────── tela ─────────────────────────────

def show():
    from utils.auth_guard import require_auth
    require_auth()
    st.markdown(CSS, unsafe_allow_html=True)

    if "db" not in st.session_state:
        st.error("Erro: Conexão com banco de dados não inicializada")
        return

    st.session_state.setdefault("fin_selecionada", None)

    # Recarrega do banco apenas ao entrar na página (navegação); reruns por
    # interação de widget usam o cache (as mutações invalidam o cache no Database).
    entrou_na_pagina = st.session_state.get("_last_page_rendered") != "Financeiro"
    if entrou_na_pagina:
        _fechar_detalhes()

    try:
        financeiro_df = st.session_state.db.get_financeiro(force_reload=entrou_na_pagina)
    except Exception as e:
        st.warning(f"Erro ao carregar dados financeiros: {e}")
        financeiro_df = pd.DataFrame()
    if financeiro_df is None:
        financeiro_df = pd.DataFrame()

    required_cols = ['id', 'tipo', 'descricao', 'valor', 'data', 'status', 'categoria']
    if not financeiro_df.empty:
        for c in required_cols:
            if c not in financeiro_df.columns:
                financeiro_df[c] = None
        financeiro_df['data'] = pd.to_datetime(financeiro_df['data'], errors='coerce')
        financeiro_df = _dedup_transacoes(financeiro_df)

    regime = _regime()
    rotulo_imp = "Impostos e MEI" if regime["regime"] == "MEI" else "Impostos"
    rotulos = ["Lançamentos", rotulo_imp]
    # trocar o tipo de empresa muda o nome da aba: reabre a aba de impostos com o nome novo
    if st.session_state.pop("fin_abrir_impostos", False) or st.session_state.get("fin_abas") not in (None, *rotulos):
        st.session_state["fin_abas"] = rotulo_imp
    na_aba_lanc = st.session_state.get("fin_abas") in (None, "Lançamentos")
    _cabecalho(com_botoes=na_aba_lanc)
    # botão "+" da barra de baixo no celular (app.py) abre o novo lançamento
    if st.session_state.pop("fin_nova_transacao_open", False):
        _dialogo_lancamento("receita")

    aba_lanc, aba_imp = st.tabs(rotulos, key="fin_abas", on_change="rerun")
    if aba_imp.open:
        with aba_imp:
            _aba_impostos(financeiro_df, regime)
    else:
        with aba_lanc:
            _conteudo_lancamentos(financeiro_df, regime)

    selected_id = st.session_state.get("fin_selecionada")
    if selected_id is not None and not financeiro_df.empty:
        rows = financeiro_df[financeiro_df['id'] == selected_id]
        if not rows.empty:
            _modal_detalhes(rows.iloc[0], financeiro_df)
        else:
            st.session_state["fin_selecionada"] = None
