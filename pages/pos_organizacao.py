"""
Pós-organização (desenho novo, protótipo "pos"): as mensagens de acompanhamento depois de cada serviço
finalizado. Cada retorno só acompanha se a mensagem foi "enviada" (no banco: status FEITO, via
db.update_post_organization_action); o resto fica pendente com a data prevista.

Tela: números (para enviar hoje, atrasadas, próximos 7 dias, voltaram a contratar), cartões "Para enviar hoje"
com a mensagem pronta (WhatsApp, editar o texto, já enviei, adiar 3 dias), "Próximos dias" e, ao lado, a
jornada da cliente selecionada (etapas, resultado, retorno técnico e nova proposta).
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.whatsapp_helper import whatsapp_link
from utils.visual import esc, icone_whatsapp
from utils import visual

# Templates de fallback caso o banco não retorne (o banco não guarda "gratuito" nem "hint": vêm daqui)
TEMPLATES_FALLBACK = {
    'agradecimento':  {'nome': 'Agradecimento',  'dias_apos': 1,  'emoji': '🙏', 'texto': 'Foi um prazer enorme participar desse momento da sua casa, {nome}. Fico feliz que tudo tenha ficado exatamente como você merecia. Qualquer coisa que precisar, estou por aqui. 🤍', 'gratuito': False, 'hint': ''},
    'acompanhamento': {'nome': 'Acompanhamento', 'dias_apos': 7,  'emoji': '📞', 'texto': 'Oi, {nome}! Passando pra saber como você está se sentindo na sua casa depois da organização. Tudo funcionando bem pra você? 😊', 'gratuito': False, 'hint': ''},
    'ajuste_fino':    {'nome': 'Ajuste fino',    'dias_apos': 30, 'emoji': '🔧', 'texto': 'Oi, {nome}! Gosto de voltar depois de algumas semanas para garantir que tudo ainda está funcionando para você — sem custo, faz parte do meu acompanhamento. Posso passar na sua casa essa semana? 🏡', 'gratuito': True, 'hint': 'Visita gratuita, como cuidado incluído no serviço. É o melhor momento para apresentar o acompanhamento periódico pago, daqui a 30 dias.'},
    'feedback':       {'nome': 'Feedback',        'dias_apos': 45, 'emoji': '💬', 'texto': 'Oi, {nome}! Sua opinião é muito importante pra mim. O que você sentiu de diferença no seu dia a dia depois da organização? Fico feliz em ouvir — mesmo o que ainda pode melhorar. 💬', 'gratuito': False, 'hint': ''},
    'continuidade':   {'nome': 'Continuidade',    'dias_apos': 60, 'emoji': '🤝', 'texto': 'Oi, {nome}! Muitas clientes gostam de manter esse cuidado com a casa de forma contínua — um acompanhamento periódico pra garantir que tudo siga funcionando bem. Se fizer sentido pra você, posso te contar como funciona. 🤝', 'gratuito': False, 'hint': ''},
    'retorno_tecnico':{'nome': 'Retorno Técnico', 'dias_apos': 0,  'emoji': '🔄', 'texto': 'Oi, {nome}! Conforme combinamos, estou passando para agendar nosso retorno técnico. Quando seria um bom momento para você? 🗓️', 'gratuito': False, 'hint': ''},
}

OBJETIVOS_ETAPA = {
    'agradecimento':   'Mensagem elegante de encerramento',
    'acompanhamento':  'Saber como a cliente está se sentindo na casa',
    'ajuste_fino':     'Propor pequenos ajustes após uso real',
    'feedback':        'Colher opinião genuína da experiência',
    'continuidade':    'Oferta elegante de serviço contínuo',
    'retorno_tecnico': 'Visita técnica agendada',
}

# o que lembrar em cada etapa (linha da jornada e "Próximos dias")
LEMBRETE_ETAPA = {
    'agradecimento':   'mensagem de encerramento',
    'acompanhamento':  'saber como ela está na casa',
    'ajuste_fino':     'visita gratuita de ajuste',
    'feedback':        'pedir depoimento',
    'continuidade':    'oferecer acompanhamento periódico',
    'retorno_tecnico': 'visita técnica combinada',
}

ETAPAS_OBRIGATORIAS = ['agradecimento', 'acompanhamento', 'ajuste_fino', 'feedback', 'continuidade']

# ícones de traço de cada etapa (no lugar dos emojis dos modelos)
_TRACOS = {
    'agradecimento':   '<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/>',
    'acompanhamento':  '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2"/>',
    'ajuste_fino':     '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L4 17l3 3 5.3-5.3a4 4 0 0 0 5.4-5.4l-2.5 2.5-2.4-.6-.6-2.4z"/>',
    'feedback':        '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/>',
    'continuidade':    '<path d="M17 2l4 4-4 4"/><path d="M3 11V9a3 3 0 0 1 3-3h15"/><path d="M7 22l-4-4 4-4"/><path d="M21 13v2a3 3 0 0 1-3 3H3"/>',
    'retorno_tecnico': '<path d="M3 11l9-7 9 7v9H3z"/><path d="M9 20v-6h6v6"/>',
    'dica':            '<path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 0 0-4 10.5c.7.7 1 1.5 1 2.5h6c0-1 .3-1.8 1-2.5A6 6 0 0 0 12 3z"/>',
    'ok':              '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
}
# cor da etiqueta de cada etapa (fundo, texto)
COR_ETAPA = {
    'agradecimento': ('#F6EDD3', '#7A5F0B'), 'acompanhamento': ('#E3E8F0', '#0D1B2A'),
    'ajuste_fino': ('#F6EDD3', '#7A5F0B'), 'feedback': ('#E3F1E8', '#2F6B4F'),
    'continuidade': ('#E3E8F0', '#0D1B2A'), 'retorno_tecnico': ('#F6EDD3', '#7A5F0B'),
}
SEM_ABREV = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
MAX_CARTOES = 5      # cartões "Para enviar hoje" à vista; o resto abre em "Mostrar mais"
MAX_PROXIMOS = 8
DIAS_ATRASO = 3      # "Atrasadas": venceu há mais que isso


def _ic(nome, tam=15, cor="currentColor"):
    return (f'<svg width="{tam}" height="{tam}" viewBox="0 0 24 24" fill="none" stroke="{cor}" stroke-width="1.9" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{_TRACOS.get(nome, "")}</svg>')


def formatar_data_br(data):
    try:
        if pd.isna(data):
            return "N/A"
        if isinstance(data, str):
            return data
        return pd.to_datetime(data).strftime('%d/%m/%Y')
    except Exception:
        return str(data) if data else "N/A"


def _etapa(action_type):
    if action_type is None or (isinstance(action_type, float) and pd.isna(action_type)):
        return ''
    return str(action_type).lower().strip()


def get_template(templates, action_type):
    """Info do modelo da etapa: (emoji, nome, texto, dias_apos, objetivo, gratuito, hint).
    O banco não guarda gratuito/hint: completa com o modelo padrão da mesma etapa."""
    etapa = _etapa(action_type)
    padrao = TEMPLATES_FALLBACK.get(etapa, {})
    t = {**padrao, **{k: v for k, v in (templates.get(etapa) or {}).items() if v not in (None, "")}}
    return (
        t.get('emoji', '📌'),
        t.get('nome', etapa.replace('_', ' ').title()),
        t.get('texto') or '',
        t.get('dias_apos', 0),
        OBJETIVOS_ETAPA.get(etapa, ''),
        t.get('gratuito', False),
        t.get('hint', ''),
    )


def _data(v):
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


def _dm(d):
    return f"{d.day:02d}/{d.month:02d}" if d else ""


def _brl(v):
    from utils.currency_formatter import fmt_brl
    txt = fmt_brl(v)
    return txt[:-3] if txt.endswith(",00") else txt


def _iniciais(nome):
    partes = [p for p in str(nome or "").split() if p[:1].isalpha()]
    if not partes:
        return "?"
    return (partes[0][0] + (partes[-1][0] if len(partes) > 1 else "")).upper()


def _primeiro_nome(nome):
    n = str(nome or "").strip()
    return n.split(" ")[0] if n and n != "N/A" else "cliente"


def _servico(r):
    for k in ("proposta_tipo", "proposta_descricao"):
        v = r.get(k)
        if v is not None and str(v).strip() and str(v).strip().lower() != "nan":
            txt = str(v).strip().split("\n")[0]
            return txt if len(txt) <= 40 else txt[:38].rstrip() + "…"
    return "Organização"


def _dias_rotulo(etapa, dias):
    if etapa == "retorno_tecnico":
        return "combinado"
    return "1 dia depois" if dias == 1 else f"{dias} dias"


def _quando_curto(d, hoje):
    n = (d - hoje).days
    if n == 0:
        return "Hoje"
    if n == 1:
        return "Amanhã"
    return f"{SEM_ABREV[d.weekday()]} {d.day}"


CSS = """
<style>
.po-eyebrow { font-size: .74rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: #9C7A22; margin: 0 0 4px; }
h1.po-titulo { margin: 0 !important; padding: 0 !important; font-family: 'Cormorant Garamond', Georgia, serif !important;
               font-size: 2.6rem !important; font-weight: 600 !important; color: var(--navy) !important; line-height: 1.15 !important; }
h1.po-titulo::after { content: ""; display: block; width: 40px; height: 3px; border-radius: 2px; background: var(--gold); margin-top: 8px; }
.po-sub { color: #5B6B80; font-size: .98rem; margin: 10px 0 4px; }
.st-key-po_links_modelos { padding-top: 78px; }
.st-key-po_links_modelos .stButton { display: flex; justify-content: flex-end; }
[class*="st-key-po_links"] button, [class*="st-key-po_links"] button p { color: #9C7A22 !important; font-weight: 700 !important; }
.po-kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin: 16px 0 24px; }
.po-kpi { background: #fff; border: 1px solid #E7E2D6; border-radius: 16px; padding: 16px 18px; min-width: 0; }
.po-kpi .l { font-size: .84rem; color: #5B6B80; }
.po-kpi .v { font-size: 1.65rem; font-weight: 700; color: var(--navy); margin: 4px 0 2px; font-variant-numeric: tabular-nums; }
.po-kpi .s { font-size: .8rem; color: #5B6B80; display: block; }
.po-kpi.hero { background: var(--navy); border-color: var(--navy); }
.po-kpi.hero .l, .po-kpi.hero .s { color: #C7CED8; }
.po-kpi.hero .v { color: var(--gold); }
.po-secao { font-size: .74rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: #4A5B73; margin: 4px 0 10px;
            display: flex; justify-content: space-between; align-items: baseline; }
.po-secao span { letter-spacing: 0; text-transform: none; font-size: .86rem; color: #9C7A22; }
/* cartão de mensagem */
[class*="st-key-pom_"], [class*="st-key-pomon_"] { background: #fff; border-radius: 16px !important; border: 1px solid #E7E2D6 !important;
                                                   padding: 16px 16px 14px !important; gap: 10px !important; }
[class*="st-key-pomon_"] { border: 2px solid var(--gold) !important; }
[class*="st-key-pom"] [data-testid="stMarkdownContainer"], [class*="st-key-kcard_po"] [data-testid="stMarkdownContainer"],
.st-key-po_jornada [data-testid="stMarkdownContainer"], .st-key-po_jornada_auto [data-testid="stMarkdownContainer"] { margin-bottom: 0 !important; }
.st-key-po_links_modelos button p { white-space: nowrap; }
.po-mh { display: flex; gap: 12px; align-items: center; min-width: 0; }
.po-av { flex: none; width: 40px; height: 40px; border-radius: 12px; background: #F6EDD3; color: #9C7A22; display: flex;
         align-items: center; justify-content: center; font-weight: 700; font-size: .95rem; }
.po-mh .t { flex: 1; min-width: 0; }
.po-mh .t b { display: block; color: var(--navy); font-size: 1rem; overflow-wrap: anywhere; }
.po-mh .t span { font-size: .84rem; color: #5B6B80; }
.po-mh .t span.atraso { color: #9B2C2C; font-weight: 600; }
.po-et { flex: none; display: inline-flex; align-items: center; gap: 5px; font-size: .75rem; font-weight: 700; padding: 4px 10px;
         border-radius: 999px; white-space: nowrap; }
.po-msg { background: #F4F7F2; border: 1px solid #E1EADD; border-radius: 4px 14px 14px 14px; padding: 11px 13px; font-size: .92rem;
          color: #22302A; line-height: 1.5; overflow-wrap: anywhere; }
.po-dica { display: flex; gap: 8px; align-items: flex-start; background: #FFF8E6; border: 1px solid #EBD9A6; border-radius: 10px;
           padding: 9px 12px; font-size: .84rem; color: #6B5208; line-height: 1.45; }
.po-dica svg { flex: none; margin-top: 2px; }
.po-wa { display: inline-flex; align-items: center; justify-content: center; min-height: 38px; padding: 4px 14px; border-radius: 8px;
         background: #1F7A4D; color: #fff !important; font-weight: 700; font-size: .86rem; text-decoration: none !important;
         white-space: nowrap; box-sizing: border-box; }
.po-wa:hover { background: #18643F; }
.po-wa { gap: 7px; }
.po-wa-ic { flex: none; display: inline-flex; align-items: center; justify-content: center; width: 20px; height: 20px;
            border-radius: 50%; background: #fff; }
.po-wa.off svg { filter: grayscale(1); opacity: .5; }
.po-wa.off { background: #E4E7EC; color: #98A2B3 !important; pointer-events: none; }
/* linha de botões do cartão: lado a lado, do tamanho do texto, quebrando linha se faltar espaço */
[class*="st-key-pobt_"] > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"],
[class*="st-key-pobt_"] > [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: wrap !important; gap: 8px !important; }
[class*="st-key-pobt_"] [data-testid="stColumn"] { flex: 0 0 auto !important; width: auto !important; min-width: 0 !important; }
[class*="st-key-pobt_"] .stButton > button { min-height: 38px !important; padding: .4rem .8rem !important; color: var(--navy) !important;
                                             border-color: #E7E2D6 !important; }
[class*="st-key-pobt_"] .stButton > button p { white-space: nowrap; font-weight: 700; font-size: .86rem; }
/* cabeçalho do cartão clicável (abre a jornada) */
[class*="st-key-kcard_po"] .po-mh { cursor: pointer; }
[class*="st-key-kcard_po"]:hover .po-mh .t b { text-decoration: underline; text-decoration-color: #C9A84C; }
/* próximos dias */
.po-prx { display: flex; align-items: center; gap: 12px; padding: 11px 14px; background: #fff; border: 1px solid #E7E2D6;
          border-radius: 12px; font-size: .92rem; min-width: 0; }
.po-prx .q { flex: none; width: 70px; font-weight: 700; color: var(--navy); font-size: .84rem; }
.po-prx b { color: var(--navy); white-space: nowrap; }
.po-prx .s { color: #5B6B80; font-size: .84rem; display: inline-flex; gap: 5px; align-items: center; min-width: 0; overflow-wrap: anywhere; }
.po-prx .s svg { flex: none; color: #9C7A22; }
[class*="st-key-kcard_poprx"] { margin-bottom: -6px; }
[class*="st-key-kcard_poprx"]:hover .po-prx, [class*="st-key-kcard_poall"]:hover .po-prx { border-color: #C9A84C; }
.po-vazio { background: #fff; border: 1px solid #E7E2D6; border-radius: 14px; padding: 16px 18px; color: #2F6B4F; font-weight: 600; }
.po-vazio.neutro { color: #5B6B80; font-weight: 400; }
/* jornada */
.st-key-po_jornada, .st-key-po_jornada_auto { background: #fff; border: 1px solid #E7E2D6 !important; border-radius: 16px; padding: 20px !important; }
.po-j-ey { font-size: .72rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: #9C7A22; }
.po-j-nome { font-family: 'Cormorant Garamond', Georgia, serif; font-size: 1.8rem; font-weight: 600; color: var(--navy); line-height: 1.15;
             margin-top: 4px; overflow-wrap: anywhere; }
.po-j-sub { font-size: .84rem; color: #5B6B80; }
.po-tl { margin-top: 14px; }
.po-st { display: flex; gap: 12px; padding-bottom: 16px; position: relative; }
.po-st:before { content: ""; position: absolute; left: 13px; top: 28px; bottom: 0; width: 2px; background: #E6E1D6; }
.po-st:last-child:before { display: none; }
.po-st i { font-style: normal; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
           font-size: .75rem; font-weight: 700; flex-shrink: 0; z-index: 1; }
.po-st.ok i { background: #E3F1E8; color: #2F6B4F; }
.po-st.hj i { background: var(--gold); color: var(--navy); }
.po-st.hj i:after { content: ""; width: 8px; height: 8px; border-radius: 50%; background: var(--navy); }
.po-st.at i { background: #FBE9E7; color: #9B2C2C; }
.po-st.at i:after { content: ""; width: 8px; height: 8px; border-radius: 50%; background: #9B2C2C; }
.po-st.fu i, .po-st.cn i { background: #fff; border: 1.5px solid #D8D2C4; color: #9A968C; }
.po-st b { color: var(--navy); font-size: .92rem; display: flex; gap: 6px; align-items: center; }
.po-st b svg { color: #9C7A22; }
.po-st.cn b { color: #98A2B3; }
.po-st span { font-size: .8rem; color: #5B6B80; display: block; }
.po-st span.atraso { color: #9B2C2C; font-weight: 600; }
.po-st .nota { font-style: italic; }
.po-res-t { font-size: .72rem; letter-spacing: .12em; font-weight: 700; color: #5B6B80; text-transform: uppercase; margin-top: 2px; }
.po-res { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 6px 0 4px; }
.po-res div { background: #FAF8F3; border-radius: 10px; padding: 10px; }
.po-res b { display: block; font-size: 1.1rem; color: var(--navy); }
.po-res span { font-size: .78rem; color: #5B6B80; }
.st-key-po_btn_retorno .stButton > button { min-height: 46px !important; color: var(--navy) !important; font-weight: 700 !important;
                                           border-color: #E7E2D6 !important; }
.po-pergunta { background: #FAF8F3; border: 1px solid #E8D5A3; border-radius: 12px; padding: 14px 18px; margin-bottom: 10px; }
.po-pergunta b { color: var(--navy); }
.po-pergunta span { display: block; font-size: .88rem; color: #5B6B80; margin-top: 2px; }
.po-modelo { border-top: 1px solid #F0ECE3; padding: 10px 0; }
.po-modelo b { color: var(--navy); display: flex; gap: 6px; align-items: center; }
.po-modelo b svg { color: #9C7A22; }
.po-modelo span { font-size: .8rem; color: #5B6B80; }
.po-modelo p { margin: 4px 0 0; font-size: .9rem; color: #22302A; }
/* tela média: a jornada desce para baixo da lista */
@media (max-width: 1280px) {
  .po-kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .st-key-po_corpo > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: wrap !important; }
  .st-key-po_corpo > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { flex: 1 1 100% !important; width: 100% !important; }
  /* a jornada só aparece quando a cliente é escolhida, e vem antes da lista */
  .st-key-po_corpo > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:has(.st-key-po_jornada) { order: -1; }
  .st-key-po_corpo > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:has(.st-key-po_jornada_auto) { display: none; }
}
@media (min-width: 1281px) { .st-key-po_fechar_jornada { display: none; } }
@media (max-width: 640px) {
  h1.po-titulo { font-size: 2.1rem !important; }
  .st-key-po_links_modelos { padding-top: 0; }
  .st-key-po_links_modelos .stButton { justify-content: flex-start; }
  .po-kpi .v { font-size: 1.4rem; }
  .po-mh { flex-wrap: wrap; row-gap: 6px; }
  .po-mh .t { flex: 1 1 calc(100% - 56px); }
  .po-et { margin-left: 52px; }
  .po-prx { flex-wrap: wrap; gap: 2px 12px; }
  .po-prx .s { flex: 1 1 100%; padding-left: 82px; }
}
</style>
"""


def _ir(pagina):
    st.session_state.current_page = pagina
    st.rerun()


def _nova_proposta(cliente_id=None):
    st.session_state["kanban_nova_proposta_open"] = True
    if cliente_id is not None and not pd.isna(cliente_id):
        st.session_state["nova_proposta_cliente_id"] = int(cliente_id)  # a Nova proposta já abre com ela
    _ir("Propostas")


def _marcar_enviada(aid, etapa, pos_id):
    st.session_state.db.update_post_organization_action(action_id=int(aid), status='FEITO')
    st.session_state.pop(f"po_edit_{aid}", None)
    st.toast("Mensagem marcada como enviada.")
    if etapa == 'acompanhamento':
        st.session_state.show_retorno_tecnico_modal = True
        st.session_state.retorno_tecnico_pos_org_id = int(pos_id)
        st.session_state.agendar_retorno = False


def _adiar(aid, venc, hoje):
    base = max(venc or hoje, hoje)
    st.session_state.db.update_post_organization_action(action_id=int(aid), status='PENDENTE',
                                                        due_date=base + timedelta(days=3))
    st.toast(f"Adiada para {_dm(base + timedelta(days=3))}.")


def _salvar_enviada(aid, etapa, pos_id):
    """Caixinha "Enviada" da jornada (desmarcar volta para pendente)."""
    enviada = bool(st.session_state.get(f"poenv_{aid}"))
    st.session_state.db.update_post_organization_action(action_id=int(aid), status='FEITO' if enviada else 'PENDENTE')
    if enviada and etapa == 'acompanhamento':
        st.session_state.show_retorno_tecnico_modal = True
        st.session_state.retorno_tecnico_pos_org_id = int(pos_id)


def _salvar_nota(aid):
    """Só a anotação: não mexe na situação nem na data em que a mensagem foi enviada."""
    from utils.pos_organizacao_dados import salvar_nota
    uid = st.session_state.get("usuario_id") or getattr(st.session_state.db, "usuario_id", None)
    salvar_nota(uid, int(aid), st.session_state.get(f"ponota_{aid}", ""))


def _alternar_edicao(aid):
    """Abre/fecha a edição do texto; ao fechar, guarda o que foi digitado (a caixa some na volta)."""
    k = f"po_edit_{aid}"
    if st.session_state.get(k) and f"po_ta_{aid}" in st.session_state:
        st.session_state[f"po_msg_{aid}"] = st.session_state[f"po_ta_{aid}"]
    st.session_state[k] = not st.session_state.get(k)


def _mensagem(templates, r):
    _, _, texto, _, _, _, _ = get_template(templates, r["action_type"])
    return (texto or "").replace("{nome}", _primeiro_nome(r.get("cliente_nome")))


def _etiqueta(templates, etapa):
    _, nome, _, dias, _, _, _ = get_template(templates, etapa)
    fundo, cor = COR_ETAPA.get(etapa, ('#F6EDD3', '#7A5F0B'))
    return (f'<span class="po-et" style="background:{fundo};color:{cor}">{_ic(etapa, 13)}{esc(nome)} · '
            f'{esc(_dias_rotulo(etapa, dias))}</span>')


def _cartao(r, templates, hoje, selecionado):
    aid, pos_id = int(r["action_id"]), int(r["post_organization_id"])
    etapa = _etapa(r["action_type"])
    venc = _data(r["due_date"]) or hoje
    _, _, _, _, _, gratuito, hint = get_template(templates, etapa)
    final = _data(r.get("data_final_projeto"))
    atraso = (hoje - venc).days
    sub = f'{esc(_servico(r))}{" · finalizado em " + _dm(final) if final else ""}'
    if atraso > 0:
        sub += f' · <span class="atraso">atrasada há {atraso} dia{"s" if atraso > 1 else ""}</span>'
    with st.container(border=True, key=f"{'pomon' if selecionado else 'pom'}_{aid}"):
        with st.container(key=f"kcard_po{aid}"):
            st.markdown(f'<div class="po-mh"><span class="po-av">{esc(_iniciais(r["cliente_nome"]))}</span>'
                        f'<div class="t"><b>{esc(r["cliente_nome"] or "Cliente")}</b><span>{sub}</span></div>'
                        f'{_etiqueta(templates, etapa)}</div>', unsafe_allow_html=True)
            if st.button("Ver a jornada da cliente", key=f"po_sel_{aid}"):
                st.session_state["pos_sel"] = pos_id
                st.session_state["pos_sel_explicito"] = True
                st.session_state["po_rolar"] = True
                st.rerun()
        # texto editado fica guardado na sessão (chave comum, não de widget, para não sumir ao fechar a edição)
        chave_txt = f"po_msg_{aid}"
        if chave_txt not in st.session_state:
            st.session_state[chave_txt] = _mensagem(templates, r)
        if st.session_state.get(f"po_edit_{aid}"):
            st.session_state[chave_txt] = st.text_area("Texto da mensagem", value=st.session_state[chave_txt],
                                                       key=f"po_ta_{aid}", height=110, label_visibility="collapsed")
        else:
            st.markdown(f'<div class="po-msg">{esc(st.session_state[chave_txt]).replace(chr(10), "<br>")}</div>',
                        unsafe_allow_html=True)
        if hint:
            st.markdown(f'<div class="po-dica">{_ic("dica", 15)}<span>{esc(hint)}</span></div>', unsafe_allow_html=True)
        url = whatsapp_link(r.get("cliente_telefone"), st.session_state[chave_txt])
        with st.container(key=f"pobt_{aid}"):
            c1, c2, c3, c4 = st.columns(4)
            ic = f'<span class="po-wa-ic">{icone_whatsapp(15)}</span>'
            editando = bool(st.session_state.get(f"po_edit_{aid}"))
            if editando and url:
                html_wa = (f'<span class="po-wa off" title="Clique em Pronto para enviar o texto editado">{ic}'
                           f'<span>Enviar no WhatsApp</span></span>')
            elif url:
                html_wa = f'<a class="po-wa" href="{esc(url)}" target="_blank" rel="noopener">{ic}<span>Enviar no WhatsApp</span></a>'
            else:
                html_wa = f'<span class="po-wa off" title="Cliente sem telefone cadastrado">{ic}<span>Sem telefone</span></span>'
            c1.markdown(html_wa,
                        unsafe_allow_html=True)
            editando = bool(st.session_state.get(f"po_edit_{aid}"))
            c2.button("Pronto" if editando else "Editar texto", key=f"po_ed_{aid}", on_click=_alternar_edicao, args=(aid,))
            c3.button("Já enviei", key=f"po_ok_{aid}", on_click=_marcar_enviada, args=(aid, etapa, pos_id))
            c4.button("Adiar 3 dias", key=f"po_ad_{aid}", on_click=_adiar, args=(aid, venc, hoje))


def _linha_proximo(r, templates, hoje, key):
    etapa = _etapa(r["action_type"])
    _, nome, _, dias, _, _, _ = get_template(templates, etapa)
    venc = _data(r["due_date"]) or hoje
    lembrete = LEMBRETE_ETAPA.get(etapa, "")
    if etapa == "acompanhamento":
        lembrete = _dias_rotulo(etapa, dias)
    with st.container(key=f"kcard_{key}"):
        st.markdown(f'<div class="po-prx"><span class="q">{_quando_curto(venc, hoje)}</span><b>{esc(r["cliente_nome"] or "Cliente")}</b>'
                    f'<span class="s">{_ic(etapa, 14)}{esc(nome)}{" · " + esc(lembrete) if lembrete else ""}</span></div>',
                    unsafe_allow_html=True)
        if st.button("Ver a jornada da cliente", key=f"btn_{key}"):
            st.session_state["pos_sel"] = int(r["post_organization_id"])
            st.session_state["pos_sel_explicito"] = True
            st.session_state["po_rolar"] = True
            st.rerun()


def _rolar_ate(seletor):
    """Telas estreitas: depois de escolher a cliente, leva a tela até o painel (que fica acima da lista)."""
    import streamlit.components.v1 as components
    components.html(f"""<script>
(function(){{ var w = window.parent; if (w.innerWidth > 1280) return;
  var n = 0, t = setInterval(function(){{ var el = w.document.querySelector('{seletor}');
    if (el) {{ clearInterval(t); el.scrollIntoView({{behavior: 'smooth', block: 'start'}}); }} else if (++n > 30) clearInterval(t); }}, 100);
}})();</script>""", height=0)


def _jornada(pos_id, df, templates, hoje, fin, explicito=False):
    acoes = df[df["post_organization_id"] == pos_id].sort_values(["due_date", "action_id"])
    if acoes.empty:
        return
    r0 = acoes.iloc[0]
    final = _data(r0.get("data_final_projeto"))
    valor = r0.get("proposta_valor")
    try:
        valor = float(valor) if valor is not None and not pd.isna(valor) else 0.0
    except (TypeError, ValueError):
        valor = 0.0
    nome = r0["cliente_nome"] or "Cliente"
    partes = [esc(_servico(r0))] + ([_brl(valor)] if valor else []) + ([f"finalizado em {_dm(final)}"] if final else [])
    passos = ""
    n = 0
    for _, a in acoes.iterrows():
        etapa = _etapa(a["action_type"])
        _, nome_et, _, dias, _, gratuito, _ = get_template(templates, etapa)
        st_ = str(a["status"] or "").upper()
        venc = _data(a["due_date"])
        if etapa != "retorno_tecnico":
            n += 1
        rot = f'{_ic(etapa, 14)}{esc(nome_et)}{" (gratuito)" if gratuito else ""}'
        dias_txt = _dias_rotulo(etapa, dias)
        if st_ == "FEITO":
            env = _data(a.get("completed_at"))
            cls, marca = "ok", _ic("ok", 14)
            det = f"{dias_txt} · enviada{' ' + _dm(env) if env else ''}"
        elif st_ == "PENDENTE":
            if venc and venc < hoje:
                cls, marca = "at", ""
                det = f'{dias_txt} · <span class="atraso" style="display:inline">era para {_dm(venc)}</span>'
            elif venc == hoje:
                cls, marca, det = "hj", "", f"{dias_txt} · hoje"
            else:
                cls, marca = "fu", (str(n) if etapa != "retorno_tecnico" else _ic("retorno_tecnico", 13))
                lemb = LEMBRETE_ETAPA.get(etapa, "")
                det = f"{dias_txt} · {_dm(venc)}" + (f" · {esc(lemb)}" if etapa in ("feedback", "continuidade") else "")
        else:  # registros antigos cancelados: só informativo
            cls, marca, det = "cn", "", f"{dias_txt} · fora do acompanhamento"
        nota = a.get("notes")
        nota_html = (f'<span class="nota">Anotação: {esc(nota)}</span>'
                     if nota is not None and not pd.isna(nota) and str(nota).strip() else "")
        passos += f'<div class="po-st {cls}"><i>{marca}</i><div><b>{rot}</b><span>{det}</span>{nota_html}</div></div>'

    obrig = acoes[acoes["action_type"].astype(str).str.lower() != "retorno_tecnico"]
    enviadas = int((obrig["status"].astype(str).str.upper() == "FEITO").sum())
    pago = 0.0
    if fin is not None and not fin.empty and "proposta_id" in fin.columns:
        f = fin[(fin["proposta_id"] == r0["proposta_id"]) & (fin["status"] == "Recebido")
                & fin["tipo"].astype(str).str.lower().isin(["receita", "receita_a_receber"])]
        pago = float(pd.to_numeric(f["valor"], errors="coerce").fillna(0).sum())

    with st.container(key="po_jornada" if explicito else "po_jornada_auto"):
        with st.container(key="po_fechar_jornada"):
            if st.button("Fechar jornada", key="po_btn_fechar", type="tertiary", icon=":material/close:"):
                st.session_state["pos_sel_explicito"] = False
                st.rerun()
        if st.session_state.pop("po_rolar", False):
            _rolar_ate(".st-key-po_jornada")
        st.markdown(f'<div class="po-j-ey">Jornada da cliente</div><div class="po-j-nome">{esc(nome)}</div>'
                    f'<div class="po-j-sub">{" · ".join(partes)}</div><div class="po-tl">{passos}</div>'
                    f'<div class="po-res-t">Resultado com ela</div>'
                    f'<div class="po-res"><div><b>{enviadas} de {len(obrig)}</b><span>mensagens enviadas</span></div>'
                    f'<div><b>{_brl(pago)}</b><span>já pago</span></div></div>', unsafe_allow_html=True)
        with st.container(key="po_btn_retorno"):
            if st.button("Agendar retorno técnico", key="po_ag_retorno", use_container_width=True):
                st.session_state["po_ag_retorno_aberto"] = not st.session_state.get("po_ag_retorno_aberto", False)
        if st.session_state.get("po_ag_retorno_aberto"):
            data_ret = st.date_input("Data do retorno técnico", value=hoje + timedelta(days=15), min_value=hoje,
                                     format="DD/MM/YYYY", key="po_data_ret_manual")
            if st.button("Confirmar retorno", key="po_conf_ret_manual", type="primary", use_container_width=True):
                if st.session_state.db.add_retorno_tecnico_action(post_organization_id=int(pos_id), due_date=data_ret):
                    st.session_state["po_ag_retorno_aberto"] = False
                    st.toast(f"Retorno técnico marcado para {formatar_data_br(data_ret)}.")
                    st.rerun()
                else:
                    st.error("Não consegui marcar o retorno técnico. Tente de novo.")
        with st.container(key="cta_po_nova"):
            if st.button(f"Nova proposta para {_primeiro_nome(nome)}", icon=":material/add:", key="po_nova_prop",
                         use_container_width=True):
                _nova_proposta(r0.get("cliente_id"))
        with st.expander("Marcar enviadas e anotar"):
            for _, a in acoes.iterrows():
                st_ = str(a["status"] or "").upper()
                if st_ not in ("FEITO", "PENDENTE"):
                    continue
                aid, etapa = int(a["action_id"]), _etapa(a["action_type"])
                _, nome_et, _, _, _, _, _ = get_template(templates, etapa)
                nota = a.get("notes")
                nota = "" if nota is None or pd.isna(nota) else str(nota)
                st.session_state[f"poenv_{aid}"] = st_ == "FEITO"
                st.session_state[f"ponota_{aid}"] = nota
                st.checkbox(f"{nome_et} · enviada", key=f"poenv_{aid}", on_change=_salvar_enviada,
                            args=(aid, etapa, pos_id))
                st.text_input("Anotação", key=f"ponota_{aid}", placeholder="Anotação (opcional)",
                              label_visibility="collapsed", on_change=_salvar_nota, args=(aid,))


def _pergunta_retorno(hoje):
    """Depois do acompanhamento enviado: precisa de retorno técnico? (entre 15 e 30 dias)."""
    pos_org_id = st.session_state.get("retorno_tecnico_pos_org_id")
    st.markdown('<div class="po-pergunta"><b>Precisa de retorno técnico?</b><span>O acompanhamento foi enviado. '
                'Se ela pediu algum ajuste ou visita, marque a data do retorno.</span></div>', unsafe_allow_html=True)
    c1, c2, _ = st.columns([1.4, 1.4, 3])
    if c1.button("Sim, agendar", key="btn_sim_retorno", type="primary", use_container_width=True):
        st.session_state.agendar_retorno = True
    if c2.button("Não precisa", key="btn_nao_retorno", use_container_width=True):
        st.session_state.show_retorno_tecnico_modal = False
        st.session_state.agendar_retorno = False
        st.rerun()
    if st.session_state.get('agendar_retorno', False):
        data_min, data_max = hoje + timedelta(days=15), hoje + timedelta(days=30)
        col_d, col_b = st.columns([2, 1], vertical_alignment="bottom")
        data_retorno = col_d.date_input("Data do retorno técnico (entre 15 e 30 dias)", value=data_min,
                                        min_value=data_min, max_value=data_max, format="DD/MM/YYYY",
                                        key="data_retorno_tecnico")
        if col_b.button("Confirmar", key="btn_confirmar_retorno", use_container_width=True, type="primary"):
            if pos_org_id and st.session_state.db.add_retorno_tecnico_action(post_organization_id=pos_org_id,
                                                                             due_date=data_retorno):
                st.toast(f"Retorno técnico marcado para {formatar_data_br(data_retorno)}.")
                st.session_state.show_retorno_tecnico_modal = False
                st.session_state.agendar_retorno = False
                st.rerun()
            else:
                st.error("Erro ao agendar retorno técnico.")


def _modelos(templates):
    html_ = ""
    for etapa in ETAPAS_OBRIGATORIAS + ['retorno_tecnico']:
        _, nome, texto, dias, objetivo, _, _ = get_template(templates, etapa)
        html_ += (f'<div class="po-modelo"><b>{_ic(etapa, 14)}{esc(nome)}</b><span>{esc(_dias_rotulo(etapa, dias))}'
                  f'{" · " + esc(objetivo.lower()) if objetivo else ""}</span><p>{esc(texto.replace("{nome}", "Ana"))}</p></div>')
    st.markdown(html_, unsafe_allow_html=True)
    st.caption("Para ajustar uma mensagem antes de enviar, use Editar texto no cartão da cliente.")


def _voltaram(df, propostas):
    """Clientes atendidas (com pós-organização) e quantas fecharam outra proposta depois do serviço."""
    if df.empty:
        return 0, 0
    primeira = df.groupby("cliente_id")["data_final_projeto"].min()
    atendidas = len(primeira)
    if propostas is None or propostas.empty:
        return 0, atendidas
    from utils.proposta_status import normalize
    voltaram = 0
    for cid, final in primeira.items():
        final = _data(final)
        ps = propostas[propostas["cliente_id"] == cid]
        for _, p in ps.iterrows():
            quando = _data(p.get("data_proposta")) or _data(p.get("data_inicio"))
            if (final and quando and quando > final
                    and normalize(p.get("status") or "") in ("aprovada", "em_execucao", "finalizada")):
                voltaram += 1
                break
    return voltaram, atendidas


def show():
    from utils.auth_guard import require_auth
    require_auth()
    if 'db' not in st.session_state:
        st.error("Erro: Conexão com banco de dados não inicializada")
        return
    db = st.session_state.db
    hoje = visual.hoje()
    st.markdown(CSS, unsafe_allow_html=True)
    if st.session_state.get("_last_page_rendered") != "PosOrganizacao":
        for k in ("pos_sel", "pos_sel_explicito", "po_mais", "po_ag_retorno_aberto", "po_ver_modelos"):
            st.session_state.pop(k, None)
    abrir = st.session_state.pop("pos_sel_abrir", None)  # vindo da tela Clientes ("Mandar mensagem")
    if abrir:
        st.session_state["pos_sel"] = int(abrir)
        st.session_state["pos_sel_explicito"] = True
        st.session_state["po_rolar"] = True

    c_tit, c_lnk = st.columns([5, 1.15], vertical_alignment="top")
    c_tit.markdown('<div class="po-eyebrow">O serviço acaba, o cuidado continua</div><h1 class="po-titulo">Pós-organização</h1>'
                   '<div class="po-sub">Mensagens no momento certo depois de cada serviço: agradecer, acompanhar, pedir opinião '
                   'e trazer a cliente de volta.</div>', unsafe_allow_html=True)
    with c_lnk, st.container(key="po_links_modelos"):
        ver = st.session_state.get("po_ver_modelos", False)
        if st.button("Fechar mensagens-modelo" if ver else "Ver mensagens-modelo", key="po_btn_modelos", type="tertiary"):
            st.session_state["po_ver_modelos"] = not ver
            st.rerun()

    templates = db.get_post_org_templates() or {}
    if st.session_state.get("po_ver_modelos"):
        with st.container(border=True, key="po_modelos"):
            _modelos(templates)

    from utils.pos_organizacao_dados import acoes_pos, pendentes
    df = acoes_pos(st.session_state.get("usuario_id") or getattr(db, "usuario_id", None))
    if df.empty:
        st.markdown('<div class="po-vazio neutro" style="margin-top:16px">Nenhum acompanhamento ainda. Quando você finalizar '
                    'uma proposta, as mensagens de pós-organização aparecem aqui com a data certa de cada uma.</div>',
                    unsafe_allow_html=True)
        return
    df = df.copy()
    df["venc"] = df["due_date"].apply(_data)
    pend = pendentes(df).copy()
    pend["venc"] = pend["due_date"].apply(_data)
    hoje_df = pend[pend["venc"].apply(lambda d: d is not None and d <= hoje)].sort_values(["venc", "action_id"], ascending=[False, True])
    atrasadas = pend[pend["venc"].apply(lambda d: d is not None and (hoje - d).days > DIAS_ATRASO)]
    prox = pend[pend["venc"].apply(lambda d: d is not None and hoje < d <= hoje + timedelta(days=7))].sort_values(["venc", "action_id"])
    try:
        propostas = db.get_propostas()
    except Exception:
        propostas = pd.DataFrame()
    voltaram, atendidas = _voltaram(df, propostas)
    pct = f" · {voltaram / atendidas:.0%}" if atendidas else ""
    n_hoje = len(hoje_df)
    st.markdown(
        '<div class="po-kpis">'
        f'<div class="po-kpi hero"><div class="l">Para enviar hoje</div><div class="v">{n_hoje}</div>'
        f'<span class="s">{"a mensagem já vem pronta" if n_hoje else "nada para hoje"}</span></div>'
        f'<div class="po-kpi"><div class="l">Atrasadas</div><div class="v" style="color:#8A3B2B">{len(atrasadas)}</div>'
        f'<span class="s">há mais de {DIAS_ATRASO} dias</span></div>'
        f'<div class="po-kpi"><div class="l">Próximos 7 dias</div><div class="v">{len(prox)}</div>'
        f'<span class="s">em {prox["cliente_id"].nunique()} cliente{"s" if prox["cliente_id"].nunique() != 1 else ""}</span></div>'
        f'<div class="po-kpi"><div class="l">Voltaram a contratar</div><div class="v" style="color:#2F6B4F">{voltaram}</div>'
        f'<span class="s">de {atendidas} atendida{"s" if atendidas != 1 else ""}{pct}</span></div>'
        '</div>', unsafe_allow_html=True)

    # cliente da jornada: a escolhida, senão a do primeiro cartão, senão a próxima
    sel = st.session_state.get("pos_sel")
    ids = set(df["post_organization_id"].astype(int))
    if sel not in ids:
        for base in (hoje_df, prox, pend, df):
            if not base.empty:
                sel = int(base.iloc[0]["post_organization_id"])
                break

    try:
        fin = db.get_financeiro()
    except Exception:
        fin = pd.DataFrame()

    col_l, col_r = st.container(key="po_corpo").columns([1.75, 1], gap="medium")
    with col_l:
        if st.session_state.get('show_retorno_tecnico_modal', False):
            _pergunta_retorno(hoje)
        st.markdown(f'<div class="po-secao">Para enviar hoje<span>{n_hoje if n_hoje else ""}</span></div>', unsafe_allow_html=True)
        if hoje_df.empty:
            st.markdown('<div class="po-vazio">Tudo em dia: nenhuma mensagem para enviar hoje.</div>', unsafe_allow_html=True)
        todos = st.session_state.get("po_mais")
        for _, r in (hoje_df if todos else hoje_df.head(MAX_CARTOES)).iterrows():
            _cartao(r, templates, hoje, int(r["post_organization_id"]) == sel)
        if n_hoje > MAX_CARTOES:
            with st.container(key="po_links_mais"):
                if st.button("Mostrar menos" if todos else f"Mostrar mais {n_hoje - MAX_CARTOES}", key="po_btn_mais",
                             type="tertiary"):
                    st.session_state["po_mais"] = not todos
                    st.rerun()

        st.markdown('<div class="po-secao" style="margin-top:22px">Próximos dias</div>', unsafe_allow_html=True)
        futuros = pend[pend["venc"].apply(lambda d: d is not None and d > hoje)].sort_values(["venc", "action_id"])
        if futuros.empty:
            st.markdown('<div class="po-vazio neutro">Nenhuma mensagem marcada para os próximos dias.</div>', unsafe_allow_html=True)
        for _, r in futuros.head(MAX_PROXIMOS).iterrows():
            _linha_proximo(r, templates, hoje, f"poprx{int(r['action_id'])}")

        n_po = df["post_organization_id"].nunique()
        with st.expander(f"Todas as clientes em acompanhamento ({n_po})"):
            resumo = (df.groupby("post_organization_id")
                      .agg(cliente_nome=("cliente_nome", "first"), final=("data_final_projeto", "max"),
                           total=("action_type", lambda s: int((s.astype(str).str.lower() != "retorno_tecnico").sum())))
                      .reset_index())
            env = (df[(df["action_type"].astype(str).str.lower() != "retorno_tecnico")
                      & (df["status"].astype(str).str.upper() == "FEITO")]
                   .groupby("post_organization_id").size())
            resumo["enviadas"] = resumo["post_organization_id"].map(env).fillna(0).astype(int)
            resumo = resumo.sort_values("final", ascending=False)
            for _, p in resumo.iterrows():
                pid = int(p["post_organization_id"])
                final = _data(p["final"])
                with st.container(key=f"kcard_poall{pid}"):
                    st.markdown(f'<div class="po-prx"><b>{esc(p["cliente_nome"] or "Cliente")}</b>'
                                f'<span class="s">{"finalizado em " + _dm(final) + " · " if final else ""}'
                                f'{p["enviadas"]} de {p["total"]} mensagens enviadas</span></div>', unsafe_allow_html=True)
                    if st.button("Ver a jornada da cliente", key=f"po_all_{pid}"):
                        st.session_state["pos_sel"] = pid
                        st.session_state["pos_sel_explicito"] = True
                        st.session_state["po_rolar"] = True
                        st.rerun()

    with col_r:
        if sel is not None:
            _jornada(sel, df, templates, hoje, fin, bool(st.session_state.get("pos_sel_explicito")))
