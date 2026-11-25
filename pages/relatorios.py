"""
Relatórios — análise de um período, sempre comparada com outro.

O Início mostra o mês de hoje e o Financeiro mostra um mês por vez. Aqui a organizadora escolhe um período
(mês, trimestre, ano ou datas livres) e vê como ele se saiu em relação ao período anterior ou ao mesmo período
do ano passado. Cada aba responde a uma pergunta do negócio:

- Resultado: quanto entrou, quanto custou e quanto sobrou (DRE simples, mês a mês)?
- Clientes: quem traz o dinheiro, de onde vêm e se voltam?
- Propostas: as propostas fecham? em quanto tempo? quais serviços fecham mais?
- Trabalhos: quais trabalhos deram lucro de verdade?
- Próximos meses: o que ainda vai entrar e sair, o que está atrasado e quais propostas aguardam resposta.

Boas práticas seguidas: números com definição visível, comparação com uma base (período anterior ou ano passado),
indicadores do que vem pela frente (a receber e propostas aguardando) em vez de projeções estatísticas, poucos
gráficos e exportação para Excel. Os cálculos ficam em utils/relatorios_calc.py (com testes).
"""
import html as html_module
import io
import re
from datetime import timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils import relatorios_calc as rc
from utils.currency_formatter import fmt_brl

NAVY, GOLD, VERDE, VERMELHO, CINZA = "#0D1B2A", "#C9A84C", "#067647", "#B42318", "#98A2B3"

CSS = """
<style>
.rl-eyebrow { font-size: .74rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: #9C7A22; margin: 0 0 4px; }
h1.rl-titulo { margin: 0 !important; padding: 0 !important; font-family: 'Cormorant Garamond', Georgia, serif !important;
               font-size: 2.75rem !important; font-weight: 600 !important; color: var(--navy) !important; line-height: 1.15 !important; }
h1.rl-titulo::after { content: ""; display: block; width: 40px; height: 3px; border-radius: 2px; background: var(--gold); margin-top: 8px; }
.rl-sub { color: #5B6B80; font-size: 1rem; margin: 12px 0 2px; }
.rl-per { color: #5B6B80; font-size: .84rem; margin: 2px 0 0; }
.rl-per b { color: var(--navy); }
.st-key-rl_acoes [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: nowrap !important; gap: 10px !important; }
.st-key-rl_acoes [data-testid="stColumn"] { min-width: 0 !important; width: auto !important; flex: 1 1 0 !important; }
.st-key-rl_acoes button { min-height: 48px !important; border-radius: 10px !important; width: 100% !important; }
.st-key-rl_acoes button p { font-weight: 700 !important; font-size: 1rem !important; white-space: nowrap; }
.st-key-rl_acoes [data-testid="stPopover"] button { background: #fff !important; border: 1px solid #E6E1D6 !important; }
.st-key-rl_acoes [data-testid="stPopover"] button, .st-key-rl_acoes [data-testid="stPopover"] button * { color: var(--navy) !important; }
.st-key-rl_acoes [data-testid="stDownloadButton"] button { background: var(--navy) !important; border-color: var(--navy) !important; }
.st-key-rl_acoes [data-testid="stDownloadButton"] button * { color: #fff !important; }

.st-key-rel_abas [role="tablist"] { background: #ECE7DC !important; border-radius: 14px !important; padding: 5px !important; margin: 14px 0 4px !important; }
.st-key-rel_abas [role="tab"] { padding: 9px 18px !important; border-radius: 10px !important; }
.st-key-rel_abas [role="tab"] p { font-size: 1rem !important; }
.st-key-rel_abas [role="tab"][aria-selected="true"] { border-color: transparent !important;
    box-shadow: inset 0 -3px 0 var(--gold), 0 1px 3px rgba(0,0,0,.08) !important; }

.rl-kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 6px 0 6px; }
.rl-kpi { background: #fff; border: 1px solid #E7E2D6; border-radius: 16px; padding: 16px 18px; min-width: 0; }
.rl-kpi .rot { font-size: .74rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: #5B6B80; display: block; }
.rl-kpi .val { font-size: 1.62rem; font-weight: 700; color: var(--navy); margin: 6px 0 2px; font-variant-numeric: tabular-nums;
               white-space: nowrap; overflow: hidden; text-overflow: ellipsis; line-height: 1.25; }
.rl-kpi .sub { font-size: .8rem; color: #5B6B80; line-height: 1.4; display: block; }
.rl-kpi.destaque { background: var(--navy); border-color: var(--navy); }
.rl-kpi.destaque .rot { color: var(--gold); }
.rl-kpi.destaque .sub { color: #C7CED8; }
.rl-kpi.destaque .val { color: #fff; }
.rl-d { font-weight: 600; }
.rl-d.up { color: #2F6B4F; } .rl-d.down { color: #9B2C2C; } .rl-d.neutro { color: #5B6B80; font-weight: 400; }
.rl-kpi.destaque .rl-d.up { color: #9FD8B5; } .rl-kpi.destaque .rl-d.down { color: #F4B3AA; } .rl-kpi.destaque .rl-d.neutro { color: #C7CED8; }
.rl-secao { font-size: .74rem; font-weight: 700; letter-spacing: .16em; text-transform: uppercase; color: #5B6B80; margin: 18px 0 8px; }
.rl-insight { background: #fff; border: 1px solid #E7E2D6; border-left: 3px solid var(--gold); border-radius: 12px;
              padding: 12px 16px; font-size: .9rem; color: #344054; margin: 4px 0 12px; line-height: 1.55; }
.rl-insight p { margin: 0 0 4px; } .rl-insight p:last-child { margin: 0; }
.rl-alerta { background: #FBE9E7; border: 1px solid #F3C9C2; border-radius: 12px; padding: 10px 14px; font-size: .88rem; color: #7A2620; margin: 0 0 12px; }
.rl-card { background: #fff; border: 1px solid #E7E2D6; border-radius: 16px; padding: 18px; margin-bottom: 14px; min-width: 0; }
.rl-card h4 { font-size: .98rem !important; font-weight: 700 !important; color: var(--navy) !important; margin: 0 0 10px !important; padding: 0 !important; }
.rl-li { display: flex; justify-content: space-between; gap: 10px; font-size: .9rem; padding: 9px 0; border-top: 1px solid #F0ECE3; }
.rl-li span { color: #5B6B80; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rl-li b { color: var(--navy); white-space: nowrap; font-variant-numeric: tabular-nums; }
.rl-cht { display: flex; align-items: flex-end; justify-content: center; gap: 10px; height: 200px; margin-top: 10px; padding: 0 4px; }
.rl-cht > div { flex: 1; display: flex; flex-direction: column; justify-content: flex-end; align-items: center; gap: 6px;
                font-size: .72rem; color: #5B6B80; min-width: 0; height: 100%; max-width: 140px; }
.rl-cht .par { display: flex; gap: 3px; align-items: flex-end; height: 170px; width: 100%; }
.rl-cht .par i { flex: 1; display: block; border-radius: 6px 6px 0 0; min-height: 2px; }
.rl-cht .par i.e { background: var(--gold); } .rl-cht .par i.g { background: #D8D2C4; }
.rl-leg { display: flex; gap: 16px; font-size: .84rem; color: #5B6B80; margin-top: 12px; }
.rl-leg i { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 6px; vertical-align: -1px; }
.rl-dre { width: 100%; border-collapse: collapse; font-size: .9rem; }
.rl-dre th { text-align: right; font-size: .72rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: #5B6B80;
             padding: 6px 10px; border-bottom: 1px solid #E7E2D6; }
.rl-dre th:first-child { text-align: left; }
.rl-dre td { padding: 8px 10px; border-bottom: 1px solid #F0ECE3; text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.rl-dre td:first-child { text-align: left; color: #344054; }
.rl-dre-wrap { overflow-x: auto; background: #fff; border: 1px solid #E7E2D6; border-radius: 16px; padding: 10px 12px; }
.rl-dre tr.tot td { font-weight: 700; color: var(--navy); border-top: 1px solid #D8D2C4; }
.rl-dre tr.sub td:first-child { padding-left: 22px; color: #5B6B80; }
.rl-cat { display: grid; grid-template-columns: minmax(0, 1.3fr) minmax(0, 1fr) auto; gap: 10px; align-items: center; padding: 6px 0; font-size: .88rem; }
.rl-cat .nm { color: #344054; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rl-cat .bar { height: 10px; background: #EFEBE2; border-radius: 6px; overflow: hidden; }
.rl-cat .bar i { display: block; height: 100%; border-radius: 6px; background: var(--gold); }
.rl-cat b { font-variant-numeric: tabular-nums; white-space: nowrap; color: var(--navy); }
.rl-vazio { color: #5B6B80; font-size: .88rem; }
.rl-def { font-size: .78rem; color: #5B6B80; margin-top: 8px; line-height: 1.5; }
@media (max-width: 1280px) {
  .rl-kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .st-key-rl_cab > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: wrap !important; }
  .st-key-rl_cab > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { flex: 1 1 100% !important; width: 100% !important; }
  .st-key-rl_acoes { max-width: 420px; margin-top: 12px; }
}
@media (max-width: 1280px) {
  .rl-lado { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); column-gap: 14px; align-items: start; }
  .st-key-rl_corpo > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: wrap !important; }
  .st-key-rl_corpo > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { flex: 1 1 100% !important; width: 100% !important; }
}
@media (max-width: 640px) {
  h1.rl-titulo { font-size: 2.2rem !important; }
  .rl-lado { grid-template-columns: 1fr; }
  .rl-kpis { gap: 10px; }
  .rl-kpi { padding: 14px; }
  .rl-kpi .val { font-size: 1.3rem; }
  .rl-cht { gap: 5px; }
  .st-key-rel_abas [role="tab"] { padding: 8px 12px !important; }
}
</style>
"""


