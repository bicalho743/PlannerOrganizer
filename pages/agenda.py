"""
Agenda: compromissos da organizer (ou da assistente) e tudo o que já tem data no app.

Compromisso com valor gera uma receita "A receber" no Financeiro, na data dele
(Database.salvar_compromisso). As regras de montagem ficam em utils/agenda.py.
"""
import html as html_module
from datetime import datetime, time, timedelta

import streamlit as st

from utils.agenda import TIPOS, montar_agenda, mes_de, semana_de, totais
from utils.currency_formatter import fmt_brl
from utils.ui import botao_editar, botao_excluir, cartao_clicavel, input_moeda
from utils.whatsapp_helper import whatsapp_icone_html

DIAS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
         "setembro", "outubro", "novembro", "dezembro"]

CSS = """
<style>
.ag-intro { color: #667085; font-size: .92rem; margin: -6px 0 14px; }
.ag-legenda { display: flex; flex-wrap: wrap; gap: 6px 14px; font-size: .78rem; color: #475467; margin: 2px 0 12px; }
.ag-legenda i { display: inline-block; width: 10px; height: 10px; border-radius: 3px; margin-right: 5px; vertical-align: -1px; }
.ag-periodo { font-weight: 700; color: #101828; font-size: 1rem; text-align: center; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
/* navegação do período numa linha só, também no celular */
.st-key-ag_nav [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: nowrap !important; gap: 6px !important; align-items: center !important; }
.st-key-ag_nav [data-testid="stColumn"] { min-width: 0 !important; width: auto !important; flex: 1 1 auto !important; }
.st-key-ag_nav [data-testid="stColumn"]:nth-child(2) { flex: 3 1 auto !important; }
.ag-resumo { background: #F8F9FB; border: 1px solid #E4E7EC; border-radius: 10px; padding: 9px 14px; font-size: .88rem; color: #344054; margin: 4px 0 14px; }
.ag-dia { font-size: .78rem; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; color: #475467;
          border-bottom: 2px solid #E4E7EC; padding: 4px 2px; margin: 14px 0 8px; }
.ag-dia.hoje { color: var(--modulo); border-color: var(--modulo); }
.ag-item { display: flex; gap: 10px; align-items: flex-start; background: #fff; border: 1px solid #E4E7EC;
           border-left: 4px solid var(--c); border-radius: 8px; padding: 8px 12px; margin-bottom: 6px; }
.ag-item .hora { flex: none; width: 48px; font-size: .82rem; font-weight: 700; color: #344054; font-variant-numeric: tabular-nums; }
.ag-item .corpo { flex: 1; min-width: 0; }
.ag-item .tit { font-weight: 600; font-size: .9rem; color: #101828; overflow-wrap: break-word; }
.ag-item .sub { font-size: .78rem; color: #667085; overflow-wrap: break-word; }
.ag-item .tag { display: inline-block; font-size: .68rem; font-weight: 700; letter-spacing: .03em; text-transform: uppercase;
                color: var(--c); margin-right: 6px; }
.ag-item .val { flex: none; font-weight: 700; font-size: .88rem; font-variant-numeric: tabular-nums; white-space: nowrap; }
.ag-item .ok { color: #067647; font-size: .72rem; font-weight: 600; display: block; text-align: right; }
.kanban-card.ag-item, [class*="st-key-kcard_"]:hover .kanban-card.ag-item { border-left: 4px solid var(--c) !important; }
.ag-vazio { color: #98A2B3; font-size: .9rem; padding: 18px 0; }
</style>
"""


def _legenda():
    return '<div class="ag-legenda">' + "".join(
        f'<span><i style="background:{cor}"></i>{rot}</span>' for rot, cor, _ in TIPOS.values()) + "</div>"


def _html_item(i):
    hora = html_module.escape(i["hora"]) if i["hora"] else "—"
    tit = html_module.escape(str(i["titulo"]))
    sub = html_module.escape(str(i["detalhe"] or ""))
    if i.get("whatsapp"):
        sub += whatsapp_icone_html(i["whatsapp"], "Dar parabéns pelo WhatsApp")
    val = ""
    if i["valor"]:
        cor = "#B42318" if i["tipo"] == "pagar" else "#067647"
        ok = '<span class="ok">recebido</span>' if i["situacao"] == "recebido" else ""
        val = f'<div class="val" style="color:{cor}">{fmt_brl(i["valor"])}{ok}</div>'
    return (f'<div class="ag-item" style="--c:{i["cor"]}"><div class="hora">{hora}</div>'
            f'<div class="corpo"><div class="tit"><span class="tag">{TIPOS[i["tipo"]][0]}</span>{tit}</div>'
            f'<div class="sub">{sub}</div></div>{val}</div>')


