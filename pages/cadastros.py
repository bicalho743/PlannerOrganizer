from utils.formatadores import formatar_df_clientes, UFS_BRASIL, validar_cpf, formatar_cpf
from utils.agenda import normalizar_aniversario, aniversario_para_digitar
from utils.origem_cliente import ORIGENS_OFICIAIS, normalizar_origem
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
from utils.importador import importar_cadastros, gerar_template_csv
from utils.custom_components import custom_info
from utils.tooltip_helper import create_tooltip, input_with_tooltip
from utils.ui import botao_excluir, botao_editar, input_moeda

# ======================================================================================
# Clientes (desenho novo, protótipo "clientes"): situação de cada cliente pelas propostas, busca,
# filtros, cartões com a ação do momento e a ficha da cliente ao lado (dados, histórico, editar, excluir).
# ======================================================================================
from urllib.parse import quote_plus
from utils.visual import CSS_PILULA, esc, icone, icone_whatsapp, pilula
from utils import visual

CLI_POR_PAGINA = 12
CLI_GRUPOS = [  # (chave, título, explicação)
    ("sem", "Sem proposta", "para orçar ou agendar visita"),
    ("enviada", "Proposta enviada", "aguardando resposta"),
    ("atend", "Em atendimento", "aprovada ou em execução"),
    ("atendida", "Atendidas", "para retorno e indicação"),
]
_CLI_TRACOS = {
    "pin": '<path d="M12 21s-7-6.1-7-11.5a7 7 0 0 1 14 0C19 14.9 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
    "busca": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
}

CLI_CSS = """
<style>
.cli-eyebrow { font-size: .74rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: #9C7A22; margin: 0 0 4px; }
h1.cli-titulo { margin: 0 !important; padding: 0 !important; font-family: 'Cormorant Garamond', Georgia, serif !important;
                font-size: 2.6rem !important; font-weight: 600 !important; color: var(--navy) !important; line-height: 1.15 !important; }
h1.cli-titulo::after { content: ""; display: block; width: 40px; height: 3px; border-radius: 2px; background: var(--gold); margin-top: 8px; }
.cli-sub { color: #5B6B80; font-size: .98rem; margin: 10px 0 4px; }
.st-key-cli_topo_btns { padding-top: 62px; }
.st-key-cli_topo_btns [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: nowrap !important; gap: 10px !important;
                                                          align-items: center !important; justify-content: flex-end; }
.st-key-cli_topo_btns [data-testid="stColumn"] { flex: 0 0 auto !important; width: auto !important; min-width: 0 !important; }
.st-key-cli_lnk_importar button, .st-key-cli_lnk_importar button p { color: #9C7A22 !important; font-weight: 700 !important; white-space: nowrap; }
.st-key-cta_nova_cliente .stButton > button p { white-space: nowrap; }
.st-key-cli_form_nova, .st-key-cli_importar { background: #fff; border-radius: 16px !important; border-color: #E7E2D6 !important; }
/* blocos só de estilo não ocupam espaço na tela */
[data-testid="stElementContainer"]:has(> [data-testid="stMarkdown"] [data-testid="stMarkdownContainer"] > style:only-child) { display: none; }
.st-key-cli_seg { margin-top: 10px; }
/* faixas por situação */
.st-key-cli_seg [data-testid="stHorizontalBlock"] { gap: 12px !important; }
.cli-sg { background: #fff; border: 1.5px solid #E7E2D6; border-radius: 14px; padding: 14px 16px; display: flex;
          justify-content: space-between; align-items: center; gap: 8px; min-height: 70px; box-sizing: border-box; }
.cli-sg b { display: block; color: var(--navy); font-size: .98rem; }
.cli-sg span { font-size: .8rem; color: #5B6B80; }
.cli-sg em { font-style: normal; font-weight: 700; font-size: 1.3rem; color: var(--navy); font-variant-numeric: tabular-nums; }
.cli-sg.on { border-color: var(--gold); background: #F6EDD3; box-shadow: inset 0 -3px 0 var(--gold); }
[class*="st-key-kcard_cliseg"]:hover .cli-sg { border-color: #C9A84C; }
.st-key-cli_busca input { background: #fff !important; }
.st-key-cli_filtros [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: wrap !important; gap: 8px !important;
                                                        align-items: center !important; }
.st-key-cli_filtros [data-testid="stColumn"] { flex: 0 0 auto !important; width: auto !important; min-width: 0 !important; }
.st-key-cli_filtros [data-testid="stSelectbox"] { width: 180px !important; }
/* cartões */
[class*="st-key-clc_"], [class*="st-key-clcon_"] { background: #fff; border-radius: 16px !important; border: 1px solid #E7E2D6 !important;
                                                  padding: 16px 14px !important; gap: 12px !important; height: 100%; }
[class*="st-key-clcon_"] { border: 2px solid var(--gold) !important; }
[class*="st-key-clc"] [data-testid="stMarkdownContainer"], .st-key-cli_ficha [data-testid="stMarkdownContainer"],
.st-key-cli_ficha_auto [data-testid="stMarkdownContainer"] { margin-bottom: 0 !important; }
.cli-hd { display: flex; gap: 12px; align-items: center; min-width: 0; }
.cli-av { flex: none; width: 42px; height: 42px; border-radius: 12px; background: #F6EDD3; color: #9C7A22; display: flex;
          align-items: center; justify-content: center; font-weight: 700; }
.cli-hd .t { flex: 1; min-width: 0; }
.cli-hd .t b { display: block; color: var(--navy); font-size: 1rem; overflow-wrap: anywhere; }
.cli-hd .t span { font-size: .84rem; color: #5B6B80; }
.cli-tag { flex: none; display: inline-flex; gap: 4px; align-items: center; font-size: .74rem; font-weight: 700; background: #F3F0EA;
           color: var(--navy); padding: 3px 8px; border-radius: 8px; white-space: nowrap; }
.cli-tag svg { color: #9C7A22; }
.cli-ln { margin-top: 12px; display: flex; gap: 6px; flex-wrap: wrap; }
.cli-sm { font-size: .84rem; color: #5B6B80; margin-top: 6px; overflow-wrap: anywhere; display: flex; gap: 4px; align-items: flex-start; }
.cli-sm svg { flex: none; color: #C0533A; margin-top: 2px; }
.cli-sm .orig { color: #9C7A22; font-weight: 600; }
.cli-vis { display: inline-flex; padding: 3px 10px; border-radius: 999px; font-size: .74rem; font-weight: 700; background: #F6EDD3; color: #5C4708; }
.cli-semp { display: inline-flex; padding: 3px 10px; border-radius: 999px; font-size: .74rem; font-weight: 700; background: #F2F4F7; color: #667085; }
[class*="st-key-kcard_cli"]:hover .cli-hd .t b { text-decoration: underline; text-decoration-color: #C9A84C; }
/* botões do cartão: ação principal azul-marinho + WhatsApp + Maps */
[class*="st-key-clc"] > [data-testid="stLayoutWrapper"]:last-child, [class*="st-key-clibt_"] { margin-top: auto; }
[class*="st-key-clibt_"] [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: wrap !important; gap: 6px !important; }
[class*="st-key-clibt_"] [data-testid="stColumn"] { min-width: 0 !important; width: auto !important; flex: 0 0 auto !important; }
[class*="st-key-clibt_"] [data-testid="stColumn"]:first-child { flex: 1 0 auto !important; }
[class*="st-key-clibt_"] .stButton > button { min-height: 38px !important; padding: .3rem .5rem !important; }
[class*="st-key-clibt_"] .stButton > button p { white-space: nowrap; font-weight: 700; font-size: .78rem; }
[class*="st-key-clibt_"] .cli-bt { font-size: .78rem; padding: 4px 8px; }
/* cartões da mesma linha com a mesma altura */
.st-key-cli_grade [data-testid="stColumn"] > [data-testid="stVerticalBlock"],
.st-key-cli_grade [data-testid="stColumn"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"] { height: 100%; }
.cli-bt { display: inline-flex; align-items: center; justify-content: center; min-height: 38px; padding: 4px 12px; border-radius: 8px;
          font-weight: 700; font-size: .84rem; text-decoration: none !important; white-space: nowrap; box-sizing: border-box; width: 100%;
          background: #fff; border: 1px solid #E7E2D6; color: var(--navy) !important; }
.cli-bt { gap: 6px; }
.cli-bt:hover { border-color: #C9A84C; }
.cli-wa-ic { flex: none; display: inline-flex; align-items: center; justify-content: center; width: 20px; height: 20px;
             border-radius: 50%; background: #fff; }
.cli-wa-ic svg { width: 15px; height: 15px; }
.cli-bt.off svg { filter: grayscale(1); opacity: .5; }
.cli-bt.nv { background: var(--navy); border-color: var(--navy); color: #fff !important; }
.cli-bt.nv:hover { background: #1B2D44; }
.cli-bt.off { color: #98A2B3 !important; pointer-events: none; background: #F9FAFB; }
/* ficha */
.st-key-cli_ficha, .st-key-cli_ficha_auto { background: #fff; border: 1px solid #E7E2D6 !important; border-radius: 16px; padding: 20px 16px !important; }
.cli-f-ey { font-size: .72rem; letter-spacing: .14em; font-weight: 700; color: #9C7A22; text-transform: uppercase; }
.cli-fh { display: flex; gap: 14px; align-items: center; margin-top: 10px; }
.cli-fh .cli-av { width: 56px; height: 56px; font-size: 1.1rem; }
.cli-fh h3 { font-family: 'Cormorant Garamond', Georgia, serif !important; font-size: 1.75rem !important; font-weight: 600 !important;
             color: var(--navy) !important; margin: 0 0 4px !important; padding: 0 !important; line-height: 1.1 !important; overflow-wrap: anywhere; }
.st-key-cli_ficha_bt [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: nowrap !important; gap: 6px !important; }
.st-key-cli_ficha_bt [data-testid="stColumn"] { min-width: 0 !important; width: auto !important; flex: 0 0 auto !important; }
.st-key-cli_ficha_bt [data-testid="stColumn"]:first-child { flex: 1 1 auto !important; }
.st-key-cli_ficha_bt .stButton > button { min-height: 38px !important; padding: .3rem .5rem !important; color: var(--navy) !important;
                                          border-color: #E7E2D6 !important; }
.st-key-cli_ficha_bt .stButton > button p { font-weight: 700; font-size: .8rem; }
.st-key-cli_ficha_bt .cli-bt { font-size: .8rem; padding: 4px 8px; }
.cli-dl { display: flex; justify-content: space-between; gap: 12px; font-size: .9rem; padding: 9px 0; border-top: 1px solid #F0ECE3; }
.cli-dl span { color: #5B6B80; flex: none; }
.cli-dl b { color: var(--navy); text-align: right; overflow-wrap: anywhere; }
.cli-f-t { font-size: .72rem; letter-spacing: .12em; font-weight: 700; color: #5B6B80; text-transform: uppercase; margin-top: 14px; }
.cli-obs { background: #FAF8F3; border-radius: 10px; padding: 10px 12px; font-size: .88rem; color: #1A202C; margin-top: 8px;
           overflow-wrap: anywhere; white-space: pre-line; }
.cli-hist { margin-top: 8px; }
.cli-hi { display: flex; gap: 10px; font-size: .88rem; padding: 6px 0; align-items: flex-start; }
.cli-hi i { width: 9px; height: 9px; border-radius: 50%; margin-top: 6px; flex-shrink: 0; }
.cli-hi div { min-width: 0; overflow-wrap: anywhere; }
.cli-hi .pv-pil { margin-left: 4px; vertical-align: 1px; }
.cli-vazio { background: #fff; border: 1px solid #E7E2D6; border-radius: 14px; padding: 16px 18px; color: #5B6B80; }
[class*="st-key-cli_links"] button, [class*="st-key-cli_links"] button p { color: #9C7A22 !important; font-weight: 700 !important; }
/* tela média e celular: cartões na largura toda; a ficha só aparece quando a cliente é escolhida, e vem antes da lista */
@media (max-width: 1280px) {
  .st-key-cli_corpo > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: wrap !important; }
  .st-key-cli_corpo > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { flex: 1 1 100% !important; width: 100% !important; }
  .st-key-cli_corpo > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:has(.st-key-cli_ficha) { order: -1; }
  .st-key-cli_corpo > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:has(.st-key-cli_ficha_auto) { display: none; }
  .st-key-cli_seg [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: wrap !important; row-gap: 12px !important; }
  .st-key-cli_seg [data-testid="stColumn"] { flex: 1 1 calc(50% - 12px) !important; min-width: 0 !important; }
}
@media (min-width: 1281px) { .st-key-cli_fechar_ficha { display: none; } }
@media (max-width: 640px) {
  h1.cli-titulo { font-size: 2.1rem !important; }
  .st-key-cli_topo_btns { padding-top: 0; }
  .st-key-cli_topo_btns [data-testid="stHorizontalBlock"] { justify-content: flex-start; }
  .cli-sg { padding: 12px; min-height: 64px; }
  .cli-sg b { font-size: .9rem; }
}
""" + CSS_PILULA + """
</style>
"""