def _hoje():
    from utils import visual
    return visual.hoje()


def _pct(v, casas=0):
    return "—" if v is None else f"{v * 100:.{casas}f}%".replace(".", ",")


_COMP = {"curto": None}   # "o período anterior" ou "o mesmo período do ano passado" (definido em show)


def _delta(atual, comp, rotulo_comp, inverso=False, pontos=False):
    """'▲ 12% que o período anterior' com cor (inverso=True quando subir é ruim, ex.: gastos)."""
    base = _COMP["curto"] or rotulo_comp
    if comp is None or atual is None:
        return '<span class="rl-d neutro">sem base para comparar</span>'
    if pontos:   # diferença de margem em pontos percentuais
        d = (atual - comp) * 100
        if abs(d) < 0.05:
            return f'<span class="rl-d neutro">igual a {base}</span>'
        cls = "up" if (d > 0) != inverso else "down"
        return (f'<span class="rl-d {cls}">{"▲" if d > 0 else "▼"} {abs(d):.1f} p.p.</span>'.replace(".", ",", 1)
                + f' que {base}')
    v = rc.variacao(atual, comp)
    if v is None:
        return '<span class="rl-d neutro">sem base para comparar</span>'
    if abs(v) < 0.005:
        return f'<span class="rl-d neutro">igual a {base}</span>'
    cls = "up" if (v > 0) != inverso else "down"
    return f'<span class="rl-d {cls}">{"▲" if v > 0 else "▼"} {_pct(abs(v))}</span> que {base}'


def _kpi(rotulo, valor, sub, cls=""):
    return (f'<div class="rl-kpi {cls}"><span class="rot">{rotulo}</span>'
            f'<div class="val">{valor}</div><span class="sub">{sub}</span></div>')


def _kpis(*cards):
    st.markdown('<div class="rl-kpis">' + "".join(cards) + '</div>', unsafe_allow_html=True)


def _secao(txt):
    st.markdown(f'<div class="rl-secao">{txt}</div>', unsafe_allow_html=True)


def _insight(frases):
    if frases:
        st.markdown('<div class="rl-insight">' + "".join(f"<p>{html_module.escape(f)}</p>" for f in frases) + '</div>',
                    unsafe_allow_html=True)


