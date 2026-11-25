"""
Onboarding do site antes da conta: "Seu primeiro orçamento em 3 minutos".

A visitante monta tudo sem cadastro (nome e negócio, sua hora, primeiro orçamento, cliente, marca e
WhatsApp) e só cria a conta no fim, para baixar o PDF e guardar. Nada vai para o banco antes disso,
a não ser o rascunho (tabela onboarding_rascunhos), salvo ao chegar na tela da conta: o login com o
Google sai do site e volta numa sessão nova, então o rascunho segue pelo código ?onb= (e pelo
"state" do Google). Depois do login, concluir() grava os números da Precificação, o perfil (nome,
negócio, WhatsApp, cor), a cliente e a proposta "Em aberto", e a tela final oferece o PDF.

Entradas: "Comece grátis" da landing (?cadastro=1), "Criar conta grátis" no login e ?comecar=1.
Quem já tem conta entra pelo link "Já tenho conta" e não passa por aqui.
"""
import json
import math
import secrets
import urllib.parse
from datetime import date, datetime

import streamlit as st
from sqlalchemy import text

from utils import precificacao as pr

CHAVE = "_ob"
PASSOS = ["inicio", "voce", "hora", "orcamento", "cliente", "marca", "conta"]   # 1-6 numerados; "inicio" sem número
CORES = {"Verde": "#2F7D57", "Ameixa": "#5B4B8A", "Azul-marinho": "#0D1B2A", "Rosa": "#B5546A",
         "Dourado": "#B8943D", "Azul": "#3D6BB3"}
AMB_ORGANIZACAO = ["Cozinha", "Closet / guarda-roupa", "Quarto de casal", "Quarto infantil", "Banheiro",
                   "Área de serviço", "Despensa", "Home office", "Sala / estante"]
COMODOS_MUDANCA = ["Cozinha", "Sala", "Quarto de casal", "Quarto infantil", "Banheiro", "Área de serviço",
                   "Escritório"]
TIPOS = {"organizacao": "Organização", "pre": "Pré-mudança", "pos": "Pós-mudança"}
CLIENTE_EXEMPLO = "Cliente de exemplo"

CARTAO = """<style>.main .block-container, [data-testid="stMainBlockContainer"] { max-width: 520px !important; }</style>"""
CSS = """<style>
.ob-topo { display:flex; justify-content:space-between; align-items:center; margin-bottom:4px; }
.ob-logo { font-family:'Cormorant Garamond',Georgia,serif; font-size:1.25rem; font-weight:600; color:#0D1B2A; }
.ob-logo b { color:#9C7A22; font-weight:600; }
.ob-n { font-size:.78rem; color:#6B7C94; }
.ob-barra { height:5px; background:#ECE7DC; border-radius:3px; margin:6px 0 14px; }
.ob-barra i { display:block; height:100%; background:#C9A84C; border-radius:3px; }
.ob-ey { font-size:.72rem; letter-spacing:.14em; font-weight:700; color:#9C7A22; text-transform:uppercase; }
.ob-t { font-family:'Cormorant Garamond',Georgia,serif; font-size:1.9rem; line-height:1.1; color:#0D1B2A;
        font-weight:600; margin:4px 0 6px; }
.ob-t em { color:#9C7A22; }
.ob-p { color:#5F6B7A; font-size:.93rem; margin:0 0 6px; }
.ob-dica { background:#FFFCF3; border:1px solid #EADFBF; border-radius:10px; padding:9px 12px; font-size:.86rem;
           color:#6B5208; margin:4px 0; }
.ob-res { background:#0D1B2A; border-radius:16px; padding:16px 18px; color:#fff; margin:8px 0 4px; }
.ob-res .l { font-size:.8rem; color:#C7CED8; }
.ob-res .v { font-family:'Cormorant Garamond',Georgia,serif; font-size:2.6rem; color:#C9A84C; font-weight:600;
             line-height:1.05; }
.ob-res .ln { display:flex; justify-content:space-between; font-size:.85rem; border-top:1px solid rgba(255,255,255,.12);
              padding:6px 0 0; margin-top:6px; color:#E7EBF0; }
.ob-res .ln b { color:#C9A84C; }
.ob-lista { margin:8px 0; } .ob-lista div { padding:7px 0; border-bottom:1px solid #EEE9DF; font-size:.93rem; }
.ob-lista b { color:#2F6B4F; margin-right:6px; }
.ob-pdf { border:1px solid #E6E1D6; border-radius:12px; overflow:hidden; margin:8px 0; font-size:.86rem; }
.ob-pdf .c { color:#fff; padding:10px 14px; font-family:'Cormorant Garamond',Georgia,serif; font-size:1.15rem; }
.ob-pdf .b { padding:10px 14px; color:#5F6B7A; }
.ob-pdf .tot { display:flex; justify-content:space-between; border-radius:8px; padding:8px 10px; margin-top:8px;
               font-weight:700; }
.stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"],
.stButton > button[kind="primary"] *, .stButton > button[data-testid="stBaseButton-primary"] * {
  background:#0D1B2A !important; color:#FFFFFF !important; border:none !important; font-weight:600 !important; }
.st-key-ob_comecar .stButton > button, .st-key-ob_comecar .stButton > button * { background:#C9A84C !important;
  color:#0D1B2A !important; }
.stButton > button[kind="primary"] { min-height:46px !important; border-radius:12px !important; }
.ob-pequeno { text-align:center; font-size:.78rem; color:#6B7C94; margin-top:4px; }
</style>"""