def _cli_ic(nome, tam=14):
    if nome in _CLI_TRACOS:
        return (f'<svg width="{tam}" height="{tam}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" '
                f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{_CLI_TRACOS[nome]}</svg>')
    return icone(nome, tam)


def _cli_txt(v):
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except (TypeError, ValueError):
        pass
    t = str(v).strip()
    return "" if t.lower() in ("nan", "none") else t


def _cli_data(v):
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(v, "date") and callable(v.date):
        return v.date()
    if hasattr(v, "year"):
        return v
    try:
        return datetime.fromisoformat(str(v)[:10]).date()
    except ValueError:
        return None


def _cli_num(v):
    try:
        f = float(v)
        return 0.0 if f != f else f
    except (TypeError, ValueError):
        return 0.0


def _cli_brl(v):
    from utils.currency_formatter import fmt_brl
    t = fmt_brl(v)
    return t[:-3] if t.endswith(",00") else t


def _cli_dm(d):
    return f"{d.day:02d}/{d.month:02d}" if d else ""


def _cli_iniciais(nome):
    partes = [p for p in str(nome or "").split() if p[:1].isalpha()]
    if not partes:
        return "?"
    return (partes[0][0] + (partes[-1][0] if len(partes) > 1 else "")).upper()


def _cli_fone(tel):
    """(11) 98765-4321 para exibir; o que não for número brasileiro comum fica como foi digitado."""
    d = "".join(ch for ch in str(tel or "") if ch.isdigit())
    if d.startswith("55") and len(d) in (12, 13):
        d = d[2:]
    if len(d) == 11:
        return f"({d[:2]}) {d[2:7]}-{d[7:]}"
    if len(d) == 10:
        return f"({d[:2]}) {d[2:6]}-{d[6:]}"
    return str(tel or "")


def _cli_primeiro(nome):
    n = _cli_txt(nome)
    return n.split(" ")[0] if n else "cliente"


def _cli_ha(d, hoje):
    n = (hoje - d).days
    if n == 0:
        return "hoje"
    if n == 1:
        return "ontem"
    return f"há {n} dias" if n > 0 else f"em {-n} dias"


def _cli_servico(p):
    for k in ("tipo_proposta", "descricao"):
        t = _cli_txt(p.get(k))
        if t:
            t = t.split("\n")[0]
            return t if len(t) <= 36 else t[:34].rstrip() + "…"
    return "Organização"


def _cli_maps(c):
    partes = [c[k] for k in ("endereco", "bairro", "cidade", "estado") if c.get(k)]
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(', '.join(partes))}" if partes else ""


def _cli_ir(pagina, **estado):
    for k, v in estado.items():
        st.session_state[k] = v
    st.session_state.current_page = pagina


def _cli_montar(db, hoje):
    """Uma linha por cliente com o que a tela precisa (situação, proposta principal, visita, retorno, aniversário)."""
    from utils.agenda import dia_mes_aniversario
    from utils.proposta_status import normalize
    clientes = db.get_clientes()
    if clientes is None or clientes.empty:
        return []
    try:
        propostas = db.get_propostas()
    except Exception:
        propostas = pd.DataFrame()
    try:
        compromissos = db.get_compromissos(inicio=hoje - timedelta(days=365))
    except Exception:
        compromissos = pd.DataFrame()
    try:
        from utils.pos_organizacao_dados import acoes_pos, pendentes
        pend = pendentes(acoes_pos(st.session_state.get("usuario_id") or getattr(db, "usuario_id", None)))
    except Exception:
        pend = pd.DataFrame()
    try:
        fin = db.get_financeiro()
    except Exception:
        fin = pd.DataFrame()

    props_por = {}
    if not propostas.empty:
        for _, p in propostas.iterrows():
            d = p.to_dict()
            d["st"] = normalize(d.get("status") or "") or ""
            d["quando"] = _cli_data(d.get("data_proposta")) or _cli_data(d.get("data_inicio"))
            props_por.setdefault(d.get("cliente_id"), []).append(d)
    comp_por = {}
    if not compromissos.empty:
        for _, c in compromissos.iterrows():
            if c.get("cliente_id") is not None and not pd.isna(c.get("cliente_id")):
                comp_por.setdefault(int(c["cliente_id"]), []).append(c.to_dict())
    ret_por = {}
    if not pend.empty:
        for _, a in pend.iterrows():
            venc = _cli_data(a["due_date"])
            if venc and venc <= hoje:
                atual = ret_por.get(a["cliente_id"])
                if not atual or venc < atual[0]:
                    ret_por[a["cliente_id"]] = (venc, int(a["post_organization_id"]))
    pago_por_prop = {}
    if not fin.empty and "proposta_id" in fin.columns:
        rec = fin[(fin["status"] == "Recebido") & fin["tipo"].astype(str).str.lower().isin(["receita", "receita_a_receber"])
                  & fin["proposta_id"].notna()]
        for pid, v in rec.groupby("proposta_id")["valor"].sum().items():
            pago_por_prop[int(pid)] = float(v)

    prioridade = ["em_execucao", "aprovada", "em_aberto", "finalizada"]
    lista = []
    for _, c in clientes.iterrows():
        cid = int(c["id"])
        info = {k: _cli_txt(c.get(k)) for k in ("nome", "telefone", "cpf", "estado", "cidade", "bairro", "endereco",
                                               "origem_cliente", "observacoes", "data_aniversario", "email")}
        info["id"] = cid
        info["origem"] = normalizar_origem(info["origem_cliente"]) if info["origem_cliente"] else ""
        info["data_cadastro"] = _cli_data(c.get("data_cadastro"))
        ps = sorted(props_por.get(cid, []), key=lambda p: (p["quando"] or datetime.min.date(), p.get("id") or 0), reverse=True)
        info["propostas"] = ps
        principal = None
        for stt in prioridade:
            cand = [p for p in ps if p["st"] == stt]
            if cand:
                principal = cand[0]
                break
        info["principal"] = principal
        info["status"] = principal["st"] if principal else ""
        info["grupo"] = {"em_execucao": "atend", "aprovada": "atend", "em_aberto": "enviada", "finalizada": "atendida"}.get(info["status"], "sem")
        info["n_finalizadas"] = sum(1 for p in ps if p["st"] == "finalizada")
        info["pago"] = sum(pago_por_prop.get(int(p["id"]), 0.0) for p in ps if p.get("id") is not None)
        comps = sorted(comp_por.get(cid, []), key=lambda x: (_cli_data(x["data"]) or hoje, x.get("hora") or ""))
        info["compromissos"] = comps
        info["visita"] = next((x for x in comps if (_cli_data(x["data"]) or hoje) >= hoje), None)
        info["retorno"] = ret_por.get(cid)
        dm = dia_mes_aniversario(info["data_aniversario"] or None)
        info["aniv_dm"] = dm
        prox = None
        if dm:
            try:
                prox = hoje.replace(month=dm[1], day=dm[0])
            except ValueError:
                prox = hoje.replace(month=dm[1], day=28)
            if prox < hoje:
                prox = prox.replace(year=hoje.year + 1)
        info["aniv_prox"] = prox
        lista.append(info)
    lista.sort(key=lambda i: i["nome"].lower())
    return lista


def _cli_pilula(c, hoje):
    if c["status"]:
        return pilula(c["status"])
    v = c["visita"]
    if v:
        d = _cli_data(v["data"])
        quando = "hoje" if d == hoje else ("amanhã" if d == hoje + timedelta(days=1) else _cli_dm(d))
        return f'<span class="cli-vis">Visita {quando}{" " + esc(v.get("hora")) if v.get("hora") else ""}</span>'
    return '<span class="cli-semp">Sem proposta</span>'


