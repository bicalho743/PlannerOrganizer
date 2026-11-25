"""
Início — o que a organizadora precisa ver ao abrir o sistema:
1. os números do mês (lucro, a receber, a pagar, conversão de propostas);
2. "Para fazer": tudo que pede uma ação hoje ou nos próximos dias, cada item com o botão da ação;
3. funil de propostas, propostas em andamento e aniversariantes do mês.
Sem dados ainda: um passo a passo para começar.
"""
import os
import streamlit as st
from datetime import datetime, timedelta, timezone
import pandas as pd
from utils.currency_formatter import fmt_brl
from utils.whatsapp_helper import whatsapp_link
from utils.visual import CSS_PILULA, esc, pilula, saudacao
from utils import visual

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
         "setembro", "outubro", "novembro", "dezembro"]
MES_ABREV = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
SEMANA = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]

# rótulo e objetivo de cada etapa da pós-organização (mesmos prazos de pages/pos_organizacao.py)
ETAPAS_POS = {
    'agradecimento':   ('Agradecimento', 'D+1', 'mensagem de encerramento'),
    'acompanhamento':  ('Acompanhamento', 'D+7', 'saber como a cliente está se sentindo'),
    'ajuste_fino':     ('Ajuste fino', 'D+30', 'propor pequenos ajustes após o uso'),
    'feedback':        ('Feedback', 'D+45', 'colher a opinião sobre a experiência'),
    'continuidade':    ('Continuidade', 'D+60', 'oferecer o serviço contínuo'),
    'retorno_tecnico': ('Retorno técnico', '', 'visita técnica agendada'),
}
DIAS_FOLLOWUP = 7  # proposta em aberto sem resposta há mais que isso pede follow-up


def _hoje():
    return visual.hoje()