# ---------------------------------------------------------------- estado

def _novo():
    return {"passo": "inicio", "nome": "", "empresa": "", "renda": pr.PADROES["renda_desejada"],
            "dias": int(pr.PADROES["dias_mes"]), "horas": float(pr.PADROES["horas_dia"]), "formal": "mei",
            "tipo": "organizacao", "amb": {}, "assist": 0, "cliente": "", "tel_cliente": "", "valor": None,
            "sinal_pct": 50, "cor": "Verde", "whatsapp": "", "ok_whats": False, "email": ""}


def estado():
    if CHAVE not in st.session_state:
        st.session_state[CHAVE] = _novo()
    return st.session_state[CHAVE]


def abrir(email=""):
    """Abre o onboarding na tela de entrada (sem conta)."""
    st.session_state.login_page = "onboarding"
    o = estado()
    if email:
        o["email"] = email


def _ir(passo):
    estado()["passo"] = passo
    st.rerun()


# ---------------------------------------------------------------- contas

def parametros(o):
    """Números da Precificação a partir das respostas (os custos fixos ficam nos padrões)."""
    p = dict(pr.PADROES)
    p["renda_desejada"] = float(o["renda"] or 0)
    p["dias_mes"] = int(o["dias"] or 1)
    p["horas_dia"] = float(o["horas"] or 1)
    p["imposto_pct"] = 0.0 if o["formal"] in ("mei", "nao") else 6.0
    p["custo_impostos_fixos"] = pr.PADROES["custo_impostos_fixos"] if o["formal"] == "mei" else 0.0
    return p


def horas_do_orcamento(o):
    if o["tipo"] == "organizacao":
        return sum(pr.AMBIENTES_PADRAO.get(a, 3.0) * q for a, q in o["amb"].items() if q)
    return sum(pr.AMBIENTES_PADRAO["Mudança (por cômodo)"] * q for q in o["amb"].values() if q)


def orcamento(o):
    p = parametros(o)
    h = horas_do_orcamento(o)
    if h <= 0:
        return None
    r = pr.preco_projeto(p, h, 1.0, o["assist"])
    r["sugerido"] = math.ceil(r["preco_sugerido"] / 10) * 10
    return r


def descricao(o):
    itens = ", ".join(f"{a} ({q})" if q > 1 else a for a, q in o["amb"].items() if q)
    r = orcamento(o) or {}
    dias = r.get("dias_no_local") or 0
    n = int(o["assist"] or 0)
    equipe = f"com {n} assistente{'s' if n > 1 else ''}" if n else "atendimento individual"
    base = TIPOS[o["tipo"]] + (" de " + itens if o["tipo"] == "organizacao" and itens else
                               (": " + itens if itens else ""))
    return f"{base}. Prazo estimado: {max(1, math.ceil(dias))} dia(s), {equipe}."