def _cli_linha_servico(c, hoje):
    p = c["principal"]
    if not p:
        v = c["visita"]
        if v:
            return f'{esc(_cli_txt(v.get("titulo")) or "Visita")} · sem proposta ainda'
        return (f'Cliente desde {_cli_dm(c["data_cadastro"])} · sem proposta ainda' if c["data_cadastro"]
                else "Sem proposta ainda")
    partes = [esc(_cli_servico(p))]
    valor = _cli_num(p.get("valor"))
    if p["st"] == "em_aberto":
        partes += ([_cli_brl(valor)] if valor else []) + ([_cli_ha(p["quando"], hoje)] if p["quando"] else [])
    elif p["st"] == "em_execucao":
        ini, fim = _cli_data(p.get("data_inicio")), _cli_data(p.get("data_fim"))
        if ini and fim and fim >= ini and ini <= hoje <= fim:
            partes.append(f"dia {(hoje - ini).days + 1} de {(fim - ini).days + 1}")
        elif ini:
            partes.append(f"desde {_cli_dm(ini)}")
        if valor:
            partes.append(_cli_brl(valor))
    elif p["st"] == "aprovada":
        partes += ([_cli_brl(valor)] if valor else []) + (["sinal recebido"] if _cli_num(p.get("sinal")) > 0 else [])
    else:
        fim = _cli_data(p.get("data_fim")) or p["quando"]
        partes += ([_cli_dm(fim)] if fim else []) + ([f'{c["n_finalizadas"]} serviços'] if c["n_finalizadas"] > 1 else [])
    return " · ".join(partes)


def _cli_local(c):
    partes = [esc(x) for x in (c["bairro"], c["cidade"]) if x]
    if c["origem"]:
        partes.append(f'<span class="orig">{esc(c["origem"])}</span>')
    if not partes:
        return ""
    return f'<div class="cli-sm">{_cli_ic("pin", 13)}<span>{" · ".join(partes)}</span></div>'


def _cli_tag(c, hoje):
    if c["aniv_prox"] and (c["aniv_prox"] - hoje).days <= 7:
        quando = "Hoje" if c["aniv_prox"] == hoje else _cli_dm(c["aniv_prox"])
        return f'<span class="cli-tag">{_cli_ic("bolo", 13)}{quando}</span>'
    if c["retorno"]:
        venc = c["retorno"][0]
        return f'<span class="cli-tag">{_cli_ic("retorno", 13)}Retorno {"hoje" if venc == hoje else "atrasado"}</span>'
    return ""


def _cli_wa_link(c, msg=""):
    from utils.whatsapp_helper import whatsapp_link
    return whatsapp_link(c["telefone"], msg) if c["telefone"] else ""


def _cli_a(url, rotulo, cls="", wa=False):
    """Link com cara de botão; wa=True põe o símbolo do WhatsApp (num círculo branco nos botões escuros)."""
    ic = ""
    if wa:
        ic = f'<span class="cli-wa-ic">{icone_whatsapp(16)}</span>' if "nv" in cls else icone_whatsapp(16)
    if not url:
        titulo = ' title="Cliente sem telefone cadastrado"' if wa else ""
        return f'<span class="cli-bt off {cls}"{titulo}>{ic}<span>{rotulo}</span></span>'
    return f'<a class="cli-bt {cls}" href="{esc(url)}" target="_blank" rel="noopener">{ic}<span>{rotulo}</span></a>'


def _cli_cartao(c, hoje, selecionado):
    cid = c["id"]
    with st.container(border=True, key=f"{'clcon' if selecionado else 'clc'}_{cid}"):
        with st.container(key=f"kcard_cli{cid}"):
            st.markdown(f'<div class="cli-hd"><span class="cli-av">{esc(_cli_iniciais(c["nome"]))}</span>'
                        f'<div class="t"><b>{esc(c["nome"])}</b><span>{esc(_cli_fone(c["telefone"])) or "sem telefone"}</span></div>'
                        f'{_cli_tag(c, hoje)}</div>'
                        f'<div class="cli-ln">{_cli_pilula(c, hoje)}</div>'
                        f'<div class="cli-sm">{_cli_linha_servico(c, hoje)}</div>{_cli_local(c)}', unsafe_allow_html=True)
            if st.button("Ver a ficha da cliente", key=f"cli_ver_{cid}"):
                st.session_state["cli_sel"] = cid
                st.session_state["cli_sel_explicito"] = True
                st.session_state["cli_rolar"] = True
                st.rerun()
        p = c["principal"]
        with st.container(key=f"clibt_{cid}"):
            c1, c2, c3 = st.columns([1.6, 1, 0.8])
            with c1:
                if c["status"] == "em_aberto":
                    msg = (f"Oi, {_cli_primeiro(c['nome'])}! Tudo bem? Passando para saber se ficou alguma dúvida sobre a "
                           f"proposta de organização que te enviei. Fico à disposição!")
                    st.markdown(_cli_a(_cli_wa_link(c, msg), "Lembrar no WhatsApp", "nv", wa=True), unsafe_allow_html=True)
                elif c["status"] in ("em_execucao", "aprovada"):
                    st.button("Abrir proposta" if c["status"] == "em_execucao" else "Agendar serviço", key=f"cli_ac_{cid}",
                              type="primary", use_container_width=True, on_click=_cli_ir,
                              args=("Propostas",), kwargs={"kanban_selected_proposta": int(p["id"])})
                elif c["status"] == "finalizada" and c["retorno"]:
                    st.button("Mandar mensagem", key=f"cli_ac_{cid}", type="primary", use_container_width=True,
                              on_click=_cli_ir, args=("PosOrganizacao",), kwargs={"pos_sel_abrir": c["retorno"][1]})
                elif c["status"] == "finalizada":
                    if st.button("Ver ficha", key=f"cli_ac_{cid}", type="primary", use_container_width=True):
                        st.session_state["cli_sel"] = cid
                        st.session_state["cli_sel_explicito"] = True
                        st.session_state["cli_rolar"] = True
                        st.rerun()
                else:
                    st.button("Criar proposta", key=f"cli_ac_{cid}", type="primary", use_container_width=True,
                              on_click=_cli_ir, args=("Propostas",),
                              kwargs={"kanban_nova_proposta_open": True, "nova_proposta_cliente_id": int(cid)})
            if c["status"] != "em_aberto":  # em aberto, a ação principal já abre o WhatsApp dela
                c2.markdown(_cli_a(_cli_wa_link(c), "WhatsApp", wa=True), unsafe_allow_html=True)
            c3.markdown(_cli_a(_cli_maps(c), "Maps"), unsafe_allow_html=True)


def _cli_form_campos(dados=None, sufixo="novo"):
    """Campos do cadastro (novo ou edição). Devolve um dict com o que foi digitado."""
    d = dados or {}
    v = {}
    v["nome"] = st.text_input("Nome", value=d.get("nome", ""))
    col1, col2 = st.columns(2)
    with col1:
        v["telefone"] = st.text_input("Telefone", value=d.get("telefone", ""))
        v["cpf"] = st.text_input("CPF", value=d.get("cpf", ""))
        ufs = list(UFS_BRASIL)
        uf = d.get("estado", "")
        if uf and uf not in ufs:
            ufs.append(uf)
        v["estado"] = st.selectbox("Estado (UF)", ufs, index=ufs.index(uf) if uf in ufs else None,
                                   placeholder="Selecione a UF") or ""
        v["cidade"] = st.text_input("Cidade", value=d.get("cidade", ""))
    with col2:
        v["bairro"] = st.text_input("Bairro", value=d.get("bairro", ""))
        v["endereco"] = st.text_input("Endereço", value=d.get("endereco", ""))
        v["aniversario"] = st.text_input("Aniversário (dia/mês)", value=aniversario_para_digitar(d.get("data_aniversario")) if d.get("data_aniversario") else "",
                                         placeholder="Ex.: 14/06", help="Só o dia e o mês. Pode digitar 14/06, 1406 ou 14/jun.")
        atual = normalizar_origem(d.get("origem_cliente")) if d.get("origem_cliente") else None
        v["origem_cliente"] = st.selectbox("Como chegou (origem)", ORIGENS_OFICIAIS,
                                           index=ORIGENS_OFICIAIS.index(atual) if atual in ORIGENS_OFICIAIS else None,
                                           placeholder="Selecione a origem")
    v["observacoes"] = st.text_area("Observações da casa", value=d.get("observacoes", ""),
                                    placeholder="Ex.: elevador de serviço até 18h, gato no apartamento")
    return v


def _cli_validar(v):
    """Confere os campos; devolve (dados para gravar, erro)."""
    if not v["nome"] or not v["nome"].strip():
        return None, "O campo Nome é obrigatório."
    cpf = v["cpf"].strip() if v["cpf"] else ""
    if cpf and not validar_cpf(cpf):
        return None, "CPF inválido. Verifique os dígitos."
    aniv = normalizar_aniversario(v["aniversario"])
    if aniv is None:
        return None, "Aniversário: informe dia e mês, por exemplo 14/06."
    return {"nome": v["nome"].strip(), "telefone": v["telefone"], "cpf": formatar_cpf(cpf) if cpf else cpf,
            "estado": v["estado"], "cidade": v["cidade"], "bairro": v["bairro"], "endereco": v["endereco"],
            "data_aniversario": aniv or None, "origem_cliente": v["origem_cliente"],
            "observacoes": v["observacoes"]}, None


def _cli_nova(db):
    with st.container(border=True, key="cli_form_nova"):
        st.markdown('<div class="cli-f-ey">Nova cliente</div>', unsafe_allow_html=True)
        with st.form("cadastro_cliente", clear_on_submit=True, border=False):
            v = _cli_form_campos()
            c1, c2, _ = st.columns([1.2, 1, 2])
            enviar = c1.form_submit_button("Cadastrar cliente", type="primary", use_container_width=True)
            fechar = c2.form_submit_button("Fechar", type="tertiary")
        if fechar:
            st.session_state["cli_nova_open"] = False
            st.rerun()
        if enviar:
            dados, erro = _cli_validar(v)
            if erro:
                st.error(erro)
                return
            try:
                novo = db.add_cliente(**dados)
                st.session_state["cli_nova_open"] = False
                if novo:
                    st.session_state["cli_sel"] = int(novo)
                    st.session_state["cli_sel_explicito"] = True
                    st.session_state["cli_rolar"] = True
                st.toast("Cliente cadastrada com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao cadastrar cliente: {str(e)}")


