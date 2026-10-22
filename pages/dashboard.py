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
    return datetime.now(timezone(timedelta(hours=-3))).date()


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
h1.ini-titulo { margin: 0 0 2px !important; padding: 0 !important; font-family: 'Cormorant Garamond', Georgia, serif !important; font-size: 2.3rem !important; font-weight: 600 !important; color: var(--navy) !important; line-height: 1.2 !important; }
.ini-data { color: #667085; font-size: 0.92rem; margin-bottom: 18px; }
.ini-kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-bottom: 22px; }
.ini-kpi { background: #fff; border: 1px solid #E4E7EC; border-radius: 12px; padding: 16px 18px; }
.ini-kpi .rot { font-size: 0.72rem; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: #667085; }
.ini-kpi .val { font-size: 1.55rem; font-weight: 700; color: #101828; margin: 4px 0 2px; font-variant-numeric: tabular-nums; }
.ini-kpi .sub { font-size: 0.8rem; color: #667085; line-height: 1.4; display: block; }
.ini-kpi.rec { border-top: 3px solid #2F855A; }
.ini-kpi.pag { border-top: 3px solid #D9653B; }
.ini-kpi.conv { border-top: 3px solid #3D6BB3; }
.ini-kpi.rec .rot { color: #2F855A; }
.ini-kpi.pag .rot { color: #C2552E; }
.ini-kpi.conv .rot { color: #3D6BB3; }
.ini-kpi.destaque { background: var(--navy); border-color: var(--navy); border-top: 3px solid var(--gold); }
.ini-kpi.destaque .rot { color: var(--gold); }
.ini-kpi.destaque .sub { color: #C8D1DC; }
.ini-kpi.destaque .val { color: #fff; }
.ini-secao { font-size: 0.78rem; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: #667085; margin: 6px 0 8px; }
.ini-secao::before { content: ""; display: inline-block; width: 14px; height: 2px; background: var(--gold); margin-right: 8px; vertical-align: 3px; }
.ini-item { display: flex; gap: 12px; align-items: flex-start; }
.ini-tag { flex: none; font-size: 0.7rem; font-weight: 600; padding: 3px 8px; border-radius: 999px; margin-top: 2px; white-space: nowrap; }
.ini-tag.pos { background: #EEF1F6; color: var(--navy); }
.ini-tag.rec { background: #ECFDF3; color: #067647; }
.ini-tag.pag { background: #FEF3F2; color: #B42318; }
.ini-tag.prop { background: #FFF6E5; color: #8A5A00; }
.ini-tag.niver { background: #FDF2FA; color: #A3195B; }
.ini-txt b { color: #101828; }
.ini-txt .det { display: block; font-size: 0.82rem; color: #667085; margin-top: 2px; }
.ini-atraso { color: #B42318 !important; font-weight: 600; }
.ini-ok { background: #F6FEF9; border: 1px solid #D1FADF; color: #067647; border-radius: 12px; padding: 14px 16px; font-weight: 500; }
.ini-wa { display: inline-flex; align-items: center; justify-content: center; height: 38px; padding: 0 14px; width: 100%;
          border-radius: 8px; background: #25D366; color: #fff !important; font-weight: 600; font-size: 0.85rem;
          text-decoration: none !important; box-sizing: border-box; }
.ini-wa:hover { background: #1EBE5A; }
.ini-wa.off { background: #E4E7EC; color: #98A2B3 !important; pointer-events: none; }
.ini-lin { display: flex; justify-content: space-between; gap: 10px; padding: 8px 0; border-bottom: 1px solid #F2F4F7; font-size: 0.9rem; }
.ini-lin:last-child { border-bottom: 0; }
.ini-lin span { color: #475467; }
.ini-lin b { font-variant-numeric: tabular-nums; white-space: nowrap; }
.ini-st { font-size: 0.7rem; font-weight: 600; padding: 2px 8px; border-radius: 999px; margin-left: 6px; }
.ini-st.em_aberto { background: #FFF6E5; color: #8A5A00; }
.ini-st.aprovada { background: #ECFDF3; color: #067647; }
.ini-st.em_execucao { background: #EEF4FF; color: #3538CD; }
.ini-passo { display: flex; gap: 12px; align-items: center; }
.ini-passo .n { flex: none; width: 28px; height: 28px; border-radius: 50%; background: #EEF1F6; color: var(--navy);
                font-weight: 700; display: flex; align-items: center; justify-content: center; }
.ini-passo .n.ok { background: #ECFDF3; color: #067647; }
.ini-fu { display: grid; grid-template-columns: 84px 1fr 28px auto; gap: 10px; align-items: center; padding: 6px 0; font-size: .88rem; }
.ini-fu .nm { color: #475467; }
.ini-fu .bar { height: 10px; background: #F2F4F7; border-radius: 999px; overflow: hidden; }
.ini-fu .bar i { display: block; height: 100%; background: var(--navy); border-radius: 999px; }
.ini-fu.e1 .bar i { background: #3D6BB3; }
.ini-fu.e2 .bar i { background: var(--gold); }
.ini-fu.e3 .bar i { background: #2F855A; }
.ini-fu b { text-align: right; font-variant-numeric: tabular-nums; }
.ini-fu .ex { color: #067647; font-size: .8rem; font-weight: 600; white-space: nowrap; min-width: 0; }
.ini-fu-rod { margin-top: 8px; padding-top: 8px; border-top: 1px solid #F2F4F7; font-size: .8rem; color: #667085; }
@media (max-width: 900px) { .ini-kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
</style>
"""


def _botao_wa(url, rotulo="WhatsApp"):
    if not url:
        return f'<span class="ini-wa off" title="Cliente sem telefone cadastrado">{rotulo}</span>'
    return f'<a class="ini-wa" href="{url}" target="_blank" rel="noopener">{rotulo}</a>'


def _item(tag_cls, tag, titulo, detalhe, acao):
    """Uma linha de "Para fazer": etiqueta, texto e a ação ao lado (função que desenha o botão)."""
    with st.container(border=True):
        c_txt, c_acao = st.columns([5, 2], vertical_alignment="center")
        with c_txt:
            st.markdown(f'<div class="ini-item"><span class="ini-tag {tag_cls}">{tag}</span>'
                        f'<div class="ini-txt"><b>{titulo}</b><span class="det">{detalhe}</span></div></div>',
                        unsafe_allow_html=True)
        with c_acao:
            acao()


def _funil_html(fn):
    """Etapas do funil com barra proporcional ao número de propostas enviadas."""
    if not fn["enviadas"]:
        return '<span style="color:#667085">Nenhuma proposta nos últimos 90 dias.</span>'
    base = fn["enviadas"]
    etapas = [("Enviadas", fn["enviadas"], ""),
              ("Fechadas", fn["fechadas"], fmt_brl(fn["valor_fechado"])),
              ("Concluídas", fn["concluidas"], "")]
    html = ""
    for i, (nome, n, extra) in enumerate(etapas, 1):
        html += (f'<div class="ini-fu e{i}"><span class="nm">{nome}</span>'
                 f'<span class="bar"><i style="width:{max(n / base * 100, 2 if n else 0):.0f}%"></i></span>'
                 f'<b>{n}</b><span class="ex">{extra}</span></div>')
    html += (f'<div class="ini-fu-rod">{fn["aguardando"]} aguardando resposta ({fmt_brl(fn["valor_aguardando"])})'
             f' · {fn["recusadas"]} recusada(s)</div>')
    return html


def _aniversario(cli, hoje):
    """data_aniversario é guardada como DD/mmm (ex.: 05/out); devolve a próxima ocorrência."""
    txt = str(cli.get("data_aniversario") or "").strip().lower()
    try:
        dia, mes = txt.split("/")[:2]
        m = MES_ABREV.index(mes[:3]) + 1
        d = hoje.replace(month=m, day=int(dia))
    except (ValueError, IndexError):
        return None
    return d if d >= hoje else d.replace(year=hoje.year + 1)


def _onboarding(perfil, clientes, propostas):
    st.markdown('<div class="ini-secao">Primeiros passos</div>', unsafe_allow_html=True)
    passos = [
        ("Coloque sua marca", "Logotipo, cores e contatos saem em todas as propostas em PDF.", "Perfil", "Abrir Perfil e marca",
         bool(perfil.get("logo"))),
        ("Cadastre sua primeira cliente", "Nome e telefone já bastam para enviar mensagens pelo WhatsApp.", "Clientes",
         "Cadastrar cliente", not clientes.empty),
        ("Crie a primeira proposta", "Monte o orçamento e gere o PDF para enviar.", "Propostas", "Criar proposta",
         not propostas.empty),
    ]
    for i, (t, d, pagina, rotulo, feito) in enumerate(passos, 1):
        with st.container(border=True):
            c1, c2 = st.columns([5, 2], vertical_alignment="center")
            marca = '<span class="n ok">✓</span>' if feito else f'<span class="n">{i}</span>'
            c1.markdown(f'<div class="ini-passo">{marca}<div class="ini-txt"><b>{t}</b>'
                        f'<span class="det">{d}</span></div></div>', unsafe_allow_html=True)
            if not feito and c2.button(rotulo, key=f"ini_passo_{i}", use_container_width=True):
                _ir(pagina)


def _perfil():
    try:
        from pages.perfil import carregar_perfil
        return carregar_perfil() or {}
    except Exception:
        return {}


def show():
    from utils.auth_guard import require_auth
    require_auth()
    if 'db' not in st.session_state:
        st.error("Conexão com o banco de dados não inicializada")
        return
    db = st.session_state.db
    hoje = _hoje()
    st.markdown(CSS, unsafe_allow_html=True)

    nome = _primeiro_nome()
    st.markdown(f'<h1 class="ini-titulo">{"Olá, " + nome if nome else "Início"}</h1>'
                f'<div class="ini-data">{SEMANA[hoje.weekday()].capitalize()}, {hoje.day} de {MESES[hoje.month - 1]}</div>',
                unsafe_allow_html=True)

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
        _onboarding(perfil, clientes, propostas)
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
        rec_pend = desp_pend = pd.DataFrame(columns=["valor", "d", "descricao"])

    atras_rec = rec_pend[rec_pend["d"].apply(lambda d: bool(d) and d < hoje)] if not rec_pend.empty else rec_pend
    prox7_pag = desp_pend[desp_pend["d"].apply(lambda d: bool(d) and d <= hoje + timedelta(days=7))] if not desp_pend.empty else desp_pend

    # ---------- números do mês ----------
    from utils.indicadores import movimentos, entrou_gastou, funil
    entrou, gastou = entrou_gastou(movimentos(fin), hoje.year, hoje.month)
    lucro = entrou - gastou
    fn = funil(propostas, hoje)
    conv = fn["conversao"]
    st.markdown('<div class="ini-kpis">' +
        _kpi(f"Lucro de {MESES[hoje.month - 1]}", fmt_brl(lucro),
             f"entrou {fmt_brl(entrou)} · gastou {fmt_brl(gastou)}", destaque=True) +
        _kpi("A receber", fmt_brl(rec_pend["valor"].sum()),
             f'<span class="ini-atraso">{len(atras_rec)} em atraso</span>' if len(atras_rec) else f"{len(rec_pend)} lançamento(s) pendente(s)", tom="rec") +
        _kpi("A pagar", fmt_brl(desp_pend["valor"].sum()),
             f"{len(prox7_pag)} vence(m) em até 7 dias" if len(prox7_pag) else f"{len(desp_pend)} conta(s) em aberto", tom="pag") +
        _kpi("Conversão", f"{conv:.0%}" if conv is not None else "—",
             f"fechou {fn['fechadas']} de {fn['fechadas'] + fn['recusadas']} respondidas · {fn['dias']} dias"
             if conv is not None else "nenhuma proposta respondida em 90 dias", tom="conv") +
        '</div>', unsafe_allow_html=True)

    if not perfil.get("logo") and not st.session_state.get("ini_sem_logo_ok"):
        with st.container(border=True):
            c1, c2, c3 = st.columns([6, 2, 1], vertical_alignment="center")
            c1.markdown('<div class="ini-txt"><b>Suas propostas ainda saem sem o seu logotipo</b>'
                        '<span class="det">Envie o logo e escolha as cores em Perfil e marca.</span></div>',
                        unsafe_allow_html=True)
            if c2.button("Colocar minha marca", key="ini_ir_marca", use_container_width=True):
                _ir("Perfil")
            if c3.button("", icon=":material/close:", key="ini_sem_logo_fechar", type="tertiary", help="Agora não"):
                st.session_state["ini_sem_logo_ok"] = True
                st.rerun()

    col_fazer, col_lado = st.columns([3, 2], gap="large")

    # ---------- para fazer ----------
    with col_fazer:
        st.markdown('<div class="ini-secao">Para fazer</div>', unsafe_allow_html=True)
        n_itens = 0

        # 1) pós-organização com prazo vencido ou no dia
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
                    st.markdown(_botao_wa(url), unsafe_allow_html=True)
                    if st.button("Feito", key=f"ini_feito_{aid}", use_container_width=True):
                        db.update_post_organization_action(action_id=aid, status='FEITO')
                        st.rerun()
                    if st.button("Adiar 3 dias", key=f"ini_adiar_{aid}", type="tertiary", use_container_width=True):
                        db.update_post_organization_action(action_id=aid, status='PENDENTE', due_date=venc + timedelta(days=3))
                        st.rerun()
                _item("pos", f"Pós {dmais}".strip(), f"{nome_etapa} · {cliente}",
                      f"{objetivo} · proposta #{a.get('proposta_numero', '')} · "
                      + (f'<span class="ini-atraso">venceu {_quando(venc, hoje)}</span>' if venc < hoje else _quando(venc, hoje)),
                      _acao)
                n_itens += 1

        # 2) recebimentos em atraso ou nos próximos 3 dias
        if not rec_pend.empty:
            for _, r in rec_pend[rec_pend["d"].apply(lambda d: bool(d) and d <= hoje + timedelta(days=3))].sort_values("d").iterrows():
                atrasado = r["d"] < hoje
                _item("rec", "Receber", f"{fmt_brl(r['valor'])} · {r.get('descricao') or 'Recebimento'}",
                      (f'<span class="ini-atraso">venceu {_quando(r["d"], hoje)}</span>' if atrasado else f"vence {_quando(r['d'], hoje)}")
                      + f" ({_dm(r['d'])})",
                      lambda k=r['id']: st.button("Abrir", key=f"ini_rec_{k}", use_container_width=True,
                                                   on_click=st.session_state.__setitem__, args=("current_page", "Financeiro")))
                n_itens += 1

        # 3) contas a pagar em atraso ou nos próximos 3 dias
        if not desp_pend.empty:
            for _, r in desp_pend[desp_pend["d"].apply(lambda d: bool(d) and d <= hoje + timedelta(days=3))].sort_values("d").iterrows():
                atrasado = r["d"] < hoje
                _item("pag", "Pagar", f"{fmt_brl(r['valor'])} · {r.get('descricao') or 'Conta'}",
                      (f'<span class="ini-atraso">venceu {_quando(r["d"], hoje)}</span>' if atrasado else f"vence {_quando(r['d'], hoje)}")
                      + f" ({_dm(r['d'])})",
                      lambda k=r['id']: st.button("Abrir", key=f"ini_pag_{k}", use_container_width=True,
                                                   on_click=st.session_state.__setitem__, args=("current_page", "Financeiro")))
                n_itens += 1

        # 4) propostas enviadas sem resposta: hora do follow-up
        if not propostas.empty:
            abertas = propostas[propostas["st"] == "em_aberto"]
            for _, p in abertas.iterrows():
                enviada = _data(p.get("data_proposta")) or _data(p.get("data_inicio"))
                if not enviada or (hoje - enviada).days < DIAS_FOLLOWUP:
                    continue
                cliente = p.get("cliente_nome") or "cliente"
                msg = (f"Oi, {str(cliente).split(' ')[0]}! Tudo bem? Passando para saber se ficou alguma dúvida "
                       f"sobre a proposta de organização que te enviei. Fico à disposição!")
                url = whatsapp_link(tel.get(p.get("cliente_id")), msg)
                _item("prop", "Follow-up", f"Proposta #{p.get('numero')} · {cliente}",
                      f"{fmt_brl(p['valor'])} · enviada {_quando(enviada, hoje)}, ainda sem resposta",
                      lambda url=url: st.markdown(_botao_wa(url), unsafe_allow_html=True))
                n_itens += 1

        # 5) aniversariantes de hoje até 7 dias
        if not clientes.empty and "data_aniversario" in clientes.columns:
            for _, c in clientes.iterrows():
                d = _aniversario(c, hoje)
                if not d or (d - hoje).days > 7:
                    continue
                primeiro = str(c["nome"]).split(" ")[0]
                url = whatsapp_link(c.get("telefone"), f"Feliz aniversário, {primeiro}! Desejo um novo ciclo leve e cheio de alegria. 💛")
                _item("niver", "Aniversário", str(c["nome"]), f"{_quando(d, hoje)} ({_dm(d)})",
                      lambda url=url: st.markdown(_botao_wa(url, "Dar parabéns"), unsafe_allow_html=True))
                n_itens += 1

        if not n_itens:
            st.markdown('<div class="ini-ok">Tudo em dia: nenhuma ação pendente para hoje.</div>', unsafe_allow_html=True)

    # ---------- propostas em andamento e aniversariantes ----------
    with col_lado:
        st.markdown(f'<div class="ini-secao">Funil de propostas · {fn["dias"]} dias</div>', unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(_funil_html(fn), unsafe_allow_html=True)

        st.markdown('<div class="ini-secao" style="margin-top:18px">Propostas em andamento</div>', unsafe_allow_html=True)
        with st.container(border=True):
            if ativas.empty:
                st.markdown('<span style="color:#667085">Nenhuma proposta em andamento.</span>', unsafe_allow_html=True)
            else:
                from utils.proposta_status import label_for
                linhas = ""
                for _, p in ativas.sort_values("valor", ascending=False).head(8).iterrows():
                    linhas += (f'<div class="ini-lin"><span>#{p.get("numero")} · {p.get("cliente_nome") or "—"}'
                               f'<span class="ini-st {p["st"]}">{label_for(p["st"])}</span></span><b>{fmt_brl(p["valor"])}</b></div>')
                st.markdown(linhas, unsafe_allow_html=True)
            if st.button("Abrir propostas", key="ini_ir_propostas", icon=":material/arrow_forward:", use_container_width=True):
                _ir("Propostas")

        st.markdown(f'<div class="ini-secao" style="margin-top:18px">Aniversariantes de {MESES[hoje.month - 1]}</div>',
                    unsafe_allow_html=True)
        with st.container(border=True):
            niver = []
            if not clientes.empty and "data_aniversario" in clientes.columns:
                for _, c in clientes.iterrows():
                    d = _aniversario(c, hoje)
                    if d and d.month == hoje.month:
                        niver.append((d.day, c["nome"]))
            if niver:
                st.markdown("".join(f'<div class="ini-lin"><span>{n}</span><b>{dia:02d}/{hoje.month:02d}</b></div>'
                                    for dia, n in sorted(niver)), unsafe_allow_html=True)
            else:
                st.markdown(f'<span style="color:#667085">Nenhuma cliente faz aniversário em {MESES[hoje.month - 1]}.</span>',
                            unsafe_allow_html=True)