def _brl(v):
    return ("R$ " + f"{float(v or 0):,.2f}").replace(",", "X").replace(".", ",").replace("X", ".").replace(",00", "")


def _valor(o):
    r = orcamento(o)
    return float(o["valor"]) if o.get("valor") else float((r or {}).get("sugerido") or 0)


# ---------------------------------------------------------------- rascunho no banco

def _engine():
    from utils.database import engine
    return engine


def _tabela(c):
    c.execute(text("CREATE TABLE IF NOT EXISTS onboarding_rascunhos (token TEXT PRIMARY KEY, dados TEXT NOT NULL, "
                   "criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP, usado_em TIMESTAMP, usuario_id TEXT)"))


def salvar_rascunho(o):
    tok = o.get("token") or secrets.token_urlsafe(16)
    o["token"] = tok
    dados = json.dumps({k: v for k, v in o.items() if k != "token"}, ensure_ascii=False)
    try:
        with _engine().begin() as c:
            _tabela(c)
            c.execute(text("INSERT INTO onboarding_rascunhos (token, dados) VALUES (:t, :d) "
                           "ON CONFLICT (token) DO UPDATE SET dados = :d"), {"t": tok, "d": dados})
    except Exception as e:
        print(f"[onboarding] rascunho: {e}", flush=True)
    st.session_state["_ob_token"] = tok
    return tok


def carregar_rascunho(tok):
    try:
        with _engine().begin() as c:
            _tabela(c)
            r = c.execute(text("SELECT dados FROM onboarding_rascunhos WHERE token = :t AND usado_em IS NULL"),
                          {"t": tok}).first()
        return json.loads(r[0]) if r else None
    except Exception as e:
        print(f"[onboarding] carregar: {e}", flush=True)
        return None


def _marcar_usado(tok, uid):
    try:
        with _engine().begin() as c:
            c.execute(text("UPDATE onboarding_rascunhos SET usado_em = :a, usuario_id = :u WHERE token = :t"),
                      {"a": datetime.now(), "u": uid, "t": tok})
    except Exception as e:
        print(f"[onboarding] marcar usado: {e}", flush=True)


def token_pendente():
    """Código do rascunho que espera a conta: da sessão, do Google (state) ou do endereço."""
    try:
        url = st.query_params.get("onb") or ""
    except Exception:
        url = ""
    return st.session_state.get("_ob_token") or st.session_state.get("_ob_token_google") or url


# ---------------------------------------------------------------- telas antes da conta

def _topo(n=None):
    st.markdown(CARTAO + CSS, unsafe_allow_html=True)
    num = f'<span class="ob-n">{n} de 6</span>' if n else ""
    barra = f'<div class="ob-barra"><i style="width:{n / 6 * 100:.0f}%"></i></div>' if n else ""
    st.markdown(f'<div class="ob-topo"><span class="ob-logo">Planner <b>Organiza</b></span>{num}</div>{barra}',
                unsafe_allow_html=True)


def _voltar(anterior, chave):
    if st.button("← Voltar", key=chave, type="tertiary"):
        _ir(anterior)


def _tela_inicio(o):
    _topo()
    st.markdown('<div class="ob-ey" style="margin-top:14px">Para personal organizer</div>'
                '<div class="ob-t" style="font-size:2.2rem">Monte seu primeiro orçamento <em>em 3 minutos</em></div>'
                '<p class="ob-p">Descubra quanto vale a sua hora, calcule o preço do projeto e veja a proposta com a '
                'sua marca. Sem cadastro para começar.</p>'
                '<div class="ob-lista"><div><b>✓</b>Sua hora e diária ideais</div>'
                '<div><b>✓</b>Preço sugerido por ambiente ou por mudança</div>'
                '<div><b>✓</b>Proposta em PDF com a sua marca</div></div>', unsafe_allow_html=True)
    if st.button("Começar agora →", key="ob_comecar", type="primary", use_container_width=True):
        _evento("onboarding_inicio")
        _ir("voce")
    st.markdown('<div class="ob-pequeno">Grátis · 7 dias com tudo liberado · sem cartão</div>', unsafe_allow_html=True)
    if st.button("Já tenho conta · Entrar", key="ob_ja_tenho", use_container_width=True):
        st.session_state.login_page = "login"
        st.rerun()