def _cli_importar(db):
    with st.container(border=True, key="cli_importar"):
        st.markdown('<div class="cli-f-ey">Importar planilha</div>', unsafe_allow_html=True)
        st.caption("Baixe o modelo, preencha com as suas clientes e envie o arquivo CSV.")
        st.download_button("Baixar modelo de planilha", gerar_template_csv("Cliente"), "template_cliente.csv", "text/csv",
                           help="Baixe este modelo, preencha com seus dados e envie para importar clientes")
        arquivo = st.file_uploader("Selecione o arquivo CSV de clientes", type=['csv'], key="cliente_file_uploader")
        if arquivo and st.button("Importar clientes", type="primary", key="cli_btn_importar"):
            with st.spinner("Importando dados..."):
                sucesso, mensagem = importar_cadastros(arquivo, "Cliente", db)
            if sucesso:
                db.invalidar_cache()
                st.session_state["cli_import_msg"] = mensagem
                st.rerun()  # a lista é montada antes: sem isso as importadas só apareciam no próximo clique
            else:
                st.error(mensagem)
        msg = st.session_state.pop("cli_import_msg", None)
        if msg:
            st.success(msg)


def _cli_rolar_ate(seletor):
    """Telas estreitas: depois de escolher a cliente, leva a tela até o painel (que fica acima da lista)."""
    import streamlit.components.v1 as components
    components.html(f"""<script>
(function(){{ var w = window.parent; if (w.innerWidth > 1280) return;
  var n = 0, t = setInterval(function(){{ var el = w.document.querySelector('{seletor}');
    if (el) {{ clearInterval(t); el.scrollIntoView({{behavior: 'smooth', block: 'start'}}); }} else if (++n > 30) clearInterval(t); }}, 100);
}})();</script>""", height=0)