def _barras(df):
    if df.empty:
        return '<div class="rl-vazio">Nada neste período.</div>'
    topo = float(df["valor"].iloc[0]) or 1
    h = ""
    for nome, valor in zip(df["categoria"].head(8), df["valor"].head(8)):
        nome_h = html_module.escape(str(nome))
        h += (f'<div class="rl-cat"><span class="nm" title="{nome_h}">{nome_h}</span>'
              f'<span class="bar"><i style="width:{max(valor / topo * 100, 1.5):.0f}%"></i></span>'
              f'<b>{fmt_brl(valor)}</b></div>')
    return h


def _brl(v):
    s = fmt_brl(v)
    return s[:-3] if s.endswith(",00") else s


def _grafico_entrou_gastou(serie):
    if serie.empty:
        return '<div class="rl-vazio">Nada neste período.</div>'
    gasto = serie["custos"] + serie["despesas"]
    topo = max(float(serie["faturamento"].max()), float(gasto.max())) or 1
    barras = ""
    for mes, e, g in zip(serie["mes"], serie["faturamento"], gasto):
        barras += (f'<div title="{mes}: entrou {fmt_brl(e)} · gastou {fmt_brl(g)}"><span class="par">'
                   f'<i class="e" style="height:{e / topo * 160:.0f}px"></i><i class="g" style="height:{g / topo * 160:.0f}px"></i>'
                   f'</span>{mes.split("/")[0] if len(serie) <= 12 else mes}</div>')
    return (f'<div class="rl-cht">{barras}</div><div class="rl-leg"><span><i style="background:var(--gold)"></i>'
            '<span style="color:#9C7A22">entrou</span></span><span><i style="background:#D8D2C4"></i>gastou</span></div>')


def _layout(fig, altura=320):
    fig.update_layout(template="plotly_white", height=altura, margin=dict(l=8, r=8, t=10, b=8), separators=",.",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0), hovermode="x unified",
                      font=dict(family="Inter, sans-serif", size=12, color="#344054"))
    fig.update_yaxes(gridcolor="#F2F4F7", zeroline=True, zerolinecolor="#D0D5DD", tickprefix="R$ ")
    return fig


def _tabela(df, moeda=(), pct=(), renomear=None, altura=None):
    d = df.copy()
    for c in moeda:
        if c in d:
            d[c] = d[c].apply(lambda v: "—" if v is None or pd.isna(v) else fmt_brl(v))
    for c in pct:
        if c in d:
            d[c] = d[c].apply(lambda v: _pct(v) if v is not None and not pd.isna(v) else "—")
    if renomear:
        d = d.rename(columns=renomear)[list(renomear.values())]
    kw = {"height": altura} if altura else {}
    st.dataframe(d, hide_index=True, use_container_width=True, **kw)


# ───────────────────────────── dados ─────────────────────────────

def _carregar():
    db = st.session_state.db
    fin = db.get_financeiro()
    # get_financeiro() traz no máximo 1.000 transações (e guarda em cache): para um ano inteiro pode faltar dado
    if fin is not None and len(fin) >= 1000:
        fin = db.get_financeiro(limit=200000, force_reload=True)
    try:
        propostas = db.get_propostas()
    except Exception:
        propostas = pd.DataFrame()
    try:
        clientes = db.get_clientes()
    except Exception:
        clientes = pd.DataFrame()
    fin = fin if fin is not None else pd.DataFrame()
    return rc.movimentos_rel(fin), propostas, clientes


# ───────────────────────────── abas ─────────────────────────────