def _tela_voce(o):
    _topo(1)
    st.markdown('<div class="ob-ey">Prazer!</div><div class="ob-t">Como quer ser <em>chamada?</em></div>',
                unsafe_allow_html=True)
    o["nome"] = st.text_input("Seu nome", value=o["nome"], placeholder="Ana", key="ob_nome")
    o["empresa"] = st.text_input("Nome do seu negócio", value=o["empresa"], placeholder="Ana Ribeiro Organização",
                                 key="ob_empresa")
    st.markdown('<div class="ob-dica">💡 O nome do negócio já sai no topo da sua proposta.</div>',
                unsafe_allow_html=True)
    if st.button("Continuar", key="ob_voce_ok", type="primary", use_container_width=True):
        if not (o["nome"] or "").strip():
            st.error("Conta pra gente como quer ser chamada.")
        else:
            _ir("hora")
    _voltar("inicio", "ob_voce_v")


def _tela_hora(o):
    _topo(2)
    st.markdown('<div class="ob-ey">Quanto vale o seu trabalho</div>'
                '<div class="ob-t">Quanto você quer <em>ganhar por mês?</em></div>', unsafe_allow_html=True)
    o["renda"] = st.number_input("Por mês, livre para você (R$)", 500.0, 100000.0, float(o["renda"]), 500.0,
                                 key="ob_renda", format="%.0f")
    c1, c2 = st.columns(2)
    o["dias"] = c1.number_input("Dias de atendimento no mês", 1, 31, int(o["dias"]), key="ob_dias")
    o["horas"] = c2.number_input("Horas por dia", 1.0, 14.0, float(o["horas"]), 0.5, key="ob_horas")
    formais = {"mei": "MEI", "simples": "Simples Nacional", "nao": "Ainda não sou formalizada"}
    o["formal"] = st.radio("Como o seu negócio é formalizado?", list(formais), format_func=formais.get,
                           index=list(formais).index(o["formal"]), horizontal=True, key="ob_formal")
    p = parametros(o)
    st.markdown(f'<div class="ob-res"><div class="l">Sua hora vale</div><div class="v">{_brl(round(pr.hora_sugerida(p)))}</div>'
                f'<div class="ln"><span>Diária ({p["horas_dia"]:g} h)</span><b>{_brl(round(pr.hora_sugerida(p) * p["horas_dia"]))}</b></div>'
                f'<div class="ln"><span>Abaixo de {_brl(round(pr.hora_minima(p)))} por hora a conta do mês não fecha</span></div></div>'
                '<p class="ob-p" style="font-size:.8rem">Já contamos transporte, ferramentas e impostos com valores '
                'comuns. Depois você ajusta tudo em Precificação.</p>', unsafe_allow_html=True)
    if st.button("Continuar", key="ob_hora_ok", type="primary", use_container_width=True):
        _ir("orcamento")
    _voltar("voce", "ob_hora_v")