def _form_compromisso(c=None):
    """Formulário de novo compromisso (c=None) ou de edição."""
    db = st.session_state.db
    clientes = db.get_clientes()
    nomes = {int(r["id"]): r["nome"] for _, r in clientes.iterrows()} if not clientes.empty else {}
    sufixo = c["id"] if c else "novo"
    with st.form(f"ag_form_{sufixo}", clear_on_submit=c is None):
        titulo = st.text_input("O que é", value=c["titulo"] if c else "",
                               placeholder="Ex.: Diária com a organizer Ana, Visita de orçamento")
        f1, f2 = st.columns(2)
        data = f1.date_input("Dia", value=c["data"] if c else st.session_state.get("ag_ref", datetime.now().date()),
                             format="DD/MM/YYYY")
        hora_txt = (c["hora"] if c else "") or ""
        try:
            hora_ini = datetime.strptime(hora_txt, "%H:%M").time() if hora_txt else None
        except ValueError:
            hora_ini = None
        hora = f2.time_input("Hora (opcional)", value=hora_ini, step=900)
        ids = list(nomes)
        atual = int(c["cliente_id"]) if c and c.get("cliente_id") else None
        cliente_id = st.selectbox("Cliente (opcional)", ids, format_func=lambda i: nomes[i],
                                  index=ids.index(atual) if atual in ids else None,
                                  placeholder="Quem contratou ou para quem é o serviço",
                                  help="Se você é assistente, cadastre a organizer que te contrata como cliente.")
        f3, f4 = st.columns(2)
        local = f3.text_input("Local (opcional)", value=c["local"] if c else "")
        with f4:
            valor = input_moeda("Valor a receber (R$)", f"ag_valor_{sufixo}", value=c["valor"] if c else 0.0,
                                step=50.0, help="Com valor, o compromisso entra em “A receber” no Financeiro.")
        obs = st.text_area("Observações (opcional)", value=c["observacoes"] if c else "", height=80)
        if c is not None and c.get("status_receita") in ("Recebido", "Pago"):
            st.caption("Este valor já foi recebido: mudar aqui não altera o Financeiro.")
        enviar = st.form_submit_button("Salvar compromisso", type="primary", use_container_width=True)
    if enviar:
        if not titulo.strip():
            st.warning("Diga o que é o compromisso.")
            return False
        cid = db.salvar_compromisso(c["id"] if c else None, data=data, titulo=titulo,
                                    hora=hora.strftime("%H:%M") if isinstance(hora, time) else None,
                                    cliente_id=cliente_id, local=local, valor=valor, observacoes=obs)
        if cid:
            st.session_state["ag_ref"] = data
            return True
        st.error("Não consegui salvar agora. Tente de novo.")
    return False