def _data(v):
    """Converte o que vier do banco (date, datetime, Timestamp, texto) em date; None se vazio."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
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


def _num(v):
    try:
        f = float(str(v).replace(",", ".")) if v is not None else 0.0
        return 0.0 if f != f else f
    except (ValueError, TypeError):
        return 0.0


def _dm(d):
    return f"{d.day:02d}/{d.month:02d}"


def _quando(d, hoje):
    """'hoje', 'amanhã', 'há 3 dias', 'em 2 dias' — mais fácil de ler que a data."""
    n = (d - hoje).days
    if n == 0:
        return "hoje"
    if n == 1:
        return "amanhã"
    if n == -1:
        return "ontem"
    return f"há {-n} dias" if n < 0 else f"em {n} dias"


def _ir(pagina):
    st.session_state.current_page = pagina
    st.rerun()


def _primeiro_nome():
    u = st.session_state.get("usuario") or {}
    nome = u.get("nome") if isinstance(u, dict) else getattr(u, "nome", "")
    return (nome or "").split(" ")[0]


def _kpi(rotulo, valor, sub, destaque=False, tom=""):
    """tom: rec (verde), pag (coral) ou conv (azul) — filete colorido no topo do cartão."""
    cls = "ini-kpi destaque" if destaque else f"ini-kpi {tom}".strip()
    return (f'<div class="{cls}"><span class="rot">{rotulo}</span>'
            f'<div class="val">{valor}</div><span class="sub">{sub}</span></div>')


CSS = """
<style>
.ini-eyebrow { font-size: .74rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: #9C7A22; margin: 0 0 4px; }
h1.ini-titulo { margin: 0 !important; padding: 0 !important; font-family: 'Cormorant Garamond', Georgia, serif !important;
                font-size: 2.6rem !important; font-weight: 600 !important; color: var(--navy) !important; line-height: 1.15 !important; }
h1.ini-titulo::after { content: ""; display: block; width: 40px; height: 3px; border-radius: 2px; background: var(--gold); margin-top: 8px; }
.ini-sub { color: #5B6B80; font-size: .98rem; margin: 10px 0 4px; }
.st-key-cta_ini_nova { padding-top: 34px; }
.ini-kpis { display: grid; grid-template-columns: 1.15fr 1fr 1fr 1fr; gap: 14px; margin: 14px 0 26px; }
.ini-kpi { background: #fff; border: 1px solid #E7E2D6; border-radius: 16px; padding: 18px 20px; min-width: 0; }
.ini-kpi .rot { font-size: .7rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; color: #5B6B80; }
.ini-kpi .val { font-size: 1.75rem; font-weight: 700; color: var(--navy); margin: 8px 0 4px; font-variant-numeric: tabular-nums;
                white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ini-kpi .val.verde { color: #2F6B4F; }
.ini-kpi .sub { font-size: .8rem; color: #5B6B80; line-height: 1.4; display: block; }
.ini-kpi.destaque { background: var(--navy); border-color: var(--navy); }
.ini-kpi.destaque .rot { color: var(--gold); }
.ini-kpi.destaque .val { color: #fff; }
.ini-kpi.destaque .sub { color: #C8D1DC; }
.ini-secao { display: flex; justify-content: space-between; align-items: baseline; font-size: .74rem; font-weight: 700;
             letter-spacing: .14em; text-transform: uppercase; color: #4A5B73; margin: 4px 0 10px; }
.ini-secao span { letter-spacing: 0; text-transform: none; font-size: .86rem; color: #9C7A22; }
[class*="st-key-inifz_"] { background: #fff; border-radius: 14px !important; border-color: #E7E2D6 !important; }
.ini-item { display: flex; gap: 14px; align-items: center; min-width: 0; }
.ini-ic { flex: none; width: 40px; height: 40px; border-radius: 10px; background: #F6EDD3; color: #7A5F0B;
          display: flex; align-items: center; justify-content: center; font-size: 1.05rem; font-weight: 700; }
.ini-ic.pag { background: #FBE9E7; color: #9B2C2C; }
.ini-ic.rec { background: #E3F1E8; color: #2F6B4F; }
.ini-txt { min-width: 0; }
.ini-txt b { color: var(--navy); font-size: .98rem; overflow-wrap: anywhere; }
.ini-txt .det { display: block; font-size: .84rem; color: #5B6B80; margin-top: 2px; overflow-wrap: anywhere; }
.ini-atraso { color: #B42318 !important; font-weight: 600; }
.ini-ok { background: #fff; border: 1px solid #E7E2D6; color: #2F6B4F; border-radius: 14px; padding: 16px 18px; font-weight: 600; }
.ini-wa { display: inline-flex; align-items: center; justify-content: center; min-height: 38px; padding: 4px 12px; width: 100%;
          border-radius: 8px; background: #fff; border: 1px solid #D5DBE3; color: var(--navy) !important; font-weight: 600;
          font-size: .84rem; text-decoration: none !important; box-sizing: border-box; text-align: center; line-height: 1.2; }
.ini-wa:hover { border-color: var(--gold); color: #7A5F0B !important; }
.ini-wa.off { color: #98A2B3 !important; pointer-events: none; }
.ini-cartao { background: #fff; border: 1px solid #E7E2D6; border-radius: 16px; padding: 6px 18px; }
.ini-ag { display: flex; gap: 14px; align-items: center; padding: 14px 0; border-bottom: 1px solid #F0ECE2; }
.ini-ag:last-child { border-bottom: 0; }
.ini-ag .h { flex: none; width: 48px; font-weight: 700; color: var(--navy); font-variant-numeric: tabular-nums; }
.ini-ag .barra { flex: none; width: 3px; align-self: stretch; border-radius: 2px; background: var(--c); }
.ini-ag .t { flex: 1; min-width: 0; }
.ini-ag .t b { color: var(--navy); overflow-wrap: anywhere; }
.ini-ag .t span { display: block; font-size: .82rem; color: #5B6B80; overflow-wrap: anywhere; }
.ini-vazio { color: #5B6B80; font-size: .9rem; padding: 14px 0; }
.ini-funil { background: #fff; border: 1px solid #E7E2D6; border-radius: 16px; padding: 18px 20px; }
.ini-funil .bar { display: flex; height: 10px; border-radius: 999px; overflow: hidden; background: #F0ECE2; }
.ini-funil .bar i { display: block; height: 100%; }
.ini-funil .leg { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; margin-top: 14px; }
.ini-funil .leg b { display: block; font-size: 1.1rem; color: var(--navy); font-variant-numeric: tabular-nums; }
.ini-funil .leg span { font-size: .8rem; color: #5B6B80; }
.ini-funil .rod { margin-top: 10px; font-size: .78rem; color: #5B6B80; }
.ini-prop { display: flex; justify-content: space-between; align-items: center; gap: 10px; background: #fff;
            border: 1px solid #E7E2D6; border-radius: 14px; padding: 14px 16px; margin-bottom: 10px; }
.ini-prop b { color: var(--navy); overflow-wrap: anywhere; }
.ini-prop .d { display: block; font-size: .82rem; color: #5B6B80; }
.ini-passo { display: flex; gap: 12px; align-items: center; }
.ini-passo .n { flex: none; width: 28px; height: 28px; border-radius: 50%; background: #EEF1F6; color: var(--navy);
                font-weight: 700; display: flex; align-items: center; justify-content: center; }
.ini-passo .n.ok { background: #E3F1E8; color: #2F6B4F; }
.ini-passo .n.prox { background: var(--gold); color: var(--navy); }
.st-key-ini_links .stButton, .st-key-ini_links3 .stButton > button { border: 0 !important; background: transparent !important; color: #9C7A22 !important;
     font-weight: 700 !important; padding: 0 !important; min-height: 0 !important; box-shadow: none !important; }
@media (max-width: 1100px) { .ini-kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 640px) {
  h1.ini-titulo { font-size: 2.1rem !important; }
  .st-key-cta_ini_nova { padding-top: 0; }
  .ini-kpi .val { font-size: 1.4rem; }
  .ini-funil .leg { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
""" + CSS_PILULA + """
</style>
"""

# cor da barrinha de cada tipo de item da agenda (o mesmo código de cores da tela Agenda)
COR_AGENDA = {"servico": "#0D1B2A", "compromisso": "#C9A84C", "pos": "#C9A84C", "aniversario": "#E8D5A3",
              "receber": "#2F6B4F", "pagar": "#C0533A"}


def _botao_wa(url, rotulo="WhatsApp"):
    if not url:
        return f'<span class="ini-wa off" title="Cliente sem telefone cadastrado">{rotulo}</span>'
    return f'<a class="ini-wa" href="{url}" target="_blank" rel="noopener">{rotulo}</a>'


def _item(n, icone, titulo, detalhe, acao, cls=""):
    """Um cartão de "Para fazer": ícone, texto e a ação ao lado (função que desenha o botão)."""
    with st.container(border=True, key=f"inifz_{n}"):
        c_txt, c_acao = st.columns([5, 2], vertical_alignment="center")
        with c_txt:
            st.markdown(f'<div class="ini-item"><span class="ini-ic {cls}">{icone}</span>'
                        f'<div class="ini-txt"><b>{titulo}</b><span class="det">{detalhe}</span></div></div>',
                        unsafe_allow_html=True)
        with c_acao:
            acao()


def _funil_html(sit, dias):
    """Barra única com as propostas dos últimos `dias` pela situação de agora (escala de cores das pílulas)."""
    partes = [("em_aberto", "em aberto", "#EFE4C4"), ("aprovada", "aprovada(s)", "#C9A84C"),
              ("em_execucao", "em execução", "#0D1B2A"), ("finalizada", "concluída(s)", "#2F6B4F")]
    total = sum(sit[k] for k, _, _ in partes)
    if not total and not sit["recusada"]:
        return f'<div class="ini-funil"><span class="ini-vazio">Nenhuma proposta nos últimos {dias} dias.</span></div>'
    barra = "".join(f'<i style="width:{sit[k] / total * 100:.1f}%;background:{cor}"></i>'
                    for k, _, cor in partes if total and sit[k])
    leg = "".join(f'<div><b>{sit[k]}</b><span>{rot}</span></div>' for k, rot, _ in partes)
    rod = f'<div class="rod">{sit["recusada"]} recusada(s) no período</div>' if sit["recusada"] else ""
    return f'<div class="ini-funil"><div class="bar">{barra}</div><div class="leg">{leg}</div>{rod}</div>'


def _linha_agenda(i):
    hora = esc(i["hora"]) if i["hora"] else "—"
    extra = pilula(i.get("status")) if i["tipo"] == "servico" and i.get("status") else ""
    if i["valor"]:
        extra = f'<b style="white-space:nowrap">{fmt_brl(i["valor"])}</b>'
    return (f'<div class="ini-ag" style="--c:{COR_AGENDA.get(i["tipo"], "#C9A84C")}"><span class="h">{hora}</span>'
            f'<span class="barra"></span><div class="t"><b>{esc(i["titulo"])}</b><span>{esc(i["detalhe"])}</span></div>'
            f'{extra}</div>')


def _aniversario(cli, hoje):
    """Próxima ocorrência do aniversário (guardado como "05/out"; entende também "05/10", datas etc.)."""
    from utils.agenda import dia_mes_aniversario
    dm = dia_mes_aniversario(cli.get("data_aniversario"))
    if not dm:
        return None
    dia, m = dm
    try:
        d = hoje.replace(month=m, day=dia)
    except ValueError:          # 29/02 em ano que não é bissexto
        d = hoje.replace(month=m, day=28)
    return d if d >= hoje else d.replace(year=hoje.year + 1)


def _perfil():
    try:
        from pages.perfil import carregar_perfil
        return carregar_perfil() or {}
    except Exception:
        return {}


def _cabecalho(hoje, sub=""):
    nome = _primeiro_nome()
    c_tit, c_btn = st.columns([4, 1.3], vertical_alignment="top")
    c_tit.markdown(f'<div class="ini-eyebrow">{SEMANA[hoje.weekday()]}, {hoje.day} de {MESES[hoje.month - 1]}</div>'
                   f'<h1 class="ini-titulo">{saudacao()}{", " + esc(nome) if nome else ""}</h1>'
                   + (f'<div class="ini-sub">{sub}</div>' if sub else ""), unsafe_allow_html=True)
    with c_btn, st.container(key="cta_ini_nova"):
        if st.button("Nova proposta", icon=":material/add:", key="ini_nova_proposta", use_container_width=True):
            st.session_state["kanban_nova_proposta_open"] = True
            _ir("Propostas")


def _plural(n, um, varios):
    return f"{n} {um if n == 1 else varios}"


def show():
    from utils.auth_guard import require_auth
    require_auth()
    if 'db' not in st.session_state:
        st.error("Conexão com o banco de dados não inicializada")
        return
    db = st.session_state.db
    hoje = _hoje()
    st.markdown(CSS, unsafe_allow_html=True)

    # ---------- dados ----------
    try:
        clientes = db.get_clientes()
    except Exception:
        clientes = pd.DataFrame()
    try:
        propostas = db.get_propostas()
    except Exception:
        propostas = pd.DataFrame()
    try:
        fin = db.get_financeiro()
    except Exception:
        fin = pd.DataFrame()
    try:
        acoes_pos = db.get_pending_post_actions_for_dashboard()
    except Exception:
        acoes_pos = pd.DataFrame()

    perfil = _perfil()
    if clientes.empty and propostas.empty:
        _cabecalho(hoje, "Vamos montar o seu Planner: siga os primeiros passos abaixo.")
        from utils import onboarding_web
        onboarding_web.mostrar_passos(perfil, clientes, propostas)
        # dados de exemplo só em ambiente de demonstração (nunca para quem assina)
        if os.environ.get("MODO_DEMO") == "1" and st.button("Adicionar dados de exemplo", key="btn_add_test_data_dashboard"):
            db.add_test_data()
            st.rerun()
        return

    from utils.proposta_status import is_ativa, normalize
    tel = {}
    if not clientes.empty:
        tel = dict(zip(clientes["id"], clientes["telefone"]))
    if not propostas.empty:
        propostas = propostas.copy()
        propostas["valor"] = propostas["valor"].apply(_num)
        propostas["st"] = propostas["status"].apply(normalize)
        ativas = propostas[propostas["status"].apply(is_ativa)]
    else:
        ativas = pd.DataFrame()

    # financeiro: receitas e despesas, pendentes ou já pagas
    def _eh(df, tipos, classif):
        return df["tipo"].astype(str).str.lower().isin(tipos) | (df["classificacao"] == classif)
    if not fin.empty:
        fin = fin.copy()
        fin["valor"] = fin["valor"].apply(_num)
        fin["d"] = fin["data"].apply(_data)
        fin["drec"] = fin["data_recebimento"].apply(_data)
        rec = fin[_eh(fin, ["receita", "receita_a_receber"], "contas_a_receber")]
        desp = fin[_eh(fin, ["despesa", "despesa_a_pagar"], "contas_a_pagar")]
        rec_pend = rec[rec["status"] == "Pendente"]
        desp_pend = desp[desp["status"] == "Pendente"]
    else:
        rec_pend = desp_pend = pd.DataFrame(columns=["id", "valor", "d", "descricao"])

    atras_rec = rec_pend[rec_pend["d"].apply(lambda d: bool(d) and d < hoje)] if not rec_pend.empty else rec_pend
    vence_hoje_rec = rec_pend[rec_pend["d"].apply(lambda d: d == hoje)] if not rec_pend.empty else rec_pend
    prox7_pag = desp_pend[desp_pend["d"].apply(lambda d: bool(d) and d <= hoje + timedelta(days=7))] if not desp_pend.empty else desp_pend

    # agenda de hoje (mesma regra da tela Agenda)
    try:
        from utils.agenda import montar_agenda
        agenda_hoje = montar_agenda(hoje, hoje, compromissos=db.get_compromissos(), propostas=db.get_propostas(),
                                    acoes_pos=db.get_acoes_pos_periodo(hoje, hoje), clientes=clientes, detalhado=True)
        agenda_hoje = [i for i in agenda_hoje if i["tipo"] in ("servico", "compromisso")]
    except Exception as e:
        print(f"[inicio] agenda: {e}")
        agenda_hoje = []

    # ---------- "para fazer": monta a lista antes, para o cabeçalho saber quantas são ----------
    fazer = []   # (icone, cls, titulo, detalhe, acao)
    if not acoes_pos.empty:
        try:
            templates = db.get_post_org_templates() or {}
        except Exception:
            templates = {}
        for _, a in acoes_pos.iterrows():
            at = str(a.get("action_type") or "").lower()
            nome_etapa, dmais, objetivo = ETAPAS_POS.get(at, (at.replace("_", " ").title(), "", ""))
            venc = _data(a.get("due_date")) or hoje
            cliente = a.get("cliente_nome") or "cliente"
            txt = (templates.get(at, {}) or {}).get("texto", "")
            url = whatsapp_link(a.get("cliente_telefone"), txt.replace("{nome}", str(cliente).split(" ")[0]) if txt else "")
            aid = a.get("action_id")

            def _acao(url=url, aid=aid, venc=venc):
                st.markdown(_botao_wa(url, "Mandar mensagem"), unsafe_allow_html=True)
                b1, b2 = st.columns(2)
                if b1.button("Feito", key=f"ini_feito_{aid}", type="tertiary", use_container_width=True):
                    db.update_post_organization_action(action_id=aid, status='FEITO')
                    st.rerun()
                if b2.button("Adiar", key=f"ini_adiar_{aid}", type="tertiary", use_container_width=True,
                             help="Adiar 3 dias"):
                    db.update_post_organization_action(action_id=aid, status='PENDENTE', due_date=venc + timedelta(days=3))
                    st.rerun()
            quando = (f'<span class="ini-atraso">venceu {_quando(venc, hoje)}</span>' if venc < hoje
                      else _quando(venc, hoje))
            fazer.append(("↻", "", f"{esc(nome_etapa)} · {esc(cliente)}",
                          f"{esc(objetivo)} {('(' + dmais + ')') if dmais else ''} · proposta Nº {esc(a.get('proposta_numero', ''))} · {quando}",
                          _acao))

    for df_, lado, rotulo in ((rec_pend, "rec", "Receber"), (desp_pend, "pag", "Pagar")):
        if df_.empty:
            continue
        for _, r in df_[df_["d"].apply(lambda d: bool(d) and d <= hoje + timedelta(days=3))].sort_values("d").iterrows():
            atrasado = r["d"] < hoje
            det = ((f'<span class="ini-atraso">venceu {_quando(r["d"], hoje)}</span>' if atrasado
                    else f"vence {_quando(r['d'], hoje)}") + f" ({_dm(r['d'])})")
            fazer.append(("R$", lado, f"{rotulo} {fmt_brl(r['valor'])} · {esc(r.get('descricao') or '')}".strip(" ·"), det,
                          lambda k=r['id'], lado=lado: st.button("Abrir", key=f"ini_{lado}_{k}",
                                                                 use_container_width=True, on_click=st.session_state.__setitem__,
                                                                 args=("current_page", "Financeiro"))))

    if not propostas.empty:
        for _, p in propostas[propostas["st"] == "em_aberto"].iterrows():
            enviada = _data(p.get("data_proposta")) or _data(p.get("data_inicio"))
            if not enviada or (hoje - enviada).days < DIAS_FOLLOWUP:
                continue
            cliente = p.get("cliente_nome") or "cliente"
            msg = (f"Oi, {str(cliente).split(' ')[0]}! Tudo bem? Passando para saber se ficou alguma dúvida "
                   f"sobre a proposta de organização que te enviei. Fico à disposição!")
            url = whatsapp_link(tel.get(p.get("cliente_id")), msg)
            servico = str(p.get("tipo_proposta") or "").strip()
            fazer.append(("✉", "", f"{esc(cliente)} não respondeu a proposta",
                          f"{esc(servico) + ' · ' if servico else ''}{fmt_brl(p['valor'])} · enviada {_quando(enviada, hoje)}",
                          lambda url=url: st.markdown(_botao_wa(url, "Lembrar no WhatsApp"), unsafe_allow_html=True)))

    if not clientes.empty and "data_aniversario" in clientes.columns:
        for _, c in clientes.iterrows():
            d = _aniversario(c, hoje)
            if not d or (d - hoje).days > 7:
                continue
            primeiro = str(c["nome"]).split(" ")[0]
            url = whatsapp_link(c.get("telefone"), f"Feliz aniversário, {primeiro}! Desejo um novo ciclo leve e cheio de alegria. 💛")
            fazer.append(("🎂", "", f"Aniversário de {esc(c['nome'])}", f"{_quando(d, hoje).capitalize()} ({_dm(d)})",
                          lambda url=url: st.markdown(_botao_wa(url, "Dar parabéns"), unsafe_allow_html=True)))

    n_serv = len(agenda_hoje)
    partes = []
    if n_serv:
        partes.append(_plural(n_serv, "compromisso hoje", "compromissos hoje"))
    if fazer:
        partes.append(_plural(len(fazer), "coisa para resolver", "coisas para resolver"))
    sub = ("Você tem " + " e ".join(partes) + ".") if partes else "Nada pendente para hoje. Bom trabalho!"
    _cabecalho(hoje, sub)

    from utils import onboarding_web
    onboarding_web.mostrar_passos(perfil, clientes, propostas)

    # ---------- números do mês ----------
    from utils.indicadores import movimentos, entrou_gastou, funil, funil_situacao
    entrou, gastou = entrou_gastou(movimentos(fin), hoje.year, hoje.month)
    fn = funil(propostas, hoje)
    conv = fn["conversao"]
    if len(atras_rec):
        sub_rec = f'<span class="ini-atraso">{len(atras_rec)} em atraso</span>'
    else:
        sub_rec = _plural(len(rec_pend), "lançamento", "lançamentos") + (f" · {len(vence_hoje_rec)} vence hoje" if len(vence_hoje_rec) else "")
    st.markdown(
        '<div class="ini-kpis">'
        f'<div class="ini-kpi destaque"><span class="rot">Lucro de {MESES[hoje.month - 1]}</span>'
        f'<div class="val">{fmt_brl(entrou - gastou)}</div><span class="sub">entrou {fmt_brl(entrou)} · gastou {fmt_brl(gastou)}</span></div>'
        f'<div class="ini-kpi"><span class="rot">A receber</span><div class="val verde">{fmt_brl(rec_pend["valor"].sum())}</div>'
        f'<span class="sub">{sub_rec}</span></div>'
        f'<div class="ini-kpi"><span class="rot">A pagar</span><div class="val">{fmt_brl(desp_pend["valor"].sum())}</div>'
        f'<span class="sub">{_plural(len(desp_pend), "conta", "contas")}'
        f'{" · " + str(len(prox7_pag)) + " vence(m) em 7 dias" if len(prox7_pag) else ""}</span></div>'
        f'<div class="ini-kpi"><span class="rot">Conversão · {fn["dias"]} dias</span>'
        f'<div class="val">{f"{conv:.0%}" if conv is not None else "—"}</div>'
        f'<span class="sub">{(str(fn["fechadas"]) + " de " + str(fn["fechadas"] + fn["recusadas"]) + " propostas aprovadas") if conv is not None else "nenhuma proposta respondida ainda"}</span></div>'
        '</div>', unsafe_allow_html=True)

    col_fazer, col_lado = st.columns([1.2, 1], gap="large")

    with col_fazer:
        st.markdown(f'<div class="ini-secao">Para fazer<span>{_plural(len(fazer), "pendência", "pendências") if fazer else ""}</span></div>',
                    unsafe_allow_html=True)
        if not fazer:
            st.markdown('<div class="ini-ok">✓ Tudo em dia: nenhuma ação pendente.</div>', unsafe_allow_html=True)
        for n, (icone, cls, titulo, det, acao) in enumerate(fazer):
            _item(n, icone, titulo, det, acao, cls)

        c_s, c_l = st.columns([3, 1.2], vertical_alignment="bottom")
        c_s.markdown('<div class="ini-secao" style="margin:22px 0 0">Hoje na agenda</div>', unsafe_allow_html=True)
        with c_l, st.container(key="ini_links"):
            if st.button("Abrir agenda →", key="ini_ir_agenda", type="tertiary", use_container_width=True):
                st.session_state["ag_dia"] = hoje
                _ir("Agenda")
        if agenda_hoje:
            st.markdown('<div class="ini-cartao">' + "".join(_linha_agenda(i) for i in agenda_hoje) + '</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<div class="ini-cartao"><div class="ini-vazio">Nenhum serviço ou visita marcado para hoje.</div></div>',
                        unsafe_allow_html=True)

    with col_lado:
        st.markdown(f'<div class="ini-secao">Funil de propostas · {fn["dias"]} dias</div>', unsafe_allow_html=True)
        st.markdown(_funil_html(funil_situacao(propostas, hoje), fn["dias"]), unsafe_allow_html=True)

        st.markdown('<div class="ini-secao" style="margin-top:22px">Propostas em andamento</div>', unsafe_allow_html=True)
        if ativas.empty:
            st.markdown('<div class="ini-cartao"><div class="ini-vazio">Nenhuma proposta em andamento.</div></div>',
                        unsafe_allow_html=True)
        else:
            ordem = {"em_execucao": 0, "aprovada": 1, "em_aberto": 2}
            lista = ativas.assign(_o=ativas["st"].map(ordem).fillna(3)).sort_values(["_o", "valor"], ascending=[True, False])
            html_ = ""
            for _, p in lista.head(6).iterrows():
                servico = str(p.get("tipo_proposta") or "").strip()
                html_ += (f'<div class="ini-prop"><div><b>{esc(p.get("cliente_nome") or "—")}</b>'
                          f'<span class="d">{esc(servico) + " · " if servico else ""}{fmt_brl(p["valor"])} · Nº {esc(p.get("numero"))}</span></div>'
                          f'{pilula(p["st"])}</div>')
            st.markdown(html_, unsafe_allow_html=True)
        with st.container(key="ini_links3"):
            if st.button("Ver todas as propostas →", key="ini_ir_propostas", type="tertiary", use_container_width=True):
                _ir("Propostas")