def _tela_orcamento(o):
    _topo(3)
    st.markdown('<div class="ob-ey">Vamos precificar</div><div class="ob-t">Qual serviço você quer <em>orçar?</em></div>',
                unsafe_allow_html=True)
    tipo = st.radio("Serviço", list(TIPOS), format_func=TIPOS.get, index=list(TIPOS).index(o["tipo"]),
                    horizontal=True, key="ob_tipo", label_visibility="collapsed")
    if tipo != o["tipo"]:
        o["tipo"], o["amb"], o["valor"] = tipo, {}, None
    lista = AMB_ORGANIZACAO if o["tipo"] == "organizacao" else COMODOS_MUDANCA
    st.markdown('<p class="ob-p" style="margin-top:6px">' + ("Quais ambientes? Marque a quantidade."
                if o["tipo"] == "organizacao" else "Quais cômodos entram na mudança?") + "</p>",
                unsafe_allow_html=True)
    cols = st.columns(2)
    for i, a in enumerate(lista):
        rot = a.replace("Closet / guarda-roupa", "Closet").replace("Sala / estante", "Sala")
        o["amb"][a] = cols[i % 2].number_input(rot, 0, 9, int(o["amb"].get(a, 0)), key=f"ob_amb_{o['tipo']}_{i}")
    o["assist"] = int(st.number_input("Quantas assistentes vão com você? (0 se for sozinha)", 0, 10, int(o["assist"]),
                                      key="ob_assist"))
    r = orcamento(o)
    if r:
        o["valor"] = None
        st.markdown(f'<div class="ob-res"><div class="l">Preço sugerido</div><div class="v">{_brl(r["sugerido"])}</div>'
                    f'<div class="ln"><span>{max(1, math.ceil(r["dias_no_local"]))} dia(s) · {r["pessoas"]} pessoa(s)'
                    f'</span><span>fica para você <b>{_brl(r["lucro"])}</b></span></div>'
                    f'<div class="ln"><span>Preço mínimo</span><span>{_brl(r["preco_minimo"])}</span></div></div>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<div class="ob-dica">Marque pelo menos um ambiente para ver o preço.</div>', unsafe_allow_html=True)
    if st.button("Continuar", key="ob_orc_ok", type="primary", use_container_width=True, disabled=not r):
        _ir("cliente")
    _voltar("hora", "ob_orc_v")


def _tela_cliente(o):
    _topo(4)
    st.markdown('<div class="ob-ey">Quase lá</div><div class="ob-t">Para quem é <em>essa proposta?</em></div>',
                unsafe_allow_html=True)
    o["cliente"] = st.text_input("Nome da cliente", value="" if o["cliente"] == CLIENTE_EXEMPLO else o["cliente"],
                                 placeholder="Juliana Ferraz", key="ob_cli")
    o["tel_cliente"] = st.text_input("Telefone da cliente (opcional)", value=o["tel_cliente"],
                                     placeholder="(11) 99999-9999", key="ob_cli_tel")
    r = orcamento(o) or {}
    c1, c2 = st.columns(2)
    valor = c1.number_input("Valor da proposta (R$)", 0.0, 500000.0, float(_valor(o)), 10.0, key="ob_valor",
                            format="%.0f", help=f"Sugerido: {_brl(r.get('sugerido'))}")
    o["valor"] = valor if abs(valor - float(r.get("sugerido") or 0)) > 0.5 else None
    o["sinal_pct"] = c2.number_input("Sinal na aprovação (%)", 0, 100, int(o["sinal_pct"]), 10, key="ob_sinal")
    if st.button("Ver minha proposta", key="ob_cli_ok", type="primary", use_container_width=True):
        if not (o["cliente"] or "").strip():
            o["cliente"] = CLIENTE_EXEMPLO
        _ir("marca")
    if st.button("Ainda não tenho cliente · usar um exemplo", key="ob_cli_ex", use_container_width=True):
        o["cliente"] = CLIENTE_EXEMPLO
        _ir("marca")
    _voltar("orcamento", "ob_cli_v")


def _previa(o):
    cor = CORES.get(o["cor"], "#2F7D57")
    empresa = (o["empresa"] or o["nome"] or "Seu negócio").strip()
    zap = f'<div style="margin-top:6px">📱 {o["whatsapp"]}</div>' if o["whatsapp"] else ""
    sinal = _valor(o) * o["sinal_pct"] / 100
    st.markdown(f'<div class="ob-pdf"><div class="c" style="background:{cor}">{empresa}</div><div class="b">'
                f'Proposta de Serviço para <b style="color:#0D1B2A">{o["cliente"]}</b><br>{descricao(o)}'
                f'<div class="tot" style="background:{cor}14;color:{cor}"><span>Investimento</span>'
                f'<span>{_brl(_valor(o))}</span></div><div style="margin-top:6px">Sinal de {o["sinal_pct"]}% '
                f'({_brl(sinal)}) na aprovação</div>{zap}</div></div>', unsafe_allow_html=True)