def _aba_resultado(mov, propostas, clientes, ini, fim, cini, cfim, rot, rot_comp, exp):
    a, c = rc.resultado(mov, ini, fim), rc.resultado(mov, cini, cfim)
    cat_e, cat_s = rc.por_categoria(mov, ini, fim, "entra"), rc.por_categoria(mov, ini, fim, "sai")
    cat_s_comp = rc.por_categoria(mov, cini, cfim, "sai")
    pr = rc.propostas_periodo(propostas, ini, fim)
    cl = rc.clientes_periodo(propostas, clientes, ini, fim)
    if not a["faturamento"] and not (a["custos"] + a["despesas"]):
        st.info("Nenhum recebimento ou pagamento registrado neste período. Marque as receitas como Recebido e as despesas "
                "como Pago no Financeiro para elas aparecerem aqui.")
    decididas = pr["fechadas"] + pr["recusadas"]
    voltam_n = int(round((cl["recompra"] or 0) * cl["clientes_base"]))
    cards = [
        ("Lucro", fmt_brl(a["lucro"]), f'margem de {_pct(a["margem"])}' if a["margem"] is not None else "lucro ÷ faturamento"),
        ("Faturamento", fmt_brl(a["faturamento"]), _delta(a["faturamento"], c["faturamento"], rot_comp)),
        ("Taxa de fechamento", _pct(pr["conversao"]),
         f'{pr["fechadas"]} de {decididas} propostas' if decididas else "nenhuma proposta respondida"),
        ("Clientes que voltam", _pct(cl["recompra"]),
         f'{voltam_n} de {cl["clientes_base"]}' if cl["clientes_base"] else "nenhum trabalho fechado ainda"),
    ]
    _kpis(*[_kpi(r, v, sub, "destaque" if i == 0 else "") for i, (r, v, sub) in enumerate(cards)])
    exp["_resumo"] = [(r, v, re.sub(r"<[^>]+>", "", sub).replace("▲ ", "+").replace("▼ ", "−")) for r, v, sub in cards] + [
        ("Gastos da empresa", fmt_brl(a["custos"] + a["despesas"]), "sem as retiradas"),
        ("Retiradas", fmt_brl(a["retiradas"]), "pró-labore"),
        ("Propostas feitas", str(pr["enviadas"]), fmt_brl(pr["valor_enviado"])),
        ("Clientes atendidas", str(cl["atendidas"]), f'{cl["novas"]} novas · {cl["voltaram"]} voltaram')]

    serie = rc.serie_mensal(mov, ini, fim)
    tipos = rc.propostas_por_tipo(propostas, ini, fim)
    origem = cl["origem"]
    corpo = st.container(key="rl_corpo")
    c_g, c_l = corpo.columns([1.9, 1], gap="medium")
    with c_g:
        st.markdown(f'<div class="rl-card"><h4>Entrou × gastou por mês</h4>{_grafico_entrou_gastou(serie)}</div>',
                    unsafe_allow_html=True)
    with c_l:
        h = '<div class="rl-lado"><div class="rl-card"><h4>Onde você ganha mais</h4>'
        t = tipos[tipos["ticket"].notna()].sort_values("ticket", ascending=False) if not tipos.empty else tipos
        if t.empty:
            h += '<div class="rl-vazio">Nenhum trabalho fechado neste período.</div>'
        for _, r in t.head(4).iterrows():
            h += (f'<div class="rl-li"><span title="{html_module.escape(str(r["tipo"]))}">{html_module.escape(str(r["tipo"]))}</span>'
                  f'<b>{_brl(r["ticket"])} por trabalho</b></div>')
        h += '</div><div class="rl-card"><h4>De onde vêm as clientes</h4>'
        if origem.empty:
            h += '<div class="rl-vazio">Nenhuma cliente atendida neste período.</div>'
        else:
            o = origem.assign(origem=origem["origem"].replace({"Cliente": "Indicação"}))
            o = o.groupby("origem", as_index=False)["clientes"].sum().sort_values("clientes", ascending=False)
            tot = float(o["clientes"].sum()) or 1
            for _, r in o.head(5).iterrows():
                h += (f'<div class="rl-li"><span>{html_module.escape(str(r["origem"]))}</span>'
                      f'<b>{r["clientes"] / tot:.0%}</b></div>')
        st.markdown(h + '</div></div>', unsafe_allow_html=True)

    _insight(rc.destaques(a, c, cat_s, cat_s_comp, rot_comp))

    # demonstrativo em largura total; categorias lado a lado embaixo
    if True:
        _secao("Demonstrativo do resultado")
        linhas = [("Faturamento", "faturamento", ""), ("(−) Custos diretos", "custos", "sub"),
                  ("= Margem bruta", "margem_bruta", "tot"), ("(−) Despesas fixas", "despesas", "sub"),
                  ("= Lucro", "lucro", "tot"), ("(−) Retiradas", "retiradas", "sub"),
                  ("= Ficou na empresa", "caixa", "tot")]
        h = (f'<div class="rl-dre-wrap"><table class="rl-dre"><tr><th></th><th>{html_module.escape(rot)}</th>'
             f'<th>{html_module.escape(rot_comp)}</th><th>Variação</th></tr>')
        for nome_linha, k, cls in linhas:
            v = rc.variacao(a[k], c[k])
            h += (f'<tr class="{cls}"><td>{nome_linha}</td><td>{fmt_brl(a[k])}</td><td>{fmt_brl(c[k])}</td>'
                  f'<td>{"—" if v is None else "0%" if abs(v) < 0.005 else ("+" if v > 0 else "−") + _pct(abs(v))}</td></tr>')
        h += (f'<tr><td>Margem de lucro</td><td>{_pct(a["margem"], 1)}</td><td>{_pct(c["margem"], 1)}</td><td></td></tr></table></div>'
              '<div class="rl-def">Regime de caixa: cada valor conta na data em que entrou ou saiu. Custos diretos são as '
              'despesas ligadas a um trabalho (assistente, equipe, fornecedor, comissão, material ou lançadas na proposta).</div>')
        st.markdown(h, unsafe_allow_html=True)
    col_e, col_s = st.columns(2, gap="medium")
    with col_e:
        st.markdown(f'<div class="rl-card" style="margin-top:14px"><h4>De onde veio</h4>{_barras(cat_e)}</div>',
                    unsafe_allow_html=True)
    with col_s:
        st.markdown(f'<div class="rl-card" style="margin-top:14px"><h4>Para onde foi</h4>{_barras(cat_s)}</div>',
                    unsafe_allow_html=True)

    exp["Resultado mês a mês"] = serie.drop(columns=["ano", "m"]).rename(columns={
        "mes": "Mês", "faturamento": "Faturamento", "custos": "Custos diretos", "despesas": "Despesas",
        "lucro": "Lucro", "retiradas": "Retiradas"})
    exp["Demonstrativo"] = pd.DataFrame([{"Linha": r, rot: a[k], rot_comp: c[k]} for r, k, _ in linhas])
    exp["Receitas por categoria"] = cat_e.rename(columns={"categoria": "Categoria", "valor": "Valor"})
    exp["Gastos por categoria"] = cat_s.rename(columns={"categoria": "Categoria", "valor": "Valor"})