def _dialogo_compromisso(c):
    @st.dialog("Compromisso", width="large")
    def _modal():
        if st.session_state.get("ag_editando") == c["id"]:
            if _form_compromisso(c):
                st.session_state.pop("ag_editando", None)
                st.session_state.pop("ag_sel", None)
                st.rerun()
        else:
            quando = c["data"].strftime("%d/%m/%Y") + (f" às {c['hora']}" if c["hora"] else "")
            st.markdown(f"**{html_module.escape(c['titulo'])}**  \n{quando}")
            linhas = [("Cliente", c["cliente_nome"]), ("Local", c["local"]), ("Observações", c["observacoes"])]
            for rot, v in linhas:
                if v:
                    st.markdown(f"{rot}: {html_module.escape(str(v))}")
            if c["valor"]:
                situ = "recebido" if c["status_receita"] in ("Recebido", "Pago") else "a receber no Financeiro"
                st.markdown(f"Valor: **{fmt_brl(c['valor'])}** ({situ})")
            b1, b2, b3 = st.columns([2, 2, 1.2])
            if c["valor"] and c["status_receita"] == "Pendente" and c.get("transacao_id"):
                if b1.button("Recebi", type="primary", icon=":material/check:", key="ag_receber",
                             use_container_width=True):
                    st.session_state.db.atualizar_status_transacao(int(c["transacao_id"]), "Recebido",
                                                                   datetime.now().date())
                    st.session_state.pop("ag_sel", None)
                    st.rerun()
            with b2:
                if botao_editar("Editar", key="ag_editar", use_container_width=True):
                    st.session_state["ag_editando"] = c["id"]
                    st.rerun()
            with b3:
                if botao_excluir("Excluir", "ag_excluir"):
                    st.session_state["ag_conf_excluir"] = c["id"]
                    st.rerun()
            if st.session_state.get("ag_conf_excluir") == c["id"]:
                extra = " A receita pendente dele sai do Financeiro." if c["status_receita"] == "Pendente" else ""
                st.warning(f"Excluir este compromisso?{extra}")
                e1, e2, _ = st.columns([1, 1, 2])
                with e1:
                    if botao_excluir("Excluir de vez", "ag_excluir_conf"):
                        st.session_state.db.excluir_compromisso(c["id"])
                        st.session_state.pop("ag_conf_excluir", None)
                        st.session_state.pop("ag_sel", None)
                        st.rerun()
                if e2.button("Voltar", key="ag_excluir_voltar", use_container_width=True):
                    st.session_state.pop("ag_conf_excluir", None)
                    st.rerun()
        if st.button("Fechar", key="ag_fechar", type="tertiary"):
            for k in ("ag_sel", "ag_editando", "ag_conf_excluir"):
                st.session_state.pop(k, None)
            st.rerun()
    _modal()


# ---------------------------------------------------------------------------------------------------------------
# Tela nova (calendário do mês + painel do dia), protótipo aprovado em 25/11/2026
# ---------------------------------------------------------------------------------------------------------------
from urllib.parse import quote_plus

from utils import visual
from utils.visual import CSS_PILULA, esc, icone, pilula

SEM_CURTA = ["DOM", "SEG", "TER", "QUA", "QUI", "SEX", "SÁB"]
DIAS_LONGOS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
FILTROS = {"Tudo": None, "Serviços": {"servico"}, "Visitas": {"compromisso"}, "Retornos": {"pos"},
           "Aniversários": {"aniversario"}, "A receber": {"receber"}, "A pagar": {"pagar"}}
COR_BARRA = {"servico": "#0D1B2A", "compromisso": "#C9A84C", "pos": "#C9A84C", "aniversario": "#E8D5A3",
             "receber": "#2F6B4F", "pagar": "#C0533A"}