def _tela_marca(o):
    _topo(5)
    st.markdown('<div class="ob-ey">Com a sua cara</div><div class="ob-t">Escolha a <em>sua cor</em></div>',
                unsafe_allow_html=True)
    # as opções do rádio viram bolinhas na cor (o nome fica só para leitores de tela)
    bolas = "".join(
        f'.st-key-ob_cor [role="radiogroup"] > div:nth-child({i}) label > div > div:first-child {{ background:{c} !important; }}'
        for i, c in enumerate(CORES.values(), 1))
    st.markdown('<style>.st-key-ob_cor [role="radiogroup"] { gap:12px !important; flex-wrap:wrap; margin:6px 0 4px; }'
                '.st-key-ob_cor [role="radiogroup"] label > div > div:first-child { width:36px !important; '
                'height:36px !important; border:none !important; border-radius:50% !important; margin:0 !important; '
                'cursor:pointer; box-shadow:0 0 0 1px rgba(13,27,42,.12); }'
                '.st-key-ob_cor [role="radiogroup"] label > div > div:first-child > div { display:none !important; }'
                '.st-key-ob_cor [role="radiogroup"] > div[data-selected="true"] label > div > div:first-child '
                '{ box-shadow:0 0 0 3px #FFFFFF, 0 0 0 5px #C9A84C !important; }'
                '.st-key-ob_cor [data-testid="stMarkdownContainer"] { position:absolute; width:1px; height:1px; '
                'overflow:hidden; clip:rect(0 0 0 0); }' + bolas + '</style>', unsafe_allow_html=True)
    o["cor"] = st.radio("Cor da proposta", list(CORES), index=list(CORES).index(o["cor"]), horizontal=True,
                        key="ob_cor", label_visibility="collapsed")
    o["whatsapp"] = st.text_input("Seu WhatsApp · sai na proposta para a cliente responder", value=o["whatsapp"],
                                  placeholder="(11) 98765-4321", key="ob_zap")
    _previa(o)
    o["ok_whats"] = st.checkbox("Quero receber dicas e ajuda do Planner pelo WhatsApp (pode sair quando quiser)",
                                value=o["ok_whats"], key="ob_ok_zap")
    if st.button("Gostei, quero baixar", key="ob_marca_ok", type="primary", use_container_width=True):
        salvar_rascunho(o)
        st.query_params["onb"] = o["token"]
        _evento("onboarding_proposta_pronta")
        _ir("conta")
    _voltar("cliente", "ob_marca_v")


def _tela_conta(o):
    _topo(6)
    st.markdown('<div class="ob-ey">Sua proposta está pronta 🎉</div>'
                '<div class="ob-t">Crie sua conta grátis para <em>baixar e guardar</em></div>'
                '<p class="ob-p">Guardamos sua hora, a cliente, a proposta e a sua marca. Você usa no computador e no '
                'celular.</p>', unsafe_allow_html=True)
    if not o.get("token"):
        salvar_rascunho(o)
    try:
        from utils.google_auth_component import google_login_button
        google_login_button(rascunho=o["token"])
    except Exception as e:
        print(f"[onboarding] google: {e}", flush=True)
    st.markdown('<div class="ob-pequeno" style="margin:6px 0">ou com e-mail</div>', unsafe_allow_html=True)
    with st.form("ob_conta"):
        email = st.text_input("E-mail", value=o.get("email") or "")
        senha = st.text_input("Senha (mínimo 6 caracteres)", type="password")
        aceito = st.checkbox("Li e aceito os Termos de Uso e a Política de Privacidade")
        st.markdown('<div class="ob-pequeno"><a href="?show_termos=true" target="_blank">Termos de Uso</a> · '
                    '<a href="?show_politica=true" target="_blank">Política de Privacidade</a></div>',
                    unsafe_allow_html=True)
        enviar = st.form_submit_button("Criar conta e baixar o PDF", type="primary", use_container_width=True)
    if enviar:
        if not email or "@" not in email or len(senha or "") < 6:
            st.error("Confira o e-mail e use uma senha com pelo menos 6 caracteres.")
        elif not aceito:
            st.error("Para criar a conta, marque que leu e aceita os termos.")
        else:
            from utils.firebase_auth import firebase_auth
            with st.spinner("Criando sua conta..."):
                r = firebase_auth.register(email.strip(), senha, (o["nome"] or "").strip() or email.split("@")[0])
            if r.get("success"):
                st.session_state["_ob_token"] = o["token"]
                st.session_state.show_welcome = True
                st.rerun()
            else:
                st.error(f"Não foi possível criar a conta: {r.get('error')}")
    st.markdown('<div class="ob-pequeno">7 dias grátis com tudo liberado · sem cartão</div>', unsafe_allow_html=True)
    _voltar("marca", "ob_conta_v")


