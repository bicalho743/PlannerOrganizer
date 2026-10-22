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


def _periodo():
    """(inicio, fim, rótulo) da visão escolhida; a referência anda com os botões de navegação."""
    hoje = datetime.now().date()
    ref = st.session_state.setdefault("ag_ref", hoje)
    c_vis, c_nav = st.columns([1, 2.4], vertical_alignment="center")
    visao = c_vis.segmented_control("Visão", ["Semana", "Mês"], default="Semana", key="ag_visao",
                                    label_visibility="collapsed") or "Semana"
    with c_nav, st.container(key="ag_nav"):
        c_ant, c_rot, c_hoje, c_prox = st.columns([.6, 2.6, 1, .6], vertical_alignment="center")
    passo = timedelta(days=7) if visao == "Semana" else None
    if c_ant.button("", icon=":material/chevron_left:", key="ag_ant", help="Anterior", use_container_width=True):
        ref = ref - passo if passo else (ref.replace(day=1) - timedelta(days=1))
    if c_prox.button("", icon=":material/chevron_right:", key="ag_prox", help="Próximo", use_container_width=True):
        ref = ref + passo if passo else (mes_de(ref)[1] + timedelta(days=1))
    if c_hoje.button("Hoje", key="ag_hoje", use_container_width=True):
        ref = hoje
    st.session_state["ag_ref"] = ref
    if visao == "Semana":
        ini, fim = semana_de(ref)
        rot = (f"{ini.day} a {fim.day} de {MESES[fim.month - 1]}" if ini.month == fim.month
               else f"{ini.day} de {MESES[ini.month - 1]} a {fim.day} de {MESES[fim.month - 1]}")
    else:
        ini, fim = mes_de(ref)
        rot = f"{MESES[ini.month - 1].capitalize()} de {ini.year}"
    c_rot.markdown(f'<div class="ag-periodo">{rot}</div>', unsafe_allow_html=True)
    return ini, fim, visao


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


def show():
    from utils.auth_guard import require_auth
    require_auth()
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown('<h1 class="page-title">Agenda</h1>', unsafe_allow_html=True)
    st.markdown('<div class="ag-intro">Seus compromissos e tudo o que tem data no app: serviços, aniversários, retornos de '
                'pós-organização e contas a receber e a pagar.</div>', unsafe_allow_html=True)
    db = st.session_state.db

    if st.session_state.get("_last_page_rendered") != "Agenda":
        for k in ("ag_sel", "ag_editando", "ag_conf_excluir"):
            st.session_state.pop(k, None)

    col_btn, _ = st.columns([1, 3])
    with col_btn, st.container(key="cta_novo_compromisso"):
        if st.button("Novo compromisso", type="primary", icon=":material/add:", use_container_width=True,
                     key="ag_btn_novo"):
            st.session_state["ag_novo_open"] = not st.session_state.get("ag_novo_open", False)
    if st.session_state.get("ag_novo_open"):
        with st.expander("Novo compromisso", expanded=True):
            if _form_compromisso():
                st.session_state["ag_novo_open"] = False
                st.rerun()

    ini, fim, visao = _periodo()
    try:
        compromissos = db.get_compromissos()
        itens = montar_agenda(ini, fim, compromissos=compromissos, propostas=db.get_propostas(),
                              acoes_pos=db.get_acoes_pos_periodo(ini, fim), financeiro=db.get_financeiro(),
                              clientes=db.get_clientes())
    except Exception as e:
        print(f"[agenda] {e}")
        st.error("Não consegui carregar a agenda agora. Tente de novo em instantes.")
        return

    st.markdown(_legenda(), unsafe_allow_html=True)
    entra, sai = totais(itens)
    if entra or sai:
        st.markdown(f'<div class="ag-resumo">Neste período: a receber <b>{fmt_brl(entra)}</b> · '
                    f'a pagar <b>{fmt_brl(sai)}</b></div>', unsafe_allow_html=True)

    hoje = datetime.now().date()
    dias = [ini + timedelta(days=n) for n in range((fim - ini).days + 1)]
    if visao == "Mês":
        dias = [d for d in dias if any(i["data"] == d for i in itens) or d == hoje]
    if not itens:
        st.markdown('<div class="ag-vazio">Nada marcado neste período. Use “Novo compromisso” para agendar.</div>',
                    unsafe_allow_html=True)
    for d in dias:
        do_dia = [i for i in itens if i["data"] == d]
        if visao == "Mês" and not do_dia and d != hoje:
            continue
        rot = f"{DIAS[d.weekday()]}, {d.day} de {MESES[d.month - 1]}" + (" · hoje" if d == hoje else "")
        st.markdown(f'<div class="ag-dia{" hoje" if d == hoje else ""}">{rot}</div>', unsafe_allow_html=True)
        if not do_dia:
            st.markdown('<div class="ag-vazio" style="padding:4px 0">Livre.</div>', unsafe_allow_html=True)
        for n, i in enumerate(do_dia):
            if i["compromisso_id"]:
                if cartao_clicavel(_html_item(i).replace('class="ag-item"', 'class="kanban-card ag-item"', 1),
                                   key=f"ag_card_{i['compromisso_id']}_{d.isoformat()}",
                                   rotulo=f"Abrir {i['titulo']}"):
                    st.session_state["ag_sel"] = i["compromisso_id"]
                    st.rerun()
            else:
                st.markdown(_html_item(i), unsafe_allow_html=True)

    sel = st.session_state.get("ag_sel")
    if sel and not compromissos.empty:
        linha = compromissos[compromissos["id"] == sel]
        if not linha.empty:
            _dialogo_compromisso(linha.iloc[0].to_dict())
        else:
            st.session_state.pop("ag_sel", None)