CSS_NOVO = """
<style>
.ag-eyebrow { font-size: .74rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: #9C7A22; margin: 0 0 4px; }
h1.ag-titulo { margin: 0 !important; padding: 0 !important; font-family: 'Cormorant Garamond', Georgia, serif !important;
               font-size: 2.6rem !important; font-weight: 600 !important; color: var(--navy) !important; line-height: 1.15 !important; }
h1.ag-titulo::after { content: ""; display: block; width: 40px; height: 3px; border-radius: 2px; background: var(--gold); margin-top: 8px; }
.ag-sub { color: #5B6B80; font-size: .98rem; margin: 10px 0 6px; }
.st-key-cta_novo_compromisso { padding-top: 34px; }
.st-key-ag_cal, .st-key-ag_painel { background: #fff; border: 1px solid #E7E2D6 !important; border-radius: 16px; padding: 18px 18px 14px; }
@media (max-width: 640px) {
  .st-key-ag_topo [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: wrap !important; gap: 6px !important; }
  .st-key-ag_topo [data-testid="stColumn"] { min-width: 0 !important; width: auto !important; flex: 1 1 0 !important; }
  .st-key-ag_topo [data-testid="stColumn"]:first-child, .st-key-ag_topo [data-testid="stColumn"]:nth-child(2) { flex: 1 1 100% !important; }
  .st-key-ag_topo [data-testid="stHorizontalBlock"] { height: auto !important; align-items: stretch !important; }
  .ag-mes { font-size: 1.6rem; line-height: 1.3; padding-bottom: 10px; }
}
.ag-mes { font-family: 'Cormorant Garamond', Georgia, serif; font-size: 1.9rem; font-weight: 600; color: var(--navy); line-height: 1.1;
          white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ag-sem { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 6px; margin: 4px 0 2px; }
.ag-sem span { text-align: center; font-size: .7rem; font-weight: 700; letter-spacing: .1em; color: #5B6B80; }
/* grade: 7 colunas sempre lado a lado, também no celular */
.st-key-ag_grade [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: nowrap !important; gap: 6px !important; }
.st-key-ag_grade [data-testid="stColumn"] { min-width: 0 !important; width: auto !important; flex: 1 1 0 !important; }
.st-key-ag_grade [data-testid="stVerticalBlock"] { gap: 6px !important; }
.kanban-card.ag-cel { border: 1px solid #E7E2D6 !important; border-radius: 10px !important; padding: 6px !important; margin: 0 !important;
                      min-height: 92px; box-shadow: none !important; background: #fff; overflow: hidden; }
.kanban-card.ag-cel.semana { min-height: 260px; }
.ag-cel.semana .ag-chip { white-space: normal; }
.ag-cel { word-break: normal !important; }
.kanban-card.ag-cel.fora { background: #FAF8F3; }
.kanban-card.ag-cel.fora .n { color: #B4BCC8; }
.kanban-card.ag-cel.sel { border: 2px solid var(--gold) !important; background: #FFFCF3; }
.ag-cel .n { display: inline-flex; align-items: center; justify-content: center; min-width: 22px; height: 22px; font-size: .78rem;
             font-weight: 700; color: var(--navy); margin-bottom: 4px; }
.ag-cel .n.hoje { background: var(--gold); border-radius: 50%; }
.ag-chip { display: block; font-size: .68rem; font-weight: 600; padding: 2px 5px; border-radius: 5px; margin-top: 3px;
           white-space: nowrap; overflow: hidden; text-overflow: ellipsis; line-height: 1.35; }
.ag-chip.servico { background: #0D1B2A; color: #fff; }
.ag-chip.compromisso { background: #F6EDD3; color: #5C4708; }
.ag-chip.pos { border: 1px solid #C9A84C; color: #5C4708; background: #fff; }
.ag-chip.aniversario { background: #F5F1E8; color: #5C4708; }
.ag-chip.receber { background: #E3F1E8; color: #2F6B4F; }
.ag-chip.pagar { background: #FBE9E7; color: #9B2C2C; }
.ag-chip.mais { background: transparent; color: #5B6B80; padding-left: 2px; }
.ag-dica { font-size: .78rem; color: #5B6B80; margin-top: 10px; }
.ag-p-eyebrow { font-size: .7rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: #9C7A22; }
.ag-p-dia { font-family: 'Cormorant Garamond', Georgia, serif; font-size: 1.45rem; font-weight: 600; color: var(--navy); line-height: 1.15; margin: 2px 0; }
.ag-p-res { font-size: .84rem; color: #5B6B80; margin-bottom: 8px; }
.ag-pi { display: flex; gap: 12px; }
.ag-pi .h { flex: none; width: 46px; font-weight: 700; color: var(--navy); font-variant-numeric: tabular-nums; font-size: .92rem; }
.ag-pi .barra { flex: none; width: 3px; border-radius: 2px; background: var(--c); }
.ag-pi .t { flex: 1; min-width: 0; }
.ag-pi .t b { color: var(--navy); font-size: .95rem; overflow-wrap: anywhere; }
.ag-pi .t > span { display: block; font-size: .82rem; color: #5B6B80; overflow-wrap: anywhere; margin-top: 2px; }
.ag-pi .v { font-weight: 700; white-space: nowrap; font-variant-numeric: tabular-nums; }
[class*="st-key-agpi_"] { border-color: #E7E2D6 !important; border-radius: 12px !important; }
.ag-lnk { display: inline-flex; align-items: center; justify-content: center; min-height: 38px; padding: 4px 10px; width: 100%;
          border-radius: 8px; background: #fff; border: 1px solid #D5DBE3; color: var(--navy) !important; font-weight: 600;
          font-size: .82rem; text-decoration: none !important; box-sizing: border-box; text-align: center; line-height: 1.2; }
.ag-lnk:hover { border-color: var(--gold); color: #7A5F0B !important; }
.st-key-ag_painel [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: nowrap !important; gap: 8px !important; }
.st-key-ag_painel [data-testid="stColumn"] { min-width: 0 !important; flex: 1 1 0 !important; width: auto !important; }
.st-key-ag_painel .stButton > button { min-height: 38px; padding: 4px 8px; }
.st-key-ag_painel .stButton > button p { font-size: .82rem; white-space: normal; line-height: 1.2; }
.st-key-ag_filtro button[aria-checked="true"] { background: var(--navy) !important; border-color: var(--navy) !important; color: #fff !important; }
.st-key-ag_filtro button[aria-checked="true"] p, .st-key-ag_filtro button[aria-checked="true"] * { color: #fff !important; }
.st-key-ag_visao button[aria-checked="true"] { background: #fff !important; border-color: var(--gold) !important; color: var(--navy) !important; }
.st-key-ag_topo [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; align-items: center !important; }
.st-key-ag_topo [data-testid="stColumn"]:not(:first-child) { flex: 0 0 auto !important; width: auto !important; min-width: 0 !important; }
.st-key-ag_topo [data-testid="stColumn"]:first-child { flex: 1 1 auto !important; min-width: 0 !important; }
.st-key-ag_topo .stButton > button { min-width: 44px; padding: 4px 12px; }
.st-key-ag_topo .stButton > button p { white-space: nowrap; }
.st-key-ag_visao button { outline: none !important; box-shadow: none !important; }
.st-key-ag_visao button p { white-space: nowrap; }
.st-key-ag_filtro button p { display: inline-flex; align-items: center; gap: 7px; }
.st-key-ag_filtro button:nth-of-type(n+2) p::before { content: ""; width: 9px; height: 9px; border-radius: 3px; flex: none; }
.st-key-ag_filtro button:nth-of-type(2) p::before { background: #0D1B2A; }
.st-key-ag_filtro button:nth-of-type(3) p::before { background: #F6EDD3; border: 1px solid #C9A84C; }
.st-key-ag_filtro button:nth-of-type(4) p::before { background: #fff; border: 1.5px solid #C9A84C; }
.st-key-ag_filtro button:nth-of-type(5) p::before { background: #E8D5A3; }
.st-key-ag_filtro button:nth-of-type(6) p::before { background: #CDE6D6; }
.st-key-ag_filtro button:nth-of-type(7) p::before { background: #F6D3CD; }
.ag-chip svg { display: inline-block; vertical-align: -1px; margin-right: 3px; }
.ag-cel.semana .ag-chip { word-break: normal; overflow-wrap: break-word; hyphens: auto; }
.ag-pi { margin-bottom: 10px; }
.ag-pi .h .ic { color: #9C7A22; display: inline-flex; }
.st-key-ag_cal { container-type: inline-size; }
@container (max-width: 560px) {
  .ag-mes { padding-bottom: 8px; line-height: 1.3; }
  .st-key-ag_topo [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: wrap !important; row-gap: 8px !important; }
  .st-key-ag_topo [data-testid="stColumn"]:first-child { flex: 1 1 100% !important; }
}
/* tela média: o painel do dia vem embaixo do calendário, com a largura toda */
@media (max-width: 1280px) {
  .st-key-ag_corpo > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: wrap !important; }
  .st-key-ag_corpo > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { flex: 1 1 100% !important; width: 100% !important; }
}
.ag-p-vazio { color: #5B6B80; font-size: .9rem; padding: 8px 0 12px; }
@media (max-width: 640px) {
  h1.ag-titulo { font-size: 2.1rem !important; }
  .st-key-cta_novo_compromisso { padding-top: 0; }
  .st-key-ag_cal { padding: 12px 8px; }
  .st-key-ag_grade [data-testid="stHorizontalBlock"] { gap: 3px !important; }
  .kanban-card.ag-cel { min-height: 54px; padding: 3px !important; }
  .kanban-card.ag-cel.semana { min-height: 120px; }
  .ag-chip { font-size: 0; height: 6px; width: 6px; padding: 0; border-radius: 50%; display: inline-block; margin: 1px; }
  .ag-chip.servico { background: #0D1B2A; } .ag-chip.compromisso, .ag-chip.pos { background: #C9A84C; }
  .ag-chip.aniversario { background: #E8D5A3; } .ag-chip.receber { background: #2F6B4F; } .ag-chip.pagar { background: #C0533A; }
  .ag-chip.mais { display: none; }
  .ag-sem span { font-size: .6rem; letter-spacing: 0; }
  .st-key-ag_topo [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; }
  .st-key-ag_topo [data-testid="stColumn"]:first-child, .st-key-ag_topo [data-testid="stColumn"]:nth-child(2) { flex: 1 1 100% !important; }
  .st-key-ag_topo [data-testid="stColumn"]:nth-child(n+3) { flex: 1 1 0 !important; }
  .st-key-ag_topo .stButton > button { width: 100%; }
}
""" + CSS_PILULA + """
</style>
"""