def _evento(nome):
    try:
        from utils.rastreamento import evento
        evento(nome, nome, meta_custom=True)
    except Exception:
        pass


def mostrar():
    """Tela do onboarding antes da conta (chamar no bloco sem login, com st.stop() depois)."""
    o = estado()
    telas = {"inicio": _tela_inicio, "voce": _tela_voce, "hora": _tela_hora, "orcamento": _tela_orcamento,
             "cliente": _tela_cliente, "marca": _tela_marca, "conta": _tela_conta}
    telas.get(o["passo"], _tela_inicio)(o)


# ---------------------------------------------------------------- depois da conta

def concluir(db):
    """Grava o rascunho na conta recém-criada. Devolve o resumo (ou None se não havia rascunho)."""
    tok = token_pendente()
    if not tok:
        return None
    o = st.session_state.get(CHAVE) if st.session_state.get(CHAVE, {}).get("token") == tok else None
    o = o or carregar_rascunho(tok)
    for k in ("_ob_token", "_ob_token_google"):
        st.session_state.pop(k, None)
    try:
        if "onb" in st.query_params:
            del st.query_params["onb"]
    except Exception:
        pass
    if not o:
        return None
    uid = getattr(db, "usuario_id", None)
    _marcar_usado(tok, uid)
    try:
        if not db.get_propostas().empty:   # conta antiga: não mistura o rascunho com os dados dela
            return None
    except Exception:
        pass
    resumo = {"nome": (o.get("nome") or "").strip(), "cliente": o.get("cliente"), "valor": _valor(o)}
    try:
        db.salvar_precificacao({k: v for k, v in parametros(o).items() if k in pr.PADROES})
        resumo["hora"] = pr.hora_sugerida(parametros(o))
    except Exception as e:
        print(f"[onboarding] precificação: {e}", flush=True)
    try:
        perfil = {"nome": resumo["nome"], "empresa": (o.get("empresa") or "").strip(),
                  "cor_principal": CORES.get(o.get("cor"), "#2F7D57")}
        if (o.get("whatsapp") or "").strip():
            perfil["telefone"] = o["whatsapp"].strip()
        db.salvar_perfil_usuario({k: v for k, v in perfil.items() if v})
        if o.get("formal") == "mei":
            db.salvar_regime("MEI")
        elif o.get("formal") == "simples":
            db.salvar_regime("Simples Nacional")
    except Exception as e:
        print(f"[onboarding] perfil: {e}", flush=True)
    try:
        from utils.proposta_status import STATUS_EM_ABERTO
        cli = db.add_cliente(nome=(o.get("cliente") or CLIENTE_EXEMPLO).strip(),
                             telefone=(o.get("tel_cliente") or "").strip() or None, origem_cliente=None)
        r = orcamento(o) or {}
        pid = db.add_proposta(cliente_id=cli, descricao=descricao(o), valor=_valor(o), status=STATUS_EM_ABERTO,
                              tipo_proposta=TIPOS.get(o.get("tipo"), "Organização"),
                              previsao_dias=max(1, math.ceil(r.get("dias_no_local") or 1)),
                              gerar_transacoes_automaticas=False)
        sinal = round(_valor(o) * int(o.get("sinal_pct") or 0) / 100, 2)
        if pid:   # data de hoje (o padrão do modelo é a data em que o servidor subiu)
            db.update_proposta(pid, data_proposta=date.today(), **({"sinal": sinal} if sinal > 0 else {}))
        resumo["proposta_id"] = pid
    except Exception as e:
        print(f"[onboarding] proposta: {e}", flush=True)
    try:
        from utils import onboarding_web
        onboarding_web._salvar({"formal": o.get("formal"), "origem": "web_onboarding_v2",
                                "respondido": date.today().isoformat(), "passos": "ativo",
                                "whatsapp_ok": bool(o.get("ok_whats"))})
        db.marcar_tutorial_visto()
    except Exception as e:
        print(f"[onboarding] marcar: {e}", flush=True)
    resumo.update({"tel_cliente": o.get("tel_cliente"), "cor": o.get("cor"), "whatsapp": o.get("whatsapp")})
    st.session_state["_ob_resumo"] = resumo
    st.session_state.pop(CHAVE, None)
    _evento("onboarding_concluido")
    return resumo