def _aba_clientes(propostas, clientes, ini, fim, cini, cfim, rot_comp, exp):
    a = rc.clientes_periodo(propostas, clientes, ini, fim)
    c = rc.clientes_periodo(propostas, clientes, cini, cfim)
    if not a["origem"].empty:   # no cadastro "Cliente" quer dizer indicação de outra cliente
        a["origem"] = a["origem"].assign(origem=a["origem"]["origem"].replace({"Cliente": "Indicação de cliente"}))
    if not a["atendidas"]:
        st.info("Nenhum trabalho fechado neste período. Os clientes aparecem aqui quando uma proposta é aprovada.")
    _kpis(
        _kpi("Clientes que voltam", _pct(a["recompra"]),
             f'de {a["clientes_base"]} clientes, as que fecharam 2 ou mais trabalhos', "destaque"),
        _kpi("Clientes atendidas", str(a["atendidas"]),
             f'{a["novas"]} nova{"s" if a["novas"] != 1 else ""} · {a["voltaram"]} voltaram · '
             + _delta(a["atendidas"], c["atendidas"] or None, rot_comp)),
        _kpi("Valor por cliente", fmt_brl(a["valor_por_cliente"]) if a["valor_por_cliente"] else "—",
             _delta(a["valor_por_cliente"], c["valor_por_cliente"], rot_comp)),
        _kpi("Dependência das 3 maiores", _pct(a["concentracao_top3"]), "do valor fechado no período"),
    )
    frases = []
    if a["atendidas"] and a["voltaram"] == 0 and a["novas"]:
        frases.append("Todo o período veio de clientes novas. Ofereça manutenção ou um segundo ambiente para quem já foi "
                      "atendida: vender para quem já confia em você custa menos do que conquistar uma cliente nova.")
    if a["concentracao_top3"] and a["concentracao_top3"] >= 0.6 and a["atendidas"] > 3:
        frases.append(f"As 3 maiores clientes respondem por {_pct(a['concentracao_top3'])} do valor: se uma delas parar, "
                      "o faturamento sente muito.")
    if not a["origem"].empty:
        o = a["origem"].iloc[0]
        frases.append(f"O canal que mais trouxe dinheiro foi {o['origem']}: {fmt_brl(o['valor'])} em {int(o['trabalhos'])} "
                      f"trabalho{'s' if o['trabalhos'] != 1 else ''}.")
    _insight(frases)
    c1, c2 = st.columns([1, 1], gap="large")
    with c1:
        _secao("De onde vêm as clientes")
        if a["origem"].empty:
            st.markdown('<div class="rl-vazio">Nada neste período.</div>', unsafe_allow_html=True)
        else:
            _tabela(a["origem"], moeda=["valor"], renomear={"origem": "Origem", "clientes": "Clientes",
                                                             "trabalhos": "Trabalhos", "valor": "Valor fechado"})
    with c2:
        _secao("Clientes que mais fecharam")
        if a["ranking"].empty:
            st.markdown('<div class="rl-vazio">Nada neste período.</div>', unsafe_allow_html=True)
        else:
            r = a["ranking"].assign(primeira_vez=a["ranking"]["primeira_vez"].map({True: "Nova", False: "Voltou"}))
            _tabela(r.head(15), moeda=["valor"], renomear={"cliente": "Cliente", "trabalhos": "Trabalhos",
                                                            "valor": "Valor fechado", "primeira_vez": ""})
    st.markdown('<div class="rl-def">Conta o valor das propostas aprovadas no período (data da aprovação). '
                '“Clientes que voltam” olha todo o histórico até o fim do período. A origem vem do cadastro da cliente.</div>',
                unsafe_allow_html=True)
    exp["Clientes"] = a["ranking"].rename(columns={"cliente": "Cliente", "trabalhos": "Trabalhos", "valor": "Valor fechado",
                                                    "primeira_vez": "Primeira vez no período"})
    exp["Origem das clientes"] = a["origem"].rename(columns={"origem": "Origem", "clientes": "Clientes",
                                                             "trabalhos": "Trabalhos", "valor": "Valor fechado"})


def _aba_propostas(propostas, ini, fim, cini, cfim, rot_comp, exp):
    a, c = rc.propostas_periodo(propostas, ini, fim), rc.propostas_periodo(propostas, cini, cfim)
    if not a["enviadas"]:
        st.info("Nenhuma proposta feita neste período.")
    _kpis(
        _kpi("Taxa de fechamento", _pct(a["conversao"]),
             (_delta(a["conversao"], c["conversao"], rot_comp, pontos=True) if a["conversao"] is not None and c["conversao"] is not None
              else f'{a["fechadas"]} fechadas · {a["recusadas"]} recusadas'), "destaque"),
        _kpi("Propostas feitas", str(a["enviadas"]),
             f'{fmt_brl(a["valor_enviado"])} · ' + _delta(a["enviadas"], c["enviadas"] or None, rot_comp)),
        _kpi("Fechamento em valor", _pct(a["conversao_valor"]),
             f'{fmt_brl(a["valor_fechado"])} fechados de {fmt_brl(a["valor_fechado"] + a["valor_recusado"])} respondidos'),
        _kpi("Tempo para fechar", "—" if a["dias_para_fechar"] is None else f'{a["dias_para_fechar"]:.0f} dias',
             "mediana, da proposta à aprovação"),
    )
    frases = []
    if a["ticket_fechado"] and a["ticket_recusado"] and a["ticket_recusado"] > a["ticket_fechado"] * 1.3:
        frases.append(f"As propostas recusadas custavam em média {fmt_brl(a['ticket_recusado'])}, contra "
                      f"{fmt_brl(a['ticket_fechado'])} das fechadas. Vale oferecer opções em etapas ou por ambiente.")
    if a["conversao"] is not None and a["conversao_valor"] is not None and a["conversao_valor"] < a["conversao"] - 0.15:
        frases.append("Você fecha mais propostas pequenas do que grandes: a taxa em valor está bem abaixo da taxa em quantidade.")
    if a["aguardando"]:
        frases.append(f"{a['aguardando']} proposta{'s' if a['aguardando'] != 1 else ''} deste período ainda "
                      f"aguarda{'m' if a['aguardando'] != 1 else ''} resposta ({fmt_brl(a['valor_aguardando'])}). "
                      "Veja a lista em Próximos meses.")
    _insight(frases)
    mens = rc.propostas_mensal(propostas, ini, fim)
    if len(mens) > 1 and mens["enviadas"].sum():
        _secao("Propostas por mês")
        fig = go.Figure()
        fig.add_bar(x=mens["mes"], y=mens["enviadas"], name="Feitas", marker_color="#D8D2C4")
        fig.add_bar(x=mens["mes"], y=mens["fechadas"], name="Fechadas", marker_color=GOLD)
        fig.add_bar(x=mens["mes"], y=mens["recusadas"], name="Recusadas", marker_color="#9A9486")
        fig.update_layout(barmode="group", bargap=0.3)
        fig = _layout(fig, 280)
        fig.update_yaxes(tickprefix="")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    _secao("Por tipo de serviço")
    tipos = rc.propostas_por_tipo(propostas, ini, fim)
    if tipos.empty:
        st.markdown('<div class="rl-vazio">Nada neste período.</div>', unsafe_allow_html=True)
    else:
        _tabela(tipos, moeda=["valor_fechado", "ticket"], pct=["conversao"],
                renomear={"tipo": "Serviço", "enviadas": "Feitas", "fechadas": "Fechadas", "recusadas": "Recusadas",
                          "conversao": "Fechamento", "valor_fechado": "Valor fechado", "ticket": "Ticket médio"})
    st.markdown('<div class="rl-def">Considera as propostas feitas no período. Taxa de fechamento = fechadas ÷ (fechadas + recusadas): '
                'as que ainda aguardam resposta não entram na conta.</div>', unsafe_allow_html=True)
    exp["Propostas por tipo"] = tipos
    exp["Propostas por mês"] = mens