def _inicio_semana_domingo(d):
    return d - timedelta(days=(d.weekday() + 1) % 7)


def _grade(ref, visao):
    """Dias da grade: semanas de domingo a sábado cobrindo o mês (ou só a semana de ref)."""
    if visao == "Semana":
        ini = _inicio_semana_domingo(ref)
        return ini, ini + timedelta(days=6)
    m_ini, m_fim = mes_de(ref)
    ini = _inicio_semana_domingo(m_ini)
    fim = _inicio_semana_domingo(m_fim) + timedelta(days=6)
    return ini, fim


def _chip(i):
    hora = f"{i['hora']} " if i["hora"] else ""
    tit = i["titulo"]
    ic = ""
    if i["tipo"] == "aniversario":
        tit, ic = tit.split(" ")[0], icone("bolo", 11)
    elif i["tipo"] == "pos":
        ic = icone("retorno", 11)
    elif i["tipo"] in ("receber", "pagar") and i["valor"]:
        tit = f"{fmt_brl(i['valor'])} · {tit}"
    return f'<span class="ag-chip {i["tipo"]}" title="{esc(hora + i["titulo"])}">{ic}{esc(hora + tit)}</span>'


def _cel_html(d, itens, ref, hoje, sel, visao):
    limite = 99 if visao == "Semana" else 3
    cls = "kanban-card ag-cel" + (" semana" if visao == "Semana" else "")
    if visao == "Mês" and d.month != ref.month:
        cls += " fora"
    if d == sel:
        cls += " sel"
    chips = "".join(_chip(i) for i in itens[:limite])
    if len(itens) > limite:
        chips += f'<span class="ag-chip mais">+{len(itens) - limite}</span>'
    return f'<div class="{cls}" lang="pt-BR"><span class="n{" hoje" if d == hoje else ""}">{d.day}</span>{chips}</div>'