def mostrar_pronto():
    """Tela final, já com a conta: o que foi salvo, o PDF e o WhatsApp. True se mostrou."""
    r = st.session_state.get("_ob_resumo")
    if not r:
        return False
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(
                f'<div class="ob-ey">Tudo salvo</div><div class="ob-t">Bem-vinda, <em>{r.get("nome") or "organizer"}!</em></div>',
                unsafe_allow_html=True)
    linhas = []
    if r.get("hora"):
        linhas.append(f"Sua hora: {_brl(r['hora'])}, guardada em Precificação")
    linhas.append(f"{r.get('cliente')} em Clientes")
    if r.get("proposta_id"):
        linhas.append(f"Proposta de {_brl(r.get('valor'))} em Propostas, em aberto")
    linhas.append(f"Sua marca {str(r.get('cor') or '').lower()}" + (" e o seu WhatsApp" if r.get("whatsapp") else ""))
    st.markdown('<div class="ob-lista">' + "".join(f"<div><b>✓</b>{x}</div>" for x in linhas) + "</div>",
                unsafe_allow_html=True)
    if r.get("proposta_id"):
        from utils.ui import baixar_pdf
        from utils.propostas_helper import gerar_pdf_cliente_proposta
        import os

        def _gerar():
            try:
                ok, msg, arq = gerar_pdf_cliente_proposta(st.session_state.db, r["proposta_id"], tipo_documento="proposta")
            except Exception as e:
                return None, None, str(e)
            return (arq, os.path.basename(arq), None) if ok and arq else (None, None, msg)
        baixar_pdf("Baixar a proposta em PDF", f"ob_pdf_{r['proposta_id']}", _gerar)
        tel = "".join(ch for ch in (r.get("tel_cliente") or "") if ch.isdigit())
        if tel:
            if not tel.startswith("55"):
                tel = "55" + tel
            msg = urllib.parse.quote(f"Oi, {r.get('cliente')}! Segue a proposta do serviço de organização. "
                                     "Qualquer dúvida, é só me chamar.")
            st.link_button("Enviar mensagem para a cliente no WhatsApp", f"https://wa.me/{tel}?text={msg}",
                           use_container_width=True)
    st.markdown('<p class="ob-p" style="margin-top:10px"><b style="color:#0D1B2A">Próximos passos:</b> coloque o seu '
                'logo em Perfil e marca, marque a visita na Agenda e instale o app para receber os avisos.</p>',
                unsafe_allow_html=True)
    if st.button("Ir para o meu Início", key="ob_fim", type="primary", use_container_width=True):
        st.session_state.pop("_ob_resumo", None)
        st.session_state.current_page = "Dashboard"
        st.rerun()
    return True