def _cli_ficha(c, db, hoje, explicito):
    cid = c["id"]
    with st.container(key="cli_ficha" if explicito else "cli_ficha_auto"):
        with st.container(key="cli_fechar_ficha"):
            if st.button("Fechar ficha", key="cli_btn_fechar", type="tertiary", icon=":material/close:"):
                st.session_state["cli_sel_explicito"] = False
                st.session_state.pop("cli_editando", None)
                st.rerun()
        if st.session_state.pop("cli_rolar", False):
            _cli_rolar_ate(".st-key-cli_ficha")
        st.markdown(f'<div class="cli-f-ey">Ficha da cliente</div><div class="cli-fh"><span class="cli-av">{esc(_cli_iniciais(c["nome"]))}</span>'
                    f'<div style="min-width:0"><h3>{esc(c["nome"])}</h3>{_cli_pilula(c, hoje)}</div></div>', unsafe_allow_html=True)

        if st.session_state.get("cli_editando") == cid:
            with st.form(f"form_editar_cliente_{cid}", border=False):
                v = _cli_form_campos(c, sufixo=str(cid))
                b1, b2 = st.columns(2)
                salvar = b1.form_submit_button("Salvar alterações", type="primary", use_container_width=True)
                cancelar = b2.form_submit_button("Cancelar", type="tertiary")
            if cancelar:
                st.session_state.pop("cli_editando", None)
                st.rerun()
            if salvar:
                dados, erro = _cli_validar(v)
                if erro:
                    st.error(erro)
                else:
                    try:
                        if db.update_cliente(cid, **dados):
                            st.session_state.pop("cli_editando", None)
                            st.toast("Cliente atualizada com sucesso!")
                            st.rerun()
                        else:
                            st.error("Erro ao atualizar cliente")
                    except Exception as e:
                        st.error(f"Erro ao salvar alterações: {str(e)}")
            return

        with st.container(key="cli_ficha_bt"):
            b1, b2, b3, b4 = st.columns([1.6, 1, 1, 1])
            b1.markdown(_cli_a(_cli_wa_link(c), "WhatsApp", "nv", wa=True), unsafe_allow_html=True)
            tel = "".join(ch for ch in c["telefone"] if ch.isdigit() or ch == "+")
            b2.markdown(_cli_a(f"tel:{tel}" if tel else "", "Ligar"), unsafe_allow_html=True)
            b3.markdown(_cli_a(_cli_maps(c), "Maps"), unsafe_allow_html=True)
            if b4.button("Editar", key=f"cli_editar_{cid}"):
                st.session_state["cli_editando"] = cid
                st.session_state["cli_sel_explicito"] = True
                st.session_state["cli_rolar"] = True
                st.rerun()

        end = ", ".join(x for x in (c["endereco"], c["bairro"]) if x)
        cidade = " - ".join(x for x in (c["cidade"], c["estado"]) if x)
        linhas = [("Telefone", esc(_cli_fone(c["telefone"])) or "—"), ("Endereço", esc(end) or "—")]
        if cidade:
            linhas.append(("Cidade", esc(cidade)))
        linhas += [("Aniversário", _cli_dm(c["aniv_prox"]) or "—"), ("Como chegou", esc(c["origem"]) or "—")]
        if c["cpf"]:
            linhas.append(("CPF", esc(c["cpf"])))
        linhas.append(("Total já pago", f'<span style="color:#2F6B4F">{_cli_brl(c["pago"])}</span>'))
        html_ = "".join(f'<div class="cli-dl"><span>{k}</span><b>{v}</b></div>' for k, v in linhas)
        if c["observacoes"]:
            html_ += f'<div class="cli-f-t">Observações da casa</div><div class="cli-obs">{esc(c["observacoes"])}</div>'

        cores = {"em_aberto": "#E8D5A3", "aprovada": "#C9A84C", "em_execucao": "#0D1B2A", "finalizada": "#2F6B4F",
                 "recusada": "#C3BDB0"}
        eventos = []
        for p in c["propostas"]:
            valor = _cli_num(p.get("valor"))
            eventos.append((p["quando"], f'<i style="background:{cores.get(p["st"], "#C3BDB0")}"></i><div>{esc(_cli_servico(p))}'
                                         f'{" · " + _cli_brl(valor) if valor else ""}{" · " + _cli_dm(p["quando"]) if p["quando"] else ""}'
                                         f' {pilula(p["st"])}</div>'))
        for x in c["compromissos"]:
            d = _cli_data(x["data"])
            eventos.append((d, f'<i style="background:#C9A84C"></i><div>{esc(_cli_txt(x.get("titulo")) or "Compromisso")} · {_cli_dm(d)}</div>'))
        eventos.sort(key=lambda e: e[0] or datetime.min.date(), reverse=True)
        hist = "".join(f'<div class="cli-hi">{h}</div>' for _, h in eventos[:8])
        if c["data_cadastro"]:
            hist += f'<div class="cli-hi"><i style="background:#C3BDB0"></i><div>Cadastro · {_cli_dm(c["data_cadastro"])}</div></div>'
        if hist:
            html_ += f'<div class="cli-f-t">Histórico</div><div class="cli-hist">{hist}</div>'
        st.markdown(html_, unsafe_allow_html=True)

        with st.container(key="cta_cli_nova_prop"):
            if st.button(f"Nova proposta para {_cli_primeiro(c['nome'])}", icon=":material/add:", key="cli_nova_prop",
                         use_container_width=True):
                _cli_ir("Propostas", kanban_nova_proposta_open=True, nova_proposta_cliente_id=int(c["id"]))
                st.rerun()

        if st.session_state.get("cli_conf_excluir") == cid:
            st.warning(f"Excluir {c['nome']}? Isso não pode ser desfeito.")
            e1, e2 = st.columns(2)
            with e1:
                if botao_excluir("Sim, excluir", f"cli_sim_excluir_{cid}"):
                    ok, msg = st.session_state.db.delete_cliente(cid)
                    st.session_state.pop("cli_conf_excluir", None)
                    if ok:
                        st.session_state.pop("cli_sel", None)
                        st.session_state["cli_sel_explicito"] = False
                        st.toast(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            if e2.button("Cancelar", key=f"cli_nao_excluir_{cid}", use_container_width=True):
                st.session_state.pop("cli_conf_excluir", None)
                st.rerun()
        else:
            with st.container(key="cli_links_excluir"):
                if st.button("Excluir cliente", key=f"cli_excluir_{cid}", type="tertiary", icon=":material/delete:"):
                    st.session_state["cli_conf_excluir"] = cid
                    st.rerun()


def _cli_excluir_varias(db):
    """Excluir várias clientes de uma vez (mesmo recurso da tela antiga)."""
    clientes_atuais = db.get_clientes()
    if clientes_atuais.empty:
        st.info("Nenhum cliente disponível para exclusão.")
        return
    df_base = clientes_atuais[['id', 'nome', 'telefone', 'cpf']].copy()
    df_base.columns = ['ID', 'Nome', 'Telefone', 'CPF']
    df_base = df_base.sort_values('Nome').reset_index(drop=True)
    fcol1, fcol2 = st.columns([3, 1])
    termo_busca = fcol1.text_input("Buscar cliente", key="busca_multi_delete", placeholder="Filtrar por nome, telefone ou CPF")
    itens_por_pagina = fcol2.selectbox("Itens por página", [10, 25, 50, 100], index=0, key="itens_pagina_multi_delete")
    df_filtrado = df_base
    if termo_busca and termo_busca.strip():
        termo = termo_busca.strip().lower()
        mascara = df_base[['Nome', 'Telefone', 'CPF']].astype(str).apply(
            lambda s: s.str.lower().str.contains(termo, na=False, regex=False)).any(axis=1)
        df_filtrado = df_base[mascara].reset_index(drop=True)
    total_registros = len(df_filtrado)
    if total_registros == 0:
        st.info("Nenhum cliente encontrado para o filtro informado.")
        return
    total_paginas = max(1, -(-total_registros // itens_por_pagina))
    pagina_atual = min(st.session_state.get("pagina_multi_delete", 1), total_paginas)
    pcol1, pcol2, pcol3 = st.columns([1, 2, 1])
    if pcol1.button("Anterior", key="prev_multi_delete", disabled=(pagina_atual <= 1), icon=":material/arrow_back:"):
        st.session_state.pagina_multi_delete = pagina_atual - 1
        st.rerun()
    pcol2.markdown(f"<div style='text-align:center;'>Página <b>{pagina_atual}</b> de <b>{total_paginas}</b> "
                   f"({total_registros} cliente(s) encontrado(s))</div>", unsafe_allow_html=True)
    if pcol3.button("Próximo", key="next_multi_delete", disabled=(pagina_atual >= total_paginas), icon=":material/arrow_forward:"):
        st.session_state.pagina_multi_delete = pagina_atual + 1
        st.rerun()
    inicio = (pagina_atual - 1) * itens_por_pagina
    df_pagina = df_filtrado.iloc[inicio:inicio + itens_por_pagina].copy()
    marcar_todos = st.checkbox("Selecionar todos desta página", key="marcar_todos_multi_delete")
    df_pagina["Selecionar"] = bool(marcar_todos)
    selection = st.data_editor(
        df_pagina,
        column_config={
            "Selecionar": st.column_config.CheckboxColumn("Selecionar", help="Selecione para excluir"),
            "ID": st.column_config.NumberColumn("ID", disabled=True),
            "Nome": st.column_config.TextColumn("Nome", disabled=True),
            "Telefone": st.column_config.TextColumn("Telefone", disabled=True),
            "CPF": st.column_config.TextColumn("CPF", disabled=True),
        },
        hide_index=True, use_container_width=True, key="editor_clientes_multi_delete")
    qtd = int(selection["Selecionar"].sum()) if "Selecionar" in selection else 0
    st.caption(f"{qtd} cliente(s) selecionado(s) nesta página.")
    if botao_excluir("Excluir clientes selecionadas", "btn_excluir_multi_clientes", use_container_width=False):
        ids = [int(r["ID"]) for _, r in selection.iterrows() if r["Selecionar"] == True]
        if not ids:
            st.warning("Nenhum cliente selecionado para exclusão.")
            return
        resultados = db.delete_multiple_clientes(ids)
        db.invalidar_cache()
        if resultados["sucesso"]:
            st.success(f"{len(resultados['sucesso'])} clientes excluídos com sucesso!")
        if resultados["erro"]:
            st.error(f"{len(resultados['erro'])} clientes não puderam ser excluídos:")
            for erro in resultados["erro"]:
                st.warning(f"Cliente {erro['nome']} (ID: {erro['id']}): {erro['mensagem']}")
        if resultados["sucesso"] and not resultados["erro"]:
            st.rerun()


def _cli_tabela(lista):
    """A lista completa em tabela (todas as colunas), como na tela antiga."""
    df = pd.DataFrame([{"ID": c["id"], "Nome": c["nome"], "Telefone": c["telefone"], "CPF": c["cpf"], "Estado": c["estado"],
                        "Cidade": c["cidade"], "Bairro": c["bairro"], "Endereço": c["endereco"],
                        "Data Aniversário": c["data_aniversario"], "Origem": c["origem"] or c["origem_cliente"],
                        "Observações": c["observacoes"]} for c in lista])
    st.dataframe(formatar_df_clientes(df), use_container_width=True, hide_index=True)


def tela_clientes():
    db = st.session_state.db
    hoje = visual.hoje()
    st.markdown(CLI_CSS, unsafe_allow_html=True)
    if st.session_state.get("_last_page_rendered") not in ("Clientes", None):
        for k in ("cli_sel", "cli_sel_explicito", "cli_editando", "cli_conf_excluir", "cli_pagina", "cli_seg_f"):
            st.session_state.pop(k, None)

    lista = _cli_montar(db, hoje)
    if st.session_state.pop("abrir_nova_cliente", False) or not lista:
        st.session_state["cli_nova_open"] = True

    c_tit, c_btn = st.columns([3.2, 1.6], vertical_alignment="top")
    c_tit.markdown('<div class="cli-eyebrow">Uma relação começa por aqui</div><h1 class="cli-titulo">Clientes</h1>'
                   '<div class="cli-sub">Cadastre, faça a proposta e acompanhe cada cliente do primeiro contato ao retorno.</div>',
                   unsafe_allow_html=True)
    with c_btn, st.container(key="cli_topo_btns"):
        b1, b2 = st.columns(2)
        with b1, st.container(key="cli_lnk_importar"):
            if st.button("Importar planilha", key="cli_btn_imp", type="tertiary"):
                st.session_state["cli_importar_open"] = not st.session_state.get("cli_importar_open", False)
                st.rerun()
        with b2, st.container(key="cta_nova_cliente"):
            if st.button("Nova cliente", icon=":material/add:", key="cli_btn_nova"):
                st.session_state["cli_nova_open"] = not st.session_state.get("cli_nova_open", False)
                st.rerun()
    if st.session_state.get("cli_importar_open"):
        _cli_importar(db)
    if st.session_state.get("cli_nova_open"):
        _cli_nova(db)
    if not lista:
        st.markdown('<div class="cli-vazio">Nenhuma cliente cadastrada ainda. Cadastre a primeira acima (nome e telefone já '
                    'bastam) ou importe a sua planilha.</div>', unsafe_allow_html=True)
        return

    # faixas por situação (clicar filtra; clicar de novo tira o filtro)
    seg = st.session_state.get("cli_seg_f")
    contagem = {k: sum(1 for c in lista if c["grupo"] == k) for k, _, _ in CLI_GRUPOS}
    with st.container(key="cli_seg"):
        for col, (k, tit, expl) in zip(st.columns(4), CLI_GRUPOS):
            with col, st.container(key=f"kcard_cliseg{k}"):
                st.markdown(f'<div class="cli-sg{" on" if seg == k else ""}"><div><b>{tit}</b><span>{expl}</span></div>'
                            f'<em>{contagem[k]}</em></div>', unsafe_allow_html=True)
                if st.button(f"Filtrar: {tit}", key=f"cli_seg_{k}"):
                    st.session_state["cli_seg_f"] = None if seg == k else k
                    st.session_state["cli_pagina"] = 1
                    st.rerun()

    with st.container(key="cli_busca"):
        busca = st.text_input("Buscar cliente", key="busca_clientes", placeholder="Buscar por nome, telefone, bairro ou cidade",
                              label_visibility="collapsed")
    n_aniv = sum(1 for c in lista if c["aniv_dm"] and c["aniv_dm"][1] == hoje.month)
    n_ret = sum(1 for c in lista if c["retorno"])
    origens = sorted({c["origem"] for c in lista if c["origem"]})
    cidades = sorted({c["cidade"] for c in lista if c["cidade"]}, key=str.lower)
    with st.container(key="cli_filtros"):
        f1, f2, f3 = st.columns(3)
        rot = {"aniv": f"Aniversário este mês ({n_aniv})", "ret": f"Retorno pendente ({n_ret})"}
        chips = f1.pills("Filtros", ["aniv", "ret"], format_func=rot.get, selection_mode="multi", key="cli_chips",
                         label_visibility="collapsed") or []
        f_origem = f2.selectbox("Origem", ["Origem: todas"] + origens, key="cli_f_origem", label_visibility="collapsed")
        f_cidade = f3.selectbox("Cidade", ["Cidade: todas"] + cidades, key="cli_f_cidade", label_visibility="collapsed")

    vis = lista
    if seg:
        vis = [c for c in vis if c["grupo"] == seg]
    if busca and busca.strip():
        termo = busca.strip().lower()
        dig = "".join(ch for ch in termo if ch.isdigit())
        vis = [c for c in vis if termo in " ".join((c["nome"], c["telefone"], c["bairro"], c["cidade"])).lower()
               or (len(dig) >= 3 and dig in "".join(ch for ch in c["telefone"] if ch.isdigit()))]
    if "aniv" in chips:
        vis = [c for c in vis if c["aniv_dm"] and c["aniv_dm"][1] == hoje.month]
    if "ret" in chips:
        vis = [c for c in vis if c["retorno"]]
    if f_origem != "Origem: todas":
        vis = [c for c in vis if c["origem"] == f_origem]
    if f_cidade != "Cidade: todas":
        vis = [c for c in vis if c["cidade"] == f_cidade]

    ids_todos = {c["id"] for c in lista}
    sel = st.session_state.get("cli_sel")
    explicito = bool(st.session_state.get("cli_sel_explicito")) and sel in ids_todos
    if sel not in ids_todos or (not explicito and sel not in {c["id"] for c in vis}):
        sel = vis[0]["id"] if vis else None

    col_l, col_r = st.container(key="cli_corpo").columns([2, 1], gap="medium")
    with col_l:
        if not vis:
            st.markdown('<div class="cli-vazio">Nenhuma cliente encontrada com esses filtros.</div>', unsafe_allow_html=True)
        pagina = st.session_state.get("cli_pagina", 1)
        mostrar = vis[:CLI_POR_PAGINA * pagina]
        with st.container(key="cli_grade"):
            for i in range(0, len(mostrar), 2):
                cols = st.columns(2, gap="small")
                for col, c in zip(cols, mostrar[i:i + 2]):
                    with col:
                        _cli_cartao(c, hoje, c["id"] == sel)
        if len(vis) > len(mostrar):
            with st.container(key="cli_links_mais"):
                if st.button(f"Mostrar mais ({len(vis) - len(mostrar)})", key="cli_btn_mais", type="tertiary"):
                    st.session_state["cli_pagina"] = pagina + 1
                    st.rerun()
        st.caption(f"{len(vis)} de {len(lista)} cliente(s)")
    with col_r:
        if sel is not None:
            _cli_ficha(next(c for c in lista if c["id"] == sel), db, hoje, explicito)

    with st.expander("Ver todas em tabela"):
        _cli_tabela(vis)
    with st.expander("Excluir várias clientes"):
        _cli_excluir_varias(db)


def show(modo="todos"):
    """modo: "clientes" (só a aba de clientes, item próprio no menu), "outros" (fornecedores,
    parceiros, assistentes e produtos) ou "todos"."""
    from utils.auth_guard import require_auth
    require_auth()
    # UX-4: tabela responsiva com rolagem horizontal visível e cabeçalhos fixos (sticky)
    st.markdown("<style>.cadastros-page [data-testid='stDataFrame'] [data-testid='stDataFrameResizable']{overflow-x:auto !important;scrollbar-width:thin;scrollbar-color:#C9A84C #e2e8f0;}.cadastros-page [data-testid='stDataFrame']{position:relative;border-radius:8px;}.cadastros-page [data-testid='stDataFrame']::after{content:'';position:absolute;top:0;right:0;width:26px;height:100%;pointer-events:none;background:linear-gradient(to right,rgba(255,255,255,0),rgba(13,27,42,0.12));border-radius:0 8px 8px 0;}.cadastros-page [data-testid='stDataFrame'] [role='columnheader']{position:sticky;top:0;z-index:3;}.cadastros-page [data-testid='stDataFrame'] ::-webkit-scrollbar{height:10px;}.cadastros-page [data-testid='stDataFrame'] ::-webkit-scrollbar-thumb{background:#C9A84C;border-radius:6px;}.cadastros-page [data-testid='stDataFrame'] ::-webkit-scrollbar-track{background:#e2e8f0;border-radius:6px;}@media screen and (max-width:768px){.cadastros-page [data-testid='stDataFrame']{font-size:0.8rem;}}</style>", unsafe_allow_html=True)
    # Verificar se o db está na sessão
    if 'db' not in st.session_state:
        st.error("Erro: Conexão com banco de dados não inicializada")
        return

    # Clientes tem o cabeçalho próprio (tela_clientes); os outros cadastros usam o mesmo estilo de cabeçalho
    if modo != "clientes":
        st.markdown('<div class="cli-eyebrow">Quem trabalha com você</div><h1 class="cli-titulo">Cadastros</h1>'
                    '<div class="cli-sub">Fornecedores, parceiros, assistentes e produtos.</div>', unsafe_allow_html=True)
        st.markdown(CLI_CSS, unsafe_allow_html=True)

    def _aba_clientes():
        tela_clientes()

    def _aba_fornecedores():
        fornecedor_tab1, fornecedor_tab2 = st.tabs(["Cadastrar/Listar", "Importar"])

        with fornecedor_tab1:
            st.subheader("Cadastro de Fornecedores")
            # Form de cadastro de fornecedor
            with st.form("cadastro_fornecedor", clear_on_submit=True):
                nome = st.text_input("Razão Social")
                col1, col2 = st.columns(2)
                with col1:
                    telefone = st.text_input("Telefone")
                    categoria = st.selectbox(
                        "Categoria",
                        ["Produtos", "Serviços", "Marcenaria", "Outro"]
                    )
                    percentual_comissao = st.number_input(
                        "% de Comissão",
                        min_value=0.0,
                        max_value=100.0,
                        value=0.0,
                        step=0.5,
                        help="Percentual de comissão para este fornecedor (entre 0% e 100%)"
                    )
                with col2:
                    pix = st.text_input("Chave PIX")

                endereco = st.text_input("Endereço")
                observacoes = st.text_area("Observações")
                submitted = st.form_submit_button("Cadastrar")

                if submitted:
                    try:
                        st.session_state.db.add_fornecedor(
                            descricao=nome,
                            contato=telefone,
                            categoria=categoria,
                            endereco=endereco,
                            pix=pix,
                            observacoes=observacoes,
                            percentual_comissao=percentual_comissao
                        )
                        st.success("Fornecedor cadastrado com sucesso!")
                        st.session_state['update_fornecedores'] = True
                    except Exception as e:
                        st.error(f"Erro ao cadastrar fornecedor: {str(e)}")

            # Lista de fornecedores
            st.subheader("Lista de Fornecedores")
            try:
                @st.cache_data(ttl=60)
                def load_fornecedores():
                    return st.session_state.db.get_fornecedores()

                if 'update_fornecedores' in st.session_state and st.session_state['update_fornecedores']:
                    load_fornecedores.clear()
                    st.session_state['fornecedores'] = load_fornecedores()
                    st.session_state['update_fornecedores'] = False
                elif 'fornecedores' not in st.session_state:
                    st.session_state['fornecedores'] = load_fornecedores()

                registros = st.session_state['fornecedores']
                
                # Ordenar fornecedores alfabeticamente por descrição (nome)
                if not registros.empty:
                    registros = registros.sort_values('descricao').reset_index(drop=True)

                if not registros.empty:
                    # Definir colunas para exibição
                    colunas = ['id', 'descricao', 'contato', 'categoria', 'endereco', 'pix', 'recorrente', 'percentual_comissao', 'observacoes']
                    rename = {
                        'id': 'ID',
                        'descricao': 'Nome/Razão Social',
                        'contato': 'Contato',
                        'categoria': 'Categoria',
                        'endereco': 'Endereço',
                        'pix': 'PIX',
                        'recorrente': 'Recorrente', 
                        'percentual_comissao': '% Comissão',
                        'observacoes': 'Observações'
                    }

                    # Criar DataFrame para exibição
                    df_display = registros[colunas].copy()
                    df_display.columns = [rename[col] for col in colunas]

                    # Exibir tabela com ordenação por clique no cabeçalho
                    st.dataframe(
                        df_display,
                        use_container_width=True,
                        hide_index=True
                    )

                    # Adicionar botões de ação para cada fornecedor
                    st.write("**Ações para fornecedores:**")
                    
                    # Criar lista de IDs e nomes para seleção
                    fornecedores_options = [f"{row['ID']} - {row['Nome/Razão Social']}" for _, row in df_display.iterrows()]
                    
                    # Dropdown para selecionar fornecedor
                    fornecedor_selecionado = st.selectbox(
                        "Selecione um fornecedor:",
                        fornecedores_options,
                        key="fornecedor_dropdown"
                    )
                    
                    if fornecedor_selecionado:
                        # Extrair ID da seleção (formato: "ID - Nome")
                        fornecedor_id = int(fornecedor_selecionado.split(" - ")[0])
                        
                        # Botões de ação lado a lado
                        col1, col2 = st.columns(2)
                        with col1:
                            if botao_editar("Editar fornecedor", key=f"edit_fornecedor_{fornecedor_id}"):
                                st.session_state['editing_fornecedor_id'] = fornecedor_id
                                st.rerun()
                        
                        with col2:
                            if botao_excluir("Excluir Fornecedor", f"delete_fornecedor_{fornecedor_id}", use_container_width=False):
                                try:
                                    st.session_state.db.delete_fornecedor(fornecedor_id)
                                    st.success(f"Fornecedor ID {fornecedor_id} excluído com sucesso!")
                                    st.session_state['update_fornecedores'] = True
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao excluir fornecedor: {str(e)}")

                else:
                    st.info("Nenhum fornecedor cadastrado.")

            except Exception as e:
                st.error(f"Erro ao carregar lista de fornecedores: {str(e)}")

        # Seção de edição do fornecedor (mantido separado para melhor organização)
        if 'editing_fornecedor_id' in st.session_state:
            st.write("---")
            st.subheader("Editar Fornecedor")
            with st.form("edit_fornecedor_form"):
                fornecedor = registros[registros['id'] == st.session_state['editing_fornecedor_id']].iloc[0]
                edited_data = {}
                edited_data['descricao'] = st.text_input("Nome/Razão Social", value=fornecedor['descricao'])
                edited_data['contato'] = st.text_input("Telefone", value=fornecedor['contato'])
                # Lista de categorias
                categorias = ["Produtos", "Serviços", "Marcenaria", "Outro"]
                
                # Verificar se a categoria do fornecedor existe na lista
                categoria_atual = fornecedor['categoria']
                if categoria_atual not in categorias:
                    categorias.append(categoria_atual)
                
                edited_data['categoria'] = st.selectbox(
                    "Categoria",
                    categorias,
                    index=categorias.index(categoria_atual)
                )
                edited_data['pix'] = st.text_input("PIX", value=fornecedor['pix'])
                edited_data['recorrente'] = st.checkbox("Recorrente", value=fornecedor['recorrente'])
                edited_data['percentual_comissao'] = st.number_input(
                    "% de Comissão",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(fornecedor['percentual_comissao']),
                    step=0.5,
                    help="Percentual de comissão para este fornecedor (entre 0% e 100%)"
                )
                edited_data['observacoes'] = st.text_area("Observações", value=fornecedor['observacoes'])

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Salvar"):
                        try:
                            st.session_state.db.update_fornecedor(
                                st.session_state['editing_fornecedor_id'],
                                **edited_data
                            )
                            del st.session_state['editing_fornecedor_id']
                            st.session_state['update_fornecedores'] = True
                            st.success("Fornecedor atualizado com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao atualizar fornecedor: {str(e)}")

                with col2:
                    if st.form_submit_button("Cancelar"):
                        del st.session_state['editing_fornecedor_id']
                        st.rerun()

        with fornecedor_tab2:
            st.subheader("Importar Fornecedores")

            # Download do template
            template = gerar_template_csv("Fornecedor")
            st.download_button(
                "Baixar Template",
                template,
                "template_fornecedor.csv",
                "text/csv",
                help="Baixe este template, preencha com seus dados e faça upload para importar"
            )

            # Upload e importação
            arquivo = st.file_uploader(
                "Selecione o arquivo CSV",
                type=['csv'],
                key="fornecedor_file_uploader"
            )
            if arquivo:
                if st.button("Importar fornecedores", type="primary"):
                    with st.spinner("Importando dados..."):
                        sucesso, mensagem = importar_cadastros(arquivo, "Fornecedor", st.session_state.db)
                        if sucesso:
                            st.success(mensagem)
                            st.session_state['update_fornecedores'] = True
                        else:
                            st.error(mensagem)

    def _aba_parceiros():
        parceiro_tab1, parceiro_tab2 = st.tabs(["Cadastrar/Listar", "Importar"])

        with parceiro_tab1:
            st.subheader("Cadastro de Parceiros")
            # Form de cadastro de parceiro
            with st.form("cadastro_parceiro", clear_on_submit=True):
                nome = st.text_input("Nome")
                col1, col2 = st.columns(2)
                with col1:
                    telefone = st.text_input("Telefone")
                    area_atuacao = st.text_input("Área de Atuação")
                with col2:
                    tipo_parceria = st.selectbox(
                        "Tipo de Parceria",
                        ["Indicação", "Colaboração", "Projeto Conjunto"]
                    )

                pix = st.text_input("PIX") # Added PIX field
                observacoes = st.text_area("Observações")
                submitted = st.form_submit_button("Cadastrar")

                if submitted:
                    try:
                        st.session_state.db.add_parceiro(
                            nome=nome,
                            telefone=telefone,
                            area_atuacao=area_atuacao,
                            tipo_parceria=tipo_parceria,
                            pix=pix, # Added pix to add_parceiro
                            observacoes=observacoes
                        )
                        st.success("Parceiro cadastrado com sucesso!")
                        st.session_state['update_parceiros'] = True
                    except Exception as e:
                        st.error(f"Erro ao cadastrar parceiro: {str(e)}")

            # Lista de parceiros
            st.subheader("Lista de Parceiros")
            try:
                @st.cache_data(ttl=60)
                def load_parceiros():
                    return st.session_state.db.get_parceiros()

                if 'update_parceiros' in st.session_state and st.session_state['update_parceiros']:
                    st.session_state['parceiros'] = load_parceiros()
                    st.session_state['update_parceiros'] = False
                elif 'parceiros' not in st.session_state:
                    st.session_state['parceiros'] = load_parceiros()

                registros = st.session_state['parceiros']
                
                # Ordenar parceiros alfabeticamente por nome
                if not registros.empty:
                    registros = registros.sort_values('nome').reset_index(drop=True)
                
                if not registros.empty:
                    # Definir colunas para exibição
                    colunas = ['id', 'nome', 'telefone', 'area_atuacao', 'tipo_parceria', 'pix', 'observacoes']
                    rename = {
                        'id': 'ID',
                        'nome': 'Nome',
                        'telefone': 'Telefone',
                        'area_atuacao': 'Área de Atuação',
                        'tipo_parceria': 'Tipo de Parceria',
                        'pix': 'PIX',
                        'observacoes': 'Observações'
                    }

                    # Criar DataFrame para exibição
                    df_display = registros[colunas].copy()
                    df_display.columns = [rename[col] for col in colunas]

                    # Exibir tabela com ordenação por clique no cabeçalho
                    st.dataframe(
                        df_display,
                        use_container_width=True,
                        hide_index=True
                    )

                    # Adicionar botões de ação para cada parceiro
                    st.write("**Ações para parceiros:**")
                    
                    # Criar lista de IDs e nomes para seleção
                    parceiros_options = [f"{row['ID']} - {row['Nome']}" for _, row in df_display.iterrows()]
                    
                    # Dropdown para selecionar parceiro
                    parceiro_selecionado = st.selectbox(
                        "Selecione um parceiro:",
                        parceiros_options,
                        key="parceiro_dropdown"
                    )
                    
                    if parceiro_selecionado:
                        # Extrair ID da seleção (formato: "ID - Nome")
                        parceiro_id = int(parceiro_selecionado.split(" - ")[0])
                        
                        # Botões de ação lado a lado
                        col1, col2 = st.columns(2)
                        with col1:
                            if botao_editar("Editar parceiro", key=f"edit_parceiro_{parceiro_id}"):
                                st.session_state['editing_parceiro_id'] = parceiro_id
                                st.rerun()
                        
                        with col2:
                            if botao_excluir("Excluir Parceiro", f"delete_parceiro_{parceiro_id}", use_container_width=False):
                                try:
                                    st.session_state.db.delete_parceiro(parceiro_id)
                                    st.success(f"Parceiro ID {parceiro_id} excluído com sucesso!")
                                    st.session_state['update_parceiros'] = True
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao excluir parceiro: {str(e)}")

                else:
                    st.info("Nenhum parceiro cadastrado.")

            except Exception as e:
                st.error(f"Erro ao carregar lista de parceiros: {str(e)}")

        # Seção de edição do parceiro (mantido separado para melhor organização)
        if 'editing_parceiro_id' in st.session_state:
            st.write("---")
            st.subheader("Editar Parceiro")
            with st.form("edit_parceiro_form"):
                parceiro = registros[registros['id'] == st.session_state['editing_parceiro_id']].iloc[0]
                edited_data = {}
                edited_data['nome'] = st.text_input("Nome", value=parceiro['nome'])
                edited_data['telefone'] = st.text_input("Telefone", value=parceiro['telefone'])
                edited_data['area_atuacao'] = st.text_input("Área de Atuação", value=parceiro['area_atuacao'])
                # Lista de tipos de parceria
                tipos_parceria = ["Indicação", "Colaboração", "Projeto Conjunto"]
                
                # Verificar se o tipo de parceria do parceiro existe na lista
                tipo_atual = parceiro['tipo_parceria']
                if tipo_atual not in tipos_parceria:
                    tipos_parceria.append(tipo_atual)
                
                edited_data['tipo_parceria'] = st.selectbox(
                    "Tipo de Parceria",
                    tipos_parceria,
                    index=tipos_parceria.index(tipo_atual)
                )
                edited_data['pix'] = st.text_input("PIX", value=parceiro['pix'])
                edited_data['observacoes'] = st.text_area("Observações", value=parceiro['observacoes'])

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Salvar"):
                        try:
                            st.session_state.db.update_parceiro(
                                st.session_state['editing_parceiro_id'],
                                **edited_data
                            )
                            del st.session_state['editing_parceiro_id']
                            st.session_state['update_parceiros'] = True
                            st.success("Parceiro atualizado com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao atualizar parceiro: {str(e)}")

                with col2:
                    if st.form_submit_button("Cancelar"):
                        del st.session_state['editing_parceiro_id']
                        st.rerun()

        with parceiro_tab2:
            st.subheader("Importar Parceiros")

            # Botão para baixar template
            template = gerar_template_csv("Parceiro")
            st.download_button(
                "Baixar Template Parceiro",
                template,
                "template_parceiro.csv",
                "text/csv",
                help="Baixe este template, preencha com seus dados e faça upload para importar parceiros"
            )

            # Upload do arquivo
            arquivo = st.file_uploader(
                "Selecione o arquivo CSV de Parceiros",
                type=['csv'],
                key="parceiro_file_uploader"
            )

            if arquivo:
                if st.button("Importar parceiros", type="primary"):
                    with st.spinner("Importando dados..."):
                        sucesso, mensagem = importar_cadastros(arquivo, "Parceiro", st.session_state.db)
                        if sucesso:
                            st.success(mensagem)
                            st.session_state['update_parceiros'] = True
                        else:
                            st.error(mensagem)

    def _aba_assistentes():
        assistente_tab1, assistente_tab2 = st.tabs(["Cadastrar/Listar", "Importar"])

        with assistente_tab1:
            st.subheader("Cadastro de Assistentes")
            # Form de cadastro de assistente
            with st.form("cadastro_assistente", clear_on_submit=True):
                nome = st.text_input("Nome")
                telefone = st.text_input("Telefone")
                endereco = st.text_input("Endereço")
                pix = st.text_input("Chave PIX")
                observacoes = st.text_area("Observações")
                submitted = st.form_submit_button("Cadastrar")

                if submitted:
                    try:
                        st.session_state.db.add_assistente(
                            nome=nome,
                            telefone=telefone,
                            endereco=endereco,
                            pix=pix,
                            observacoes=observacoes
                        )
                        st.success("Assistente cadastrado com sucesso!")
                        st.session_state['update_assistentes'] = True
                    except Exception as e:
                        st.error(f"Erro ao cadastrar assistente: {str(e)}")

            # Lista de cadastros
            st.subheader(f"Lista de Assistentes")
            try:
                @st.cache_data(ttl=60)
                def load_assistentes():
                    return st.session_state.db.get_assistentes()

                if 'update_assistentes' in st.session_state and st.session_state['update_assistentes']:
                    st.session_state['assistentes'] = load_assistentes()
                    st.session_state['update_assistentes'] = False
                elif 'assistentes' not in st.session_state:
                    st.session_state['assistentes'] = load_assistentes()

                registros = st.session_state['assistentes']
                colunas = ['id','nome', 'telefone', 'endereco', 'pix', 'observacoes']
                rename = {
                    'id': 'ID',
                    'nome': 'Nome',
                    'telefone': 'Telefone',
                    'endereco': 'Endereço',
                    'pix': 'PIX',
                    'observacoes': 'Observações'
                }
                if not registros.empty:
                    # Criar uma cópia do DataFrame original com apenas as colunas desejadas
                    df_display = registros[colunas].copy()

                    # Renomear colunas para exibição
                    df_display.columns = [rename[col] for col in colunas]

                    # Exibir tabela com ordenação por clique no cabeçalho
                    st.dataframe(
                        df_display,
                        use_container_width=True,
                        hide_index=True
                    )

                    # Adicionar botões de ação para cada assistente
                    st.write("**Ações para assistentes:**")
                    
                    # Criar lista de IDs e nomes para seleção
                    assistentes_options = [f"{row['ID']} - {row['Nome']}" for _, row in df_display.iterrows()]
                    
                    # Dropdown para selecionar assistente
                    assistente_selecionado = st.selectbox(
                        "Selecione um assistente:",
                        assistentes_options,
                        key="assistente_dropdown"
                    )
                    
                    if assistente_selecionado:
                        # Extrair ID da seleção (formato: "ID - Nome")
                        assistente_id = int(assistente_selecionado.split(" - ")[0])
                        
                        # Botões de ação lado a lado
                        col1, col2 = st.columns(2)
                        with col1:
                            if botao_editar("Editar assistente", key=f"edit_assistente_{assistente_id}"):
                                st.session_state['editing_assistente_id'] = assistente_id
                                st.rerun()
                        
                        with col2:
                            if botao_excluir("Excluir Assistente", f"delete_assistente_{assistente_id}", use_container_width=False):
                                try:
                                    st.session_state.db.delete_assistente(assistente_id)
                                    st.success(f"Assistente ID {assistente_id} excluído com sucesso!")
                                    st.session_state['update_assistentes'] = True
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao excluir assistente: {str(e)}")

                else:
                    st.info(f"Nenhum assistente cadastrado.")

            except Exception as e:
                st.error(f"Erro ao carregar lista de assistentes: {str(e)}")

        with assistente_tab2:
            st.subheader("Importar Assistentes")

            # Botão para baixar template
            template = gerar_template_csv("Assistente")
            st.download_button(
                "Baixar Template Assistente",
                template,
                "template_assistente.csv",
                "text/csv",
                help="Baixe este template, preencha com seus dados e faça upload para importar assistentes"
            )

            # Upload do arquivo
            arquivo = st.file_uploader(
                "Selecione o arquivo CSV de Assistentes",
                type=['csv'],
                key="assistente_file_uploader"
            )

            if arquivo:
                if st.button("Importar assistentes", key="assistente_import_button", type="primary"):
                    with st.spinner("Importando dados..."):
                        sucesso, mensagem = importar_cadastros(arquivo, "Assistente", st.session_state.db)
                        if sucesso:
                            st.success(mensagem)
                            st.session_state['update_assistentes'] = True
                        else:
                            st.error(mensagem)

        # Seção de edição do assistente (mantido separado para melhor organização)
        if 'editing_assistente_id' in st.session_state:
            st.write("---")
            st.subheader("Editar Assistente")
            with st.form("edit_assistente_form"):
                assistente = registros[registros['id'] == st.session_state['editing_assistente_id']].iloc[0]
                edited_data = {}
                edited_data['nome'] = st.text_input("Nome", value=assistente['nome'])
                edited_data['telefone'] = st.text_input("Telefone", value=assistente['telefone'])
                edited_data['endereco'] = st.text_input("Endereço", value=assistente['endereco'])
                edited_data['pix'] = st.text_input("PIX", value=assistente['pix'])
                edited_data['observacoes'] = st.text_area("Observações", value=assistente['observacoes'])

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Salvar"):
                        try:
                            st.session_state.db.update_assistente(
                                st.session_state['editing_assistente_id'],
                                **edited_data
                            )
                            del st.session_state['editing_assistente_id']
                            st.session_state['update_assistentes'] = True
                            st.success("Assistente atualizado com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao atualizar assistente: {str(e)}")

                with col2:
                    if st.form_submit_button("Cancelar"):
                        del st.session_state['editing_assistente_id']
                        st.rerun()

    # === Aba de Produtos ===
    def _aba_produtos():
        produto_tab1, produto_tab2 = st.tabs(["Cadastrar/Listar", "Importar"])

        with produto_tab2:
            try:
                from utils.componentes_importacao import interface_importacao
                interface_importacao(tipo_cadastro="Produto", db=st.session_state.db,
                                    pagina_titulo="Importação de Produtos")
            except Exception as e:
                st.error(f"Erro ao carregar interface de importação: {str(e)}")
                import traceback
                st.error(traceback.format_exc())

        with produto_tab1:
            col1, col2 = st.columns([1, 1])

            with col1:
                st.subheader("Cadastrar Produto")

                with st.form("form_produto"):
                    nome_produto = input_with_tooltip(
                        "text_input",
                        "Nome do Produto",
                        "Digite o nome comercial do produto que será vendido"
                    )

                    col_desc, col_help_desc = st.columns([4, 1])
                    with col_desc:
                        descricao = st.text_area("Descrição", label_visibility="visible")
                    with col_help_desc:
                        st.markdown(create_tooltip("Descrição detalhada do produto para identificação"), unsafe_allow_html=True)

                    col_cat, col_help_cat = st.columns([4, 1])
                    with col_cat:
                        categoria = st.selectbox("Categoria", ["Organização", "Higiene", "Beleza", "Casa", "Outros"])
                    with col_help_cat:
                        st.markdown(create_tooltip("Categoria para organização e filtros do produto"), unsafe_allow_html=True)

                    col_preco1, col_preco2 = st.columns(2)
                    with col_preco1:
                        preco_custo = input_moeda("Preço de Custo (R$)", "preco_custo_novo", value=0.0, step=1.0)
                    with col_preco2:
                        preco_venda = input_moeda("Preço de Venda (R$)", "preco_venda_novo", value=0.0, step=1.0)

                    c_est, c_min = st.columns(2)
                    estoque = c_est.number_input("Estoque Inicial", min_value=0, value=0)
                    minimo_novo = c_min.number_input("Estoque mínimo", min_value=0, value=None, step=1,
                                                     placeholder="5 se deixar vazio",
                                                     help="Com essa quantidade ou menos, o produto aparece em Repor estoque, em Vendas.")
                    margem = st.number_input("Margem (%)", min_value=0.0, max_value=100.0, value=50.0, format="%.1f")

                    submitted = st.form_submit_button("Cadastrar Produto", type="primary")

                    if submitted and nome_produto:
                        try:
                            nome_produto = nome_produto.strip().title()
                            produto_id = st.session_state.db.add_produto(
                                nome=nome_produto,
                                preco_custo=preco_custo,
                                preco_venda=preco_venda,
                                descricao=descricao,
                                categoria=categoria,
                                estoque=estoque,
                                estoque_minimo=minimo_novo
                            )
                            st.success(f"Produto '{nome_produto}' cadastrado com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao cadastrar produto: {str(e)}")

            with col2:
                st.subheader("Produtos Cadastrados")
                try:
                    produtos_df = st.session_state.db.get_produtos()

                    if not produtos_df.empty:
                        produtos_df = produtos_df.sort_values('nome').reset_index(drop=True)

                        produtos_display = produtos_df.copy()

                        if 'data_cadastro' in produtos_display.columns:
                            def formatar_data_produto(data_cadastro):
                                if isinstance(data_cadastro, str):
                                    try:
                                        data_obj = datetime.strptime(data_cadastro[:10], '%Y-%m-%d')
                                        return data_obj.strftime('%d/%m/%Y')
                                    except:
                                        return data_cadastro
                                else:
                                    try:
                                        return data_cadastro.strftime('%d/%m/%Y')
                                    except:
                                        return str(data_cadastro)

                            produtos_display['data_cadastro'] = produtos_display['data_cadastro'].map(formatar_data_produto)

                        st.dataframe(produtos_display, hide_index=True, use_container_width=True)

                        st.subheader("Gerenciar Produtos")

                        acao = st.radio("Ação", ["Editar", "Excluir"], horizontal=True)

                        produtos_ordenados = sorted(produtos_df['nome'].tolist())

                        produto_selecionado = st.selectbox(
                            f"Selecionar produto para {acao.lower()}",
                            options=["-- Selecione --"] + produtos_ordenados,
                            key="select_produto_gerenciar"
                        )

                        if produto_selecionado != "-- Selecione --":
                            produto_id = produtos_df[produtos_df['nome'] == produto_selecionado]['id'].iloc[0]
                            produto_dados = produtos_df[produtos_df['id'] == produto_id].iloc[0]

                            if acao == "Editar":
                                st.subheader(f"Editar: {produto_selecionado}")

                                with st.form("form_editar_produto"):
                                    nome_edit = st.text_input("Nome do Produto", value=produto_dados['nome'])
                                    descricao_edit = st.text_area("Descrição", value=produto_dados.get('descricao', ''))

                                    categoria_atual = produto_dados.get('categoria', 'Outros')
                                    if categoria_atual == '' or categoria_atual not in ["Organização", "Higiene", "Beleza", "Casa", "Outros"]:
                                        categoria_atual = 'Outros'

                                    categoria_edit = st.selectbox(
                                        "Categoria",
                                        ["Organização", "Higiene", "Beleza", "Casa", "Outros"],
                                        index=["Organização", "Higiene", "Beleza", "Casa", "Outros"].index(categoria_atual)
                                    )

                                    col_edit1, col_edit2 = st.columns(2)
                                    with col_edit1:
                                        preco_custo_edit = input_moeda("Preço de Custo (R$)", f"preco_custo_edit_{produto_dados.get('id')}", value=float(produto_dados.get('preco_custo', 0)), step=1.0)
                                    with col_edit2:
                                        preco_venda_edit = input_moeda("Preço de Venda (R$)", f"preco_venda_edit_{produto_dados.get('id')}", value=float(produto_dados.get('preco_venda', 0)), step=1.0)

                                    c_ee, c_em = st.columns(2)
                                    estoque_edit = c_ee.number_input("Estoque", value=int(produto_dados.get('estoque', 0)), min_value=0)
                                    _min_atual = produto_dados.get('estoque_minimo')
                                    try:
                                        _min_atual = None if _min_atual is None or _min_atual != _min_atual else int(_min_atual)
                                    except (TypeError, ValueError):
                                        _min_atual = None
                                    minimo_edit = c_em.number_input("Estoque mínimo", min_value=0, value=_min_atual, step=1,
                                                                    placeholder="5 se deixar vazio",
                                                                    help="Com essa quantidade ou menos, o produto aparece em Repor estoque, em Vendas.")

                                    submitted_edit = st.form_submit_button("Salvar Alterações", type="primary")

                                    if submitted_edit and nome_edit:
                                        try:
                                            nome_edit = nome_edit.strip().title()
                                            if hasattr(st.session_state.db, 'update_produto'):
                                                st.session_state.db.update_produto(
                                                    produto_id=produto_id,
                                                    nome=nome_edit,
                                                    preco_custo=preco_custo_edit,
                                                    preco_venda=preco_venda_edit,
                                                    descricao=descricao_edit,
                                                    categoria=categoria_edit,
                                                    estoque=estoque_edit,
                                                    estoque_minimo=minimo_edit
                                                )
                                            else:
                                                st.session_state.db.delete_produto(produto_id)
                                                st.session_state.db.add_produto(
                                                    nome=nome_edit,
                                                    preco_custo=preco_custo_edit,
                                                    preco_venda=preco_venda_edit,
                                                    descricao=descricao_edit,
                                                    categoria=categoria_edit,
                                                    estoque=estoque_edit
                                                )
                                            st.success(f"Produto '{nome_edit}' atualizado com sucesso!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Erro ao editar produto: {str(e)}")

                            elif acao == "Excluir":
                                vendas_com_produto = st.session_state.db.verificar_produto_em_vendas(produto_id)

                                if vendas_com_produto > 0:
                                    st.warning(f"Este produto está sendo usado em {vendas_com_produto} venda(s). Não é possível excluir.")
                                else:
                                    if not st.session_state.get('exclusao_produto_confirmada', False):
                                        if botao_excluir("Excluir Produto", "btn_excluir_produto", use_container_width=False):
                                            st.session_state.exclusao_produto_confirmada = True
                                            st.rerun()
                                    else:
                                        st.warning("Confirmar exclusão do produto?")
                                        confirm_col1, confirm_col2 = st.columns(2)

                                        with confirm_col1:
                                            if st.button("Confirmar", type="primary", key="btn_confirmar_exclusao_produto"):
                                                try:
                                                    st.session_state.db.delete_produto(produto_id)
                                                    st.success("Produto excluído com sucesso!")
                                                    st.session_state.exclusao_produto_confirmada = False
                                                    st.rerun()
                                                except Exception as e:
                                                    st.error(f"Erro ao excluir produto: {str(e)}")

                                        with confirm_col2:
                                            if st.button("Cancelar", use_container_width=True, key="btn_cancelar_exclusao_produto"):
                                                st.session_state.exclusao_produto_confirmada = False
                                                st.rerun()
                    else:
                        custom_info("Nenhum produto cadastrado.")

                except Exception as e:
                    st.error(f"Erro ao carregar produtos: {str(e)}")
    # Clientes tem item próprio no menu; os cadastros de apoio ficam juntos em "Cadastros"
    abas = [("Clientes", _aba_clientes)] if modo == "clientes" else []
    if modo != "clientes":
        abas += [("Fornecedores", _aba_fornecedores), ("Parceiros", _aba_parceiros),
                 ("Assistentes", _aba_assistentes), ("Produtos", _aba_produtos)]
        if modo == "todos":
            abas.insert(0, ("Clientes", _aba_clientes))
    if len(abas) == 1:
        abas[0][1]()
    else:
        for tab, (_, render) in zip(st.tabs([n for n, _ in abas]), abas):
            with tab:
                render()

# Removida seção antiga de importação