def _maps(endereco):
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(endereco)}" if endereco else ""


def _lnk(url, rotulo):
    return f'<a class="ag-lnk" href="{url}" target="_blank" rel="noopener">{rotulo}</a>'


def _ir(pagina):
    st.session_state.current_page = pagina
    st.rerun()


def _painel_item(n, i, db):
    sem_hora = {"aniversario": "bolo", "pos": "retorno", "receber": "receber", "pagar": "pagar",
                "servico": "servico", "compromisso": "visita"}
    hora = esc(i["hora"]) if i["hora"] else f'<span class="ic">{icone(sem_hora.get(i["tipo"], "visita"), 18)}</span>'
    direita = ""
    if i["tipo"] == "servico" and i.get("status"):
        direita = f'<div style="margin-top:6px">{pilula(i["status"])}</div>'
    elif i["valor"]:
        cor = "#9B2C2C" if i["tipo"] == "pagar" else "#2F6B4F"
        direita = f'<div class="v" style="color:{cor};margin-top:4px">{fmt_brl(i["valor"])}</div>'
    with st.container(border=True, key=f"agpi_{n}"):
        st.markdown(f'<div class="ag-pi" style="--c:{COR_BARRA.get(i["tipo"], "#C9A84C")}"><span class="h">{hora}</span>'
                    f'<span class="barra"></span><div class="t"><b>{esc(i["titulo"])}</b><span>{esc(i["detalhe"])}</span>'
                    f'{direita}</div></div>', unsafe_allow_html=True)
        acoes = []
        if i["tipo"] == "compromisso" and i.get("compromisso_id"):
            acoes.append(("btn", "Abrir", lambda: st.session_state.__setitem__("ag_sel", i["compromisso_id"])))
            if i.get("cliente_id"):
                acoes.append(("btn", "Criar proposta", lambda: (st.session_state.__setitem__("kanban_nova_proposta_open", True),
                                                               st.session_state.__setitem__("current_page", "Propostas"))))
        if i["tipo"] == "servico" and i.get("proposta_id"):
            acoes.append(("btn", "Abrir proposta", lambda: (st.session_state.__setitem__("kanban_selected_proposta", i["proposta_id"]),
                                                           st.session_state.__setitem__("current_page", "Propostas"))))
        if i["tipo"] in ("servico", "compromisso") and i.get("endereco"):
            acoes.append(("lnk", "Rota no Maps", _maps(i["endereco"])))
        if i["tipo"] == "aniversario" and i.get("whatsapp"):
            acoes.append(("lnk", "Dar parabéns no WhatsApp", i["whatsapp"]))
        if i["tipo"] == "pos" and i.get("action_id"):
            def _feito(aid=i["action_id"]):
                db.update_post_organization_action(action_id=int(aid), status="FEITO")
            acoes.append(("btn", "Marcar como feito", _feito))
        if i["tipo"] in ("receber", "pagar"):
            acoes.append(("btn", "Abrir no Financeiro", lambda: st.session_state.__setitem__("current_page", "Financeiro")))
        for k, (tipo, rot, alvo) in enumerate(acoes):
            if k % 2 == 0:
                cols = st.columns(2 if len(acoes) - k > 1 else 1)
            with cols[k % 2]:
                if True:
                    if tipo == "lnk":
                        st.markdown(_lnk(alvo, rot), unsafe_allow_html=True)
                    else:
                        st.button(rot, key=f"agpa_{n}_{k}", on_click=alvo, use_container_width=True)