def _aba_trabalhos(mov, propostas, ini, fim, exp):
    t = rc.lucro_por_trabalho(mov, propostas, ini, fim)
    if t.empty:
        st.info("Nenhum trabalho fechado neste período.")
        return
    com_custo = t[t["custos"] > 0]
    receb = float(t["recebido"].sum())
    _kpis(
        _kpi("Lucro dos trabalhos", fmt_brl(t["lucro"].sum()), "recebido − custos ligados ao trabalho", "destaque"),
        _kpi("Trabalhos fechados", str(len(t)), f'{fmt_brl(t["valor"].sum())} contratados'),
        _kpi("Já recebido", fmt_brl(receb), f'{_pct(receb / t["valor"].sum() if t["valor"].sum() else None)} do contratado'),
        _kpi("Margem média", _pct(t["lucro"].sum() / receb if receb else None, 1),
             f'{len(com_custo)} de {len(t)} com custos lançados'),
    )
    frases = []
    baixa = t[(t["margem"].notna()) & (t["margem"] < 0.3)]
    if len(baixa):
        frases.append(f"{len(baixa)} trabalho{'s' if len(baixa) != 1 else ''} com margem abaixo de 30%. "
                      "Confira o preço desses serviços ou os custos com equipe e material.")
    if len(com_custo) < len(t):
        frases.append("Para o lucro por trabalho ficar certo, lance as despesas (assistente, material, fornecedor) "
                      "dentro da proposta no Financeiro.")
    _insight(frases)
    _tabela(t, moeda=["valor", "recebido", "custos", "lucro"], pct=["margem"],
            renomear={"numero": "Proposta", "cliente": "Cliente", "tipo": "Serviço", "valor": "Contratado",
                      "recebido": "Recebido", "custos": "Custos", "lucro": "Lucro", "margem": "Margem"})
    exp["Lucro por trabalho"] = t