def show():
    from utils.auth_guard import require_auth
    require_auth()
    st.markdown(CSS_NOVO, unsafe_allow_html=True)
    db = st.session_state.db
    hoje = visual.hoje()

    if st.session_state.get("_last_page_rendered") != "Agenda":
        for k in ("ag_sel", "ag_editando", "ag_conf_excluir"):
            st.session_state.pop(k, None)
    sel = st.session_state.setdefault("ag_dia", hoje)
    ref = st.session_state.setdefault("ag_ref", sel)

    c_tit, c_btn = st.columns([4, 1.4], vertical_alignment="top")
    c_tit.markdown('<div class="ag-eyebrow">Cada compromisso no seu lugar</div><h1 class="ag-titulo">Agenda</h1>'
                   '<div class="ag-sub">Serviços, visitas, retornos, aniversários e contas, organizados por dia.</div>',
                   unsafe_allow_html=True)
    with c_btn, st.container(key="cta_novo_compromisso"):
        if st.button("Novo compromisso", icon=":material/add:", use_container_width=True, key="ag_btn_novo"):
            st.session_state["ag_ref"] = sel
            st.session_state["ag_novo_open"] = not st.session_state.get("ag_novo_open", False)
            st.rerun()
    if st.session_state.get("ag_novo_open"):
        with st.expander(f"Novo compromisso · {sel.day:02d}/{sel.month:02d}", expanded=True):
            if _form_compromisso():
                st.session_state["ag_novo_open"] = False
                st.session_state["ag_dia"] = st.session_state.get("ag_ref", sel)
                st.rerun()

    filtro = st.pills("Mostrar", list(FILTROS), default="Tudo", key="ag_filtro", label_visibility="collapsed") or "Tudo"

    visao = st.session_state.get("ag_visao") or "Mês"
    ini, fim = _grade(ref, visao)
    try:
        compromissos = db.get_compromissos()
        itens = montar_agenda(ini, fim, compromissos=compromissos, propostas=db.get_propostas(),
                              acoes_pos=db.get_acoes_pos_periodo(ini, fim), financeiro=db.get_financeiro(),
                              clientes=db.get_clientes(), detalhado=True)
    except Exception as e:
        print(f"[agenda] {e}")
        st.error("Não consegui carregar a agenda agora. Tente de novo em instantes.")
        return
    tipos = FILTROS[filtro]
    if tipos:
        itens = [i for i in itens if i["tipo"] in tipos]
    por_dia = {}
    for i in itens:
        por_dia.setdefault(i["data"], []).append(i)

    col_cal, col_dia = st.container(key="ag_corpo").columns([2.1, 1], gap="medium")
    with col_cal, st.container(key="ag_cal"):
        with st.container(key="ag_topo"):
            c_mes, c_vis, c_ant, c_hoje, c_prox = st.columns([3, 1.6, .55, .8, .55], vertical_alignment="center",
                                                             gap="small")
            if visao == "Semana":
                s_fim = ini + timedelta(days=6)
                rot = (f"{ini.day} a {s_fim.day} de {MESES[s_fim.month - 1]}" if ini.month == s_fim.month
                       else f"{ini.day}/{ini.month:02d} a {s_fim.day}/{s_fim.month:02d}")
            else:
                rot = f"{MESES[ref.month - 1].capitalize()} de {ref.year}"
            c_mes.markdown(f'<div class="ag-mes">{rot}</div>', unsafe_allow_html=True)
            c_vis.segmented_control("Visão", ["Semana", "Mês"], default="Mês", key="ag_visao", label_visibility="collapsed")
            if c_ant.button("", icon=":material/arrow_back:", key="ag_ant", help="Anterior"):
                st.session_state["ag_ref"] = ref - timedelta(days=7) if visao == "Semana" else ref.replace(day=1) - timedelta(days=1)
                st.rerun()
            if c_hoje.button("Hoje", key="ag_hoje"):
                st.session_state["ag_ref"] = st.session_state["ag_dia"] = hoje
                st.rerun()
            if c_prox.button("", icon=":material/arrow_forward:", key="ag_prox", help="Próximo"):
                st.session_state["ag_ref"] = ref + timedelta(days=7) if visao == "Semana" else mes_de(ref)[1] + timedelta(days=1)
                st.rerun()

        st.markdown('<div class="ag-sem">' + "".join(f"<span>{d}</span>" for d in SEM_CURTA) + "</div>",
                    unsafe_allow_html=True)
        with st.container(key="ag_grade"):
            d = ini
            while d <= fim:
                cols = st.columns(7)
                for k in range(7):
                    dia = d + timedelta(days=k)
                    with cols[k]:
                        if cartao_clicavel(_cel_html(dia, por_dia.get(dia, []), ref, hoje, sel, visao),
                                           key=f"agd_{dia.isoformat()}", rotulo=f"Ver o dia {dia.day}/{dia.month}"):
                            st.session_state["ag_dia"] = dia
                            st.rerun()
                d += timedelta(days=7)
        st.markdown('<div class="ag-dica">Toque em um dia para ver os detalhes. Serviços de vários dias aparecem em todos '
                    'os dias do período.</div>', unsafe_allow_html=True)

    with col_dia, st.container(key="ag_painel"):
        do_dia = por_dia.get(sel)
        if do_dia is None:   # dia escolhido fora da grade (mudou de mês): busca só ele
            try:
                do_dia = montar_agenda(sel, sel, compromissos=compromissos, propostas=db.get_propostas(),
                                       acoes_pos=db.get_acoes_pos_periodo(sel, sel), financeiro=db.get_financeiro(),
                                       clientes=db.get_clientes(), detalhado=True)
                if tipos:
                    do_dia = [i for i in do_dia if i["tipo"] in tipos]
            except Exception:
                do_dia = []
        quando = "Hoje" if sel == hoje else ("Amanhã" if sel == hoje + timedelta(days=1) else "")
        contagem = []
        for tipos_, um, varios in ((("servico", "compromisso"), "compromisso", "compromissos"),
                                   (("pos",), "retorno", "retornos"), (("aniversario",), "aniversário", "aniversários"),
                                   (("receber", "pagar"), "conta", "contas")):
            n_ = sum(1 for i in do_dia if i["tipo"] in tipos_)
            if n_:
                contagem.append(f"{n_} {um if n_ == 1 else varios}")
        partes = [quando] if quando else []
        partes.append(", ".join(contagem[:-1]) + " e " + contagem[-1] if len(contagem) > 1
                      else (contagem[0] if contagem else "nada marcado"))
        st.markdown(f'<div class="ag-p-eyebrow">Sua programação</div>'
                    f'<div class="ag-p-dia">{DIAS_LONGOS[sel.weekday()]}, {sel.day} de {MESES[sel.month - 1]}</div>'
                    f'<div class="ag-p-res">{" · ".join(partes)}</div>', unsafe_allow_html=True)
        if not do_dia:
            st.markdown('<div class="ag-p-vazio">Dia livre.</div>', unsafe_allow_html=True)
        for n, i in enumerate(do_dia):
            _painel_item(n, i, db)
        if st.button("Agendar neste dia", icon=":material/add:", key="ag_agendar_dia", use_container_width=True):
            st.session_state["ag_ref"] = sel
            st.session_state["ag_novo_open"] = True
            st.rerun()

    sel_c = st.session_state.get("ag_sel")
    if sel_c and not compromissos.empty:
        linha = compromissos[compromissos["id"] == sel_c]
        if not linha.empty:
            _dialogo_compromisso(linha.iloc[0].to_dict())
        else:
            st.session_state.pop("ag_sel", None)