def _aba_futuro(mov, propostas, hoje, exp):
    faixas, atrasados = rc.agenda_pendente(mov, hoje)
    # taxa de fechamento dos últimos 12 meses, para estimar quanto das propostas em aberto deve virar trabalho
    hist = rc.propostas_periodo(propostas, hoje - timedelta(days=365), hoje)
    ag = rc.propostas_aguardando(propostas, hoje)
    rec30 = float(faixas.loc[faixas["faixa"].isin(["Atrasado", "Até 30 dias"]), "a_receber"].sum())
    pag30 = float(faixas.loc[faixas["faixa"].isin(["Atrasado", "Até 30 dias"]), "a_pagar"].sum())
    v_ag = float(ag["valor"].sum()) if not ag.empty else 0.0
    esperado = v_ag * hist["conversao"] if hist["conversao"] is not None else None
    _kpis(
        _kpi("Saldo dos próximos 30 dias", fmt_brl(rec30 - pag30), "a receber − a pagar", "destaque"),
        _kpi("A receber em 30 dias", fmt_brl(rec30), "inclui os atrasados"),
        _kpi("A pagar em 30 dias", fmt_brl(pag30), "inclui os atrasados"),
        _kpi("Propostas aguardando", fmt_brl(v_ag),
             f'{len(ag)} em aberto' + (f' · devem virar ~{fmt_brl(esperado)}' if esperado else "")),
    )
    atr_rec = atrasados[atrasados["lado"] == "entra"] if not atrasados.empty else atrasados
    if not atr_rec.empty:
        st.markdown(f'<div class="rl-alerta"><b>{len(atr_rec)} recebimento{"s" if len(atr_rec) != 1 else ""} atrasado'
                    f'{"s" if len(atr_rec) != 1 else ""}</b>, somando {fmt_brl(atr_rec["valor"].sum())}. Cobre pelo WhatsApp '
                    'ou, se já recebeu, marque como Recebido no Financeiro.</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1], gap="large")
    with c1:
        _secao("Agenda de recebimentos e pagamentos")
        f = faixas[(faixas["a_receber"] > 0) | (faixas["a_pagar"] > 0)].assign(saldo=lambda d: d["a_receber"] - d["a_pagar"])
        if f.empty:
            st.markdown('<div class="rl-vazio">Nada pendente.</div>', unsafe_allow_html=True)
        else:
            _tabela(f, moeda=["a_receber", "a_pagar", "saldo"],
                    renomear={"faixa": "Vencimento", "a_receber": "A receber", "a_pagar": "A pagar", "saldo": "Saldo"})
        if not atrasados.empty:
            _secao("Atrasados")
            d = atrasados.assign(tipo=atrasados["lado"].map({"entra": "Receber", "sai": "Pagar"}),
                                 venc=atrasados["d"].apply(lambda x: x.strftime("%d/%m/%Y") if x else "—"),
                                 dias=atrasados["d"].apply(lambda x: (hoje - x).days if x else None))
            _tabela(d, moeda=["valor"], renomear={"tipo": "", "descricao": "Descrição", "venc": "Venceu em",
                                                   "dias": "Dias", "valor": "Valor"})
    with c2:
        _secao("Propostas aguardando resposta")
        if ag.empty:
            st.markdown('<div class="rl-vazio">Nenhuma proposta em aberto.</div>', unsafe_allow_html=True)
        else:
            _tabela(ag, moeda=["valor"], renomear={"numero": "Proposta", "cliente": "Cliente", "valor": "Valor", "dias": "Dias parada"})
            paradas, velhas = ag[ag["dias"].fillna(0) > 7], ag[ag["dias"].fillna(0) > 60]
            if len(paradas):
                st.caption(f"{len(paradas)} sem resposta há mais de 7 dias: um lembrete simples costuma destravar a decisão."
                           + (f" {len(velhas)} estão paradas há mais de 60 dias e dificilmente vão fechar: marque-as como recusadas "
                              "nas Propostas para a taxa de fechamento e esta previsão ficarem certas." if len(velhas) else ""))
    st.markdown('<div class="rl-def">Pela data de vencimento das receitas e despesas pendentes. A estimativa das propostas usa a '
                'taxa de fechamento dos últimos 12 meses.</div>', unsafe_allow_html=True)
    exp["A receber e a pagar"] = faixas.rename(columns={"faixa": "Vencimento", "a_receber": "A receber", "a_pagar": "A pagar"})
    exp["Propostas aguardando"] = ag


# Excel já formatado: cabeçalho nas cores da marca, R$ e % nas colunas certas, larguras ajustadas,
# cabeçalho fixo e filtro em cada aba. As colunas são reconhecidas pelo nome.
_XL_NOMES = {"valor": "Valor", "valor_fechado": "Valor fechado", "ticket": "Ticket médio", "conversao": "Conversão",
             "margem": "Margem", "custos": "Custos", "lucro": "Lucro", "recebido": "Recebido", "dias": "Dias parada",
             "numero": "Proposta", "cliente": "Cliente", "tipo": "Tipo", "mes": "Mês", "enviadas": "Enviadas",
             "fechadas": "Fechadas", "recusadas": "Recusadas", "em_aberto": "Em aberto", "categoria": "Categoria"}
_XL_PCT = ("conversão", "margem", "taxa", "%")
_XL_INTEIRO = ("trabalhos", "clientes", "enviadas", "fechadas", "recusadas", "em aberto", "dias", "qtd")


def _xl_formato(coluna, serie):
    """Formato numérico do Excel pela coluna: %, inteiro ou R$ (o resto dos números é dinheiro)."""
    if not pd.api.types.is_numeric_dtype(serie) or pd.api.types.is_bool_dtype(serie):
        return None
    nome = str(coluna).lower()
    if any(k in nome for k in _XL_PCT):
        return "0.0%"
    if "proposta" in nome:
        return "0"
    if any(k in nome for k in _XL_INTEIRO):
        return "#,##0"
    return '"R$" #,##0.00;[Red]-"R$" #,##0.00'


def _agora_txt():
    from utils import visual
    return visual.agora().strftime("%d/%m/%Y %H:%M")


def _excel(exp, titulo):
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
    navy, dourado, creme = "0D1B2A", "C9A84C", "F8F6F1"
    fino = Side(style="thin", color="E4E7EC")
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        try:
            from pages.perfil import carregar_perfil
            perfil = carregar_perfil() or {}
        except Exception:
            perfil = {}
        conta = perfil.get("empresa") or perfil.get("nome") or ""
        sobre = pd.DataFrame({"": ["Relatório", "Conta", "Gerado em", "Abas"],
                              " ": [titulo, conta, _agora_txt(),
                                    ", ".join(n for n, df in exp.items() if isinstance(df, pd.DataFrame) and not df.empty)]})
        sobre.to_excel(xw, sheet_name="Sobre", index=False, header=False, startrow=2)
        ws = xw.sheets["Sobre"]
        ws["A1"] = "Planner Organiza"
        ws["A1"].font = Font(bold=True, size=16, color=navy)
        for r in range(3, 7):
            ws.cell(r, 1).font = Font(bold=True, color="667085")
        ws.column_dimensions["A"].width, ws.column_dimensions["B"].width = 14, 60
        ws["B6"].alignment = Alignment(wrap_text=True, vertical="top")
        ws.sheet_view.showGridLines = False

        for nome, df in exp.items():
            if not isinstance(df, pd.DataFrame) or df.empty:
                continue
            df = df.rename(columns=lambda c: _XL_NOMES.get(c, str(c).replace("_", " ").capitalize()
                                                            if "_" in str(c) else c))
            aba = nome[:31]
            df.to_excel(xw, sheet_name=aba, index=False, startrow=2)
            ws = xw.sheets[aba]
            ncol, nlin = len(df.columns), len(df) + 3
            ws["A1"] = nome
            ws["A1"].font = Font(bold=True, size=14, color=navy)
            ws["A2"] = titulo
            ws["A2"].font = Font(italic=True, size=9, color="667085")
            for j, col in enumerate(df.columns, 1):
                h = ws.cell(3, j)
                h.font, h.fill = Font(bold=True, color="FFFFFF"), PatternFill("solid", fgColor=navy)
                h.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                h.border = Border(bottom=Side(style="medium", color=dourado))
                fmt = _xl_formato(col, df[col])
                largura = len(str(col))
                for i in range(4, nlin + 1):
                    c = ws.cell(i, j)
                    if isinstance(c.value, str) and c.value.startswith("="):
                        c.data_type = "s"  # "= Lucro" é texto, não fórmula (antes aparecia #NAME?)
                    c.border = Border(bottom=fino)
                    if fmt:
                        c.number_format = fmt
                    elif hasattr(c.value, "year"):
                        c.number_format = "DD/MM/YYYY"
                    if i % 2 == 1:
                        c.fill = PatternFill("solid", fgColor=creme)
                    largura = max(largura, len(f"{c.value:,.2f}") + 4 if isinstance(c.value, (int, float)) and fmt
                                  else len(str(c.value or "")))
                ws.column_dimensions[get_column_letter(j)].width = min(max(largura + 2, 10), 50)
            ws.row_dimensions[3].height = 22
            ws.freeze_panes = "A4"
            ws.auto_filter.ref = f"A3:{get_column_letter(ncol)}{nlin}"
            ws.sheet_view.showGridLines = False
    return buf.getvalue()


def _df_texto(df):
    """Tabela pronta para o PDF: mesmos nomes de coluna e formatos (R$, %, inteiro, data) do Excel, como texto."""
    d = df.rename(columns=lambda c: _XL_NOMES.get(c, str(c).replace("_", " ").capitalize() if "_" in str(c) else c))
    out = pd.DataFrame(index=d.index)
    for col in d.columns:
        serie = d[col]
        if pd.api.types.is_bool_dtype(serie):
            out[col] = serie.map({True: "Sim", False: "Não"})
            continue
        fmt = _xl_formato(col, serie)

        def f(v, fmt=fmt):
            if v is None or (isinstance(v, float) and pd.isna(v)):
                return ""
            if hasattr(v, "strftime"):
                return v.strftime("%d/%m/%Y")
            if fmt == "0.0%":
                return _pct(v, 1)
            if fmt in ("0", "#,##0"):
                return f"{v:,.0f}".replace(",", ".")
            if fmt:
                return fmt_brl(v)
            return str(v)
        out[col] = serie.apply(f)
    return out


def _pdf(exp, titulo, periodo):
    from utils.relatorio_pdf import gerar_pdf
    try:
        from pages.perfil import carregar_perfil
        perfil = carregar_perfil() or {}
    except Exception:
        perfil = {}
    conta = perfil.get("empresa") or perfil.get("nome") or ""
    tabelas = {n: _df_texto(df) for n, df in exp.items() if isinstance(df, pd.DataFrame) and not df.empty}
    return gerar_pdf(titulo, periodo, conta, exp.get("_resumo", []), tabelas)


def show():
    from utils.auth_guard import require_auth
    require_auth()
    st.markdown(CSS, unsafe_allow_html=True)
    hoje = _hoje()

    c_tit, c_btn = st.container(key="rl_cab").columns([2.7, 1.9], vertical_alignment="bottom")
    c_tit.markdown('<div class="rl-eyebrow">Como o seu negócio está indo</div><h1 class="rl-titulo">Relatórios</h1>'
                   '<div class="rl-sub">Os números que ajudam a decidir: onde ganha mais, quem volta e o que vem por aí.</div>',
                   unsafe_allow_html=True)
    with c_btn, st.container(key="rl_acoes"):
        b_per, b_pdf = st.columns([1.35, 1])
        with b_per.popover(st.session_state.get("rel_periodo") or "Últimos 6 meses", key="rel_pop", use_container_width=True):
            preset = st.selectbox("Período", rc.PERIODOS, index=rc.PERIODOS.index("Últimos 6 meses"), key="rel_periodo")
            ini_c = fim_c = None
            if preset == "Personalizado":
                datas = st.date_input("Datas", value=(hoje.replace(day=1), hoje), format="DD/MM/YYYY", key="rel_datas")
                if isinstance(datas, (list, tuple)) and len(datas) == 2:
                    ini_c, fim_c = datas
            comparar = st.selectbox("Comparar com", ["Período anterior", "Mesmo período do ano passado"], key="rel_comp")
        lugar_pdf = b_pdf.empty()
    if preset == "Personalizado" and ini_c is None:
        st.caption("Escolha a data inicial e a final no seletor de período.")
        return
    ini, fim = rc.intervalo(preset, hoje, ini_c, fim_c)
    cini, cfim = rc.periodo_anterior(ini, fim) if comparar == "Período anterior" else rc.mesmo_periodo_ano_passado(ini, fim)
    _COMP["curto"] = "o período anterior" if comparar == "Período anterior" else "o mesmo período do ano passado"
    rot, rot_comp = rc.rotulo_periodo(ini, fim), rc.rotulo_periodo(cini, cfim)
    # período em andamento: compara até hoje com o mesmo número de dias do outro período
    ini, fim, cini, cfim, cortado = rc.ate_hoje(ini, fim, cini, cfim, hoje)
    if cortado:
        rot, rot_comp = f"{rot} até {fim:%d/%m}", f"{rot_comp} até {cfim:%d/%m}"
    c_tit.markdown(f'<div class="rl-per"><b>{html_module.escape(rot)}</b> · comparado com {html_module.escape(rot_comp)}</div>',
                   unsafe_allow_html=True)

    try:
        mov, propostas, clientes = _carregar()
    except Exception as e:
        st.error(f"Não consegui carregar os dados: {e}")
        return

    exp = {}
    abas = st.tabs(["Resultado", "Clientes", "Propostas", "Trabalhos", "Próximos meses"], key="rel_abas")
    with abas[0]:
        _aba_resultado(mov, propostas, clientes, ini, fim, cini, cfim, rot, rot_comp, exp)
    with abas[1]:
        _aba_clientes(propostas, clientes, ini, fim, cini, cfim, rot_comp, exp)
    with abas[2]:
        _aba_propostas(propostas, ini, fim, cini, cfim, rot_comp, exp)
    with abas[3]:
        _aba_trabalhos(mov, propostas, ini, fim, exp)
    with abas[4]:
        _aba_futuro(mov, propostas, hoje, exp)

    titulo = f"Relatório {rot} (comparado com {rot_comp})"
    try:
        lugar_pdf.download_button("Baixar PDF", data=_pdf(exp, "Relatório do negócio", f"{rot} · comparado com {rot_comp}"),
                                  file_name=f"relatorio_{ini:%Y-%m-%d}_{fim:%Y-%m-%d}.pdf", mime="application/pdf",
                                  type="primary", key="rel_pdf", use_container_width=True)
    except Exception as e:
        print(f"[relatorios] pdf: {e}")
        lugar_pdf.caption("Não foi possível gerar o PDF agora.")

    st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
    try:
        st.download_button("Baixar em Excel", data=_excel(exp, titulo), icon=":material/table_view:",
                           file_name=f"relatorio_{ini:%Y-%m-%d}_{fim:%Y-%m-%d}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="rel_excel")
    except Exception as e:
        st.caption(f"Não foi possível gerar o Excel: {e}")
    st.caption("Relatórios gerenciais, pela data em que o dinheiro entrou ou saiu. O Planner organiza, mas não substitui "
               "o seu contador. Em dúvida, procure um contador.")
