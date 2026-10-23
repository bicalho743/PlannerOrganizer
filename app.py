import os
import sys
import re
import streamlit as st
import logging
import pandas as pd
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from utils.type_conversion_fix import fix_numpy_int64_bug
    fix_numpy_int64_bug()
except Exception as e:
    logger.error(f"Erro: {str(e)}")

project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.database import Database
from utils.planos import verificar_login
from utils.analytics_injector import inject_analytics_tags, track_page_view, inject_seo_meta_tags
from utils.html_head_injector import inject_head_content

try:
    from utils.firebase_auth import firebase_auth
except ImportError:
    firebase_auth = None

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if 'login_page' not in st.session_state:
    st.session_state.login_page = "login"
if "show_termos" not in st.session_state:
    st.session_state.show_termos = False
if "show_politica" not in st.session_state:
    st.session_state.show_politica = False
if "show_enviar_manual" not in st.session_state:
    st.session_state.show_enviar_manual = False
if "show_debug_propostas_finalizadas" not in st.session_state:
    st.session_state.show_debug_propostas_finalizadas = False

st.set_page_config(
    
    page_title="Planner Organiza | Sistema para Personal Organizers",
    page_icon="favicon.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)
from utils.pwa_inject import inject_pwa
inject_pwa()

import streamlit.components.v1 as _components
_components.html("""
<script>
(function(){
  var doc = window.parent.document;
  if (doc.getElementById('mobile-sidebar-fab')) return;

  var style = doc.createElement('style');
  style.textContent =
    '#mobile-sidebar-fab { display:none !important; }' +
    '#mobile-sidebar-overlay { display:none !important; }' +
    '@media screen and (max-width:768px) {' +
    '  #mobile-sidebar-fab.aberto { display:flex !important; }' +
    '  #mobile-sidebar-overlay { display:block !important; }' +
    '}';
  doc.head.appendChild(style);

  var fab = doc.createElement('button');
  fab.id = 'mobile-sidebar-fab';
  fab.setAttribute('aria-label', 'Abrir menu');
  fab.textContent = '\\u2630';
  doc.body.appendChild(fab);

  var overlay = doc.createElement('div');
  overlay.id = 'mobile-sidebar-overlay';
  doc.body.appendChild(overlay);

  function getSidebar() {
    return doc.querySelector('section[data-testid="stSidebar"]');
  }

  // Streamlit antigo marca o menu com aria-expanded; o novo (1.4x+) com data-collapsed.
  function isOpen() {
    var sb = getSidebar();
    return !!sb && (sb.getAttribute('aria-expanded') === 'true' || sb.getAttribute('data-collapsed') === 'false');
  }

  function clickNativeBtn() {
    var sel = isOpen()
      ? '[data-testid="stSidebarCollapseButton"] button,button[data-testid="stBaseButton-headerNoPadding"]'
      : 'button[data-testid="stExpandSidebarButton"],button[data-testid="collapsedControl"],button[data-testid="stBaseButton-headerNoPadding"]';
    var btn = doc.querySelector(sel);
    if (btn) { btn.click(); return true; }
    return false;
  }

  function syncState() {
    var open = isOpen();
    if (open) {
      fab.innerHTML = '\\u2715';
      var sb = getSidebar();
      var sbW = sb ? sb.getBoundingClientRect().width : 280;
      fab.style.left = (sbW - 46) + 'px';
      fab.style.background = 'rgba(13,27,42,0.85)';
      fab.style.borderColor = 'rgba(255,255,255,0.3)';
      fab.style.color = '#ffffff';
      overlay.classList.add('overlay-visible');
      fab.classList.add('aberto');
    } else {
      fab.classList.remove('aberto');
      fab.innerHTML = '\\u2630';
      fab.style.left = '14px';
      fab.style.background = '#0D1B2A';
      fab.style.borderColor = '#C9A84C';
      fab.style.color = '#C9A84C';
      overlay.classList.remove('overlay-visible');
    }
  }

  fab.addEventListener('click', function(e) {
    e.preventDefault();
    e.stopPropagation();
    clickNativeBtn();
    setTimeout(syncState, 100);
  });

  // celular: escolher uma tela no menu fecha o menu
  doc.addEventListener('click', function(e) {
    if (doc.defaultView.innerWidth > 768 || !isOpen()) return;
    var b = e.target.closest && e.target.closest('[data-testid="stSidebarUserContent"] button');
    if (b && !/Sair|Sim, sair|Cancelar|Manual/.test(b.innerText)) setTimeout(function() { if (isOpen()) clickNativeBtn(); setTimeout(syncState, 100); }, 250);
  }, true);

  overlay.addEventListener('click', function() {
    if (isOpen()) clickNativeBtn();
    setTimeout(syncState, 100);
  });

  var initRetries = 0;
  function initObserver() {
    var sb = getSidebar();
    if (sb) {
      new MutationObserver(function() { syncState(); }).observe(sb, {attributes: true, attributeFilter: ['aria-expanded', 'data-collapsed']});
      syncState();
    } else if (initRetries < 10) {
      initRetries++;
      setTimeout(initObserver, 500);
    } else {
      fab.style.display = 'none';
    }
  }
  initObserver();

  window.addEventListener('resize', function() { setTimeout(syncState, 200); });

  // ── barra de baixo no celular: Início, Propostas, +, Financeiro, Menu ──
  var ICONES = {
    inicio: '<path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>',
    propostas: '<path d="M7 3h7l5 5v12a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/><path d="M14 3v5h5M9 13h6M9 17h6"/>',
    financeiro: '<path d="M3 7a2 2 0 0 1 2-2h13v4"/><path d="M3 7v11a2 2 0 0 0 2 2h15V9H5a2 2 0 0 1-2-2z"/><circle cx="16" cy="14.5" r="1.3"/>',
    menu: '<path d="M4 7h16M4 12h16M4 17h16"/>',
    mais: '<path d="M12 5v14M5 12h14"/>'
  };
  function svg(nome) {
    return '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" ' +
           'stroke-linecap="round" stroke-linejoin="round">' + ICONES[nome] + '</svg>';
  }
  var css = doc.createElement('style');
  css.textContent =
    '#barra-cel, #barra-cel-folha, #barra-cel-fundo { display:none; }' +
    '@media screen and (max-width:768px) {' +
    '  body.tem-barra #barra-cel { display:flex; }' +
    '  body.tem-barra [data-testid="stMainBlockContainer"], body.tem-barra .block-container { padding-bottom: 96px !important; }' +
    '  #barra-cel { position:fixed; left:0; right:0; bottom:0; z-index:999990; background:#fff; border-top:1px solid #E4E7EC;' +
    '    height:64px; padding:0 6px env(safe-area-inset-bottom); box-shadow:0 -2px 10px rgba(16,24,40,.06); align-items:stretch; }' +
    '  #barra-cel button { flex:1; border:0; background:none; color:#667085; font-family:inherit; font-size:11px; font-weight:600; line-height:1.1; display:flex;' +
    '    flex-direction:column; align-items:center; justify-content:center; gap:3px; padding:0; cursor:pointer; -webkit-tap-highlight-color:transparent; }' +
    '  #barra-cel button.ativo { color:#0D1B2A; }' +
    '  #barra-cel button.mais span.bola { width:46px; height:46px; border-radius:50%; background:#0D1B2A; color:#fff; display:flex;' +
    '    align-items:center; justify-content:center; margin-top:-18px; box-shadow:0 4px 12px rgba(13,27,42,.3); }' +
    '  #barra-cel-fundo.aberta { display:block; position:fixed; inset:0; background:rgba(16,24,40,.35); z-index:999991; }' +
    '  #barra-cel-folha.aberta { display:block; position:fixed; left:12px; right:12px; bottom:76px; z-index:999992; background:#fff;' +
    '    border-radius:14px; padding:8px; box-shadow:0 12px 32px rgba(16,24,40,.18); }' +
    '  #barra-cel-folha button { display:flex; width:100%; align-items:center; gap:12px; border:0; background:none; padding:14px 12px;' +
    '    border-radius:10px; font-family:inherit; font-size:15px; font-weight:600; color:#101828; text-align:left; cursor:pointer; }' +
    '  #barra-cel-folha button:active { background:#F2F4F7; }' +
    '  #barra-cel-folha small { display:block; font-weight:400; font-size:12px; color:#667085; margin-top:2px; }' +
    '}';
  doc.head.appendChild(css);

  var barra = doc.createElement('nav');
  barra.id = 'barra-cel';
  barra.setAttribute('aria-label', 'Navegação');
  var ABAS = [
    {id: 'inicio', rot: 'Início', chave: 'main_menu_dashboard'},
    {id: 'propostas', rot: 'Propostas', chave: 'main_menu_propostas'},
    {id: 'mais', rot: 'Novo', chave: null},
    {id: 'financeiro', rot: 'Financeiro', chave: 'main_menu_financeiro'},
    {id: 'menu', rot: 'Menu', chave: null}
  ];
  ABAS.forEach(function(a) {
    var b = doc.createElement('button');
    b.type = 'button';
    b.dataset.aba = a.id;
    b.setAttribute('aria-label', a.rot);
    if (a.id === 'mais') { b.className = 'mais'; b.innerHTML = '<span class="bola">' + svg('mais') + '</span>'; }
    else { b.innerHTML = svg(a.id) + '<span>' + a.rot + '</span>'; }
    b.addEventListener('click', function(e) {
      e.preventDefault();
      if (a.id === 'mais') { alternarFolha(); return; }
      fecharFolha();
      if (a.id === 'menu') { if (!isOpen()) clickNativeBtn(); setTimeout(syncState, 100); return; }
      clicarChave(a.chave);
    });
    barra.appendChild(b);
  });
  doc.body.appendChild(barra);

  var fundo = doc.createElement('div');
  fundo.id = 'barra-cel-fundo';
  fundo.addEventListener('click', fecharFolha);
  doc.body.appendChild(fundo);
  var folha = doc.createElement('div');
  folha.id = 'barra-cel-folha';
  [['acao_nova_proposta', 'Nova proposta', 'Orçamento para uma cliente'],
   ['acao_nova_cliente', 'Nova cliente', 'Nome e telefone já bastam'],
   ['acao_novo_compromisso', 'Novo compromisso', 'Diária, visita ou orçamento na agenda'],
   ['acao_novo_lancamento', 'Novo lançamento', 'Receita ou despesa no financeiro']].forEach(function(o) {
    var b = doc.createElement('button');
    b.type = 'button';
    b.innerHTML = svg('mais') + '<span>' + o[1] + '<small>' + o[2] + '</small></span>';
    b.addEventListener('click', function() { fecharFolha(); clicarChave(o[0]); });
    folha.appendChild(b);
  });
  doc.body.appendChild(folha);

  function alternarFolha() { var abrir = !folha.classList.contains('aberta'); folha.classList.toggle('aberta', abrir); fundo.classList.toggle('aberta', abrir); }
  function fecharFolha() { folha.classList.remove('aberta'); fundo.classList.remove('aberta'); }
  function clicarChave(chave) {
    var b = doc.querySelector('.st-key-' + chave + ' button');
    if (b) b.click();
  }
  var pendente = false;
  function syncBarra() {
    pendente = false;
    var logado = !!doc.querySelector('.st-key-main_menu_dashboard');
    doc.body.classList.toggle('tem-barra', logado);
    ABAS.forEach(function(a) {
      if (!a.chave) return;
      var ativo = !!doc.querySelector('.st-key-' + a.chave + ' button[kind="primary"], .st-key-' + a.chave + ' [data-testid="stBaseButton-primary"]');
      var el = barra.querySelector('[data-aba="' + a.id + '"]');
      if (el) el.classList.toggle('ativo', ativo);
    });
  }
  new MutationObserver(function() { if (!pendente) { pendente = true; setTimeout(syncBarra, 150); } })
    .observe(doc.body, {childList: true, subtree: true});
  syncBarra();
})();
</script>
""", height=0)

try:
    from utils.session_persistence import setup_session_persistence
    setup_session_persistence()
except Exception as e:
    logger.warning(f"Erro ao configurar persistência de sessão: {str(e)}")

# App Android na Google Play (o referrer mostra no Play Console de onde veio a instalação)
_PLAY = "https://play.google.com/store/apps/details?id=com.plannerorganiza.app"
PLAY_URL_LOGIN = _PLAY + "&referrer=utm_source%3Dapp_web%26utm_medium%3Dlogin"
PLAY_URL_MENU = _PLAY + "&referrer=utm_source%3Dapp_web%26utm_medium%3Dmenu"

# Google Analytics e Pixel da Meta em todas as telas, inclusive a de entrada (utils/rastreamento.py)
from utils import rastreamento
rastreamento.instalar()

# tema do anúncio e UTMs (ex.: ?tema=retorno&utm_campaign=retorno) seguem até o cadastro
rastreamento.guardar_origem(st.query_params)

# Vindo da landing ("Começar grátis"): abre direto o cadastro, com o e-mail que ela já digitou lá
if (not st.session_state.authenticated and st.query_params.get("cadastro") == "1"
        and not st.session_state.get("_cadastro_aberto")):
    st.session_state.login_page = "registrar"
    st.session_state._cadastro_aberto = True
    st.session_state._email_cadastro = st.query_params.get("email", "")

# ══════════════════════════════════════════════════════════
# BLOCO DE LOGIN — visual novo, lógica original preservada
# ══════════════════════════════════════════════════════════
if not st.session_state.authenticated:

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=DM+Sans:wght@300;400;500;600&display=swap');

    /* Mesmo layout do cartão de login da landing (promo.plannerorganiza.com.br): fundo creme com
       brilho dourado, cartão branco, título em Cormorant, Entrar azul-marinho e criar conta em dourado. */
    section[data-testid="stSidebar"],
    [data-testid="collapsedControl"],
    header[data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stDeployButton"],
    footer { display: none !important; }

    html, body, .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stHeader"] {
        background: #F7F5F0 !important;
        margin: 0 !important; padding: 0 !important;
    }
    .stApp {
        background:
            radial-gradient(ellipse 60% 80% at 70% 30%, rgba(184,151,60,.10) 0%, transparent 70%),
            radial-gradient(ellipse 40% 50% at 10% 85%, rgba(13,27,53,.06) 0%, transparent 60%),
            #F7F5F0 !important;
        min-height: 100vh !important;
    }

    /* o próprio container do Streamlit é o cartão branco */
    .main .block-container,
    [data-testid="stMainBlockContainer"] {
        max-width: 420px !important;
        margin: 4vh auto 2rem !important;
        padding: 2rem 2rem 1.5rem !important;
        background: #FFFFFF !important;
        border: 1px solid #E0DACB !important;
        border-radius: 20px !important;
        box-shadow: 0 20px 60px rgba(13,27,53,.12), 0 4px 16px rgba(184,151,60,.08) !important;
    }
    /* elementos invisíveis (estilos e scripts injetados) não ocupam espaço no cartão */
    div[data-testid="stElementContainer"]:has(iframe[height="0"]),
    div[data-testid="stElementContainer"]:has(div[data-testid="stMarkdownContainer"] > style:only-child),
    div[data-testid="stElementContainer"]:has(div[data-testid="stMarkdownContainer"] link),
    div[data-testid="stElementContainer"]:empty { display: none !important; }
    [data-testid="stVerticalBlock"] { gap: 0.6rem !important; }
    div[data-testid="stForm"] [data-testid="stVerticalBlock"] { gap: 0.75rem !important; }

    .login-logo { text-align: center; margin: 0 0 1rem; }
    .login-logo h1 {
        font-family: 'Cormorant Garamond', serif;
        font-size: 2rem; font-weight: 600;
        color: #0D1B2A; margin: 0; letter-spacing: 0.01em;
    }
    .login-logo h1::before {
        content: ""; display: inline-block; width: 10px; height: 10px; border-radius: 3px;
        background: #C9A84C; margin-right: 10px; vertical-align: 6px;
    }
    .login-logo p {
        font-size: 0.7rem; color: #B8942F; font-weight: 500;
        text-transform: uppercase; letter-spacing: 0.15em; margin: 6px 0 0;
    }
    .login-card-title {
        font-family: 'Cormorant Garamond', serif;
        font-size: 1.5rem; font-weight: 500;
        color: #0D1B2A; text-align: center; margin: 0 0 0.2rem;
    }
    .login-card-sub {
        font-size: 0.82rem; color: #6B7C94; font-weight: 300;
        text-align: center; margin: 0 0 1.5rem;
    }

    /* campos brancos com borda creme e foco dourado (caixa do Streamlit 1.66: stTextInputRootElement) */
    [data-testid="stTextInputRootElement"] {
        background: #FFFFFF !important;
        border: 1px solid #E0DACB !important;
        border-radius: 10px !important;
        color-scheme: light;
    }
    [data-testid="stTextInputRootElement"]:focus-within {
        border-color: #B8942F !important;
        box-shadow: 0 0 0 3px rgba(184,151,60,.14) !important;
    }
    [data-testid="stTextInputRootElement"] input,
    [data-testid="stTextInputRootElement"] input:focus {
        background: #FFFFFF !important; border: 0 !important; box-shadow: none !important;
        color: #16283E !important; -webkit-text-fill-color: #16283E !important; caret-color: #B8942F !important;
        padding: 0.7rem 1rem !important;
        font-family: 'DM Sans', sans-serif !important; font-size: 0.9rem !important;
    }
    [data-testid="stTextInputRootElement"] input::placeholder { color: #A9B4C2 !important; -webkit-text-fill-color: #A9B4C2 !important; }
    [data-testid="stTextInputRootElement"] input:-webkit-autofill {
        -webkit-box-shadow: 0 0 0 1000px #FFFFFF inset !important;
        -webkit-text-fill-color: #16283E !important;
    }
    [data-testid="stTextInputRootElement"] button,
    [data-testid="stTextInputRootElement"] button * { background: transparent !important; color: #6B7C94 !important; }
    div[data-testid="InputInstructions"] { display: none !important; }
    .stTextInput label, .stTextInput label * {
        color: #3A4E68 !important;
        font-size: 0.72rem !important; font-weight: 500 !important;
        text-transform: uppercase !important; letter-spacing: 0.06em !important;
    }

    /* Entrar: azul-marinho, como "Entrar no sistema" da landing */
    .stFormSubmitButton > button, .stFormSubmitButton > button * {
        background: #0D1B2A !important; color: #FFFFFF !important; border: none !important;
        border-radius: 10px !important; font-weight: 600 !important;
        font-size: 0.92rem !important; letter-spacing: 0.01em !important;
        font-family: 'DM Sans', sans-serif !important;
    }
    .stFormSubmitButton > button { padding: 0.8rem !important; width: 100% !important; min-height: 46px !important; }
    .stFormSubmitButton > button:hover, .stFormSubmitButton > button:hover * { background: #16283E !important; }
    div[data-testid="stForm"] { border: 0 !important; padding: 0 !important; }

    /* Esqueci a senha (contorno discreto) e Criar conta grátis (contorno dourado, como na landing) */
    div[data-testid="stHorizontalBlock"] .stButton > button {
        background: #FFFFFF !important; border: 1px solid #E0DACB !important; color: #3A4E68 !important;
        border-radius: 10px !important; font-family: 'DM Sans', sans-serif !important;
        font-size: 0.82rem !important; padding: 0.65rem !important; min-height: 42px !important;
    }
    div[data-testid="stHorizontalBlock"] .stButton > button * { color: inherit !important; }
    div[data-testid="stHorizontalBlock"] .stButton > button:hover { border-color: #B8942F !important; color: #0D1B2A !important; }
    div[data-testid="stHorizontalBlock"] .st-key-btn_criar_conta .stButton > button {
        border: 1.5px solid #B8942F !important; color: #8A6D12 !important; font-weight: 600 !important;
    }
    div[data-testid="stHorizontalBlock"] .st-key-btn_criar_conta .stButton > button:hover { background: #C9A84C !important; color: #0D1B2A !important; }

    .stAlert { border-radius: 10px !important; font-size: 0.85rem !important; }
    .stCheckbox label span, .stCheckbox label p, .stCheckbox label { color: #3A4E68 !important; font-size: 0.85rem !important; }
    /* botões soltos (Voltar ao login etc.) */
    .stButton > button { color: #3A4E68 !important; }

    .login-footer { text-align: center; margin-top: 1.5rem; font-size: 0.75rem; }
    .login-footer a { color: #6B7C94; text-decoration: none; transition: color 0.2s; }
    .login-footer a:hover { color: #0D1B2A; text-decoration: underline; }
    .login-footer span { color: #CBD2DB; margin: 0 0.4rem; }

    @media (max-width: 480px) {
        .main .block-container, [data-testid="stMainBlockContainer"] {
            margin: 0 auto !important; border-radius: 0 !important; border: 0 !important;
            box-shadow: none !important; padding: 2rem 1.25rem !important; min-height: 100vh;
        }
        .login-logo h1 { font-size: 1.7rem; }
    }
    </style>
    """, unsafe_allow_html=True)

    # Query params (termos/política)
    query_params = st.query_params
    if "show_termos" in query_params and query_params["show_termos"] == "true":
        try:
            from pages.termos_de_uso import show; show(); st.stop()
        except ImportError as e:
            st.error(f"Não foi possível carregar os termos de uso: {e}")
    elif "show_politica" in query_params and query_params["show_politica"] == "true":
        try:
            from pages.politica_privacidade import show; show(); st.stop()
        except ImportError as e:
            st.error(f"Não foi possível carregar a política de privacidade: {e}")

    # Verificar callback do Google login
    try:
        from utils.google_auth_component import handle_google_callback
        if handle_google_callback():
            st.rerun()
    except Exception as e:
        print(f"Erro no callback Google: {e}")

    # Sub-páginas
    if st.session_state.login_page == "registrar":
        try:
            from pages.registrar import show
            show()
            # Auto-login apos cadastro: se o Firebase registrou com sucesso,
            # session_state ja tem usuario_id — autentica direto sem pedir login
            if st.session_state.get("usuario_id") and not st.session_state.authenticated:
                uid = st.session_state.usuario_id
                from utils.database import Database
                st.session_state.db = Database(usuario_id=uid)
                st.session_state.authenticated = True
                st.session_state.current_page = "Dashboard"
                st.session_state.login_page = "login"
                st.success("Conta criada com sucesso! Entrando no sistema...")
                st.rerun()
            st.stop()
        except ImportError as e:
            st.error(f"Erro ao carregar registro: {e}")
            st.session_state.login_page = "login"
    elif st.session_state.login_page == "recuperar_senha":
        try:
            from pages.recuperar_senha import show; show(); st.stop()
        except ImportError as e:
            st.error(f"Erro ao carregar recuperação de senha: {e}")
            st.session_state.login_page = "login"

    # HTML — logo
    st.markdown("""
      <div class="login-logo">
        <h1>Planner Organiza</h1>
        <p>Sistema para Personal Organizers</p>
      </div>
    """, unsafe_allow_html=True)

    # Título do card
    st.markdown("""
      <p class="login-card-title">Bem-vinda de volta ✦</p>
      <p class="login-card-sub">Acesse sua conta para continuar</p>
    """, unsafe_allow_html=True)

    # Formulário
    with st.form("login_form"):
        email = st.text_input("E-mail", placeholder="seu@email.com")
        password = st.text_input("Senha", type="password", placeholder="••••••••")
        st.markdown('<div style="height:22px"></div>', unsafe_allow_html=True)
        submit = st.form_submit_button("Entrar na minha conta", use_container_width=True)

        if submit:
            if firebase_auth is not None:
                with st.spinner("Autenticando..."):
                    result = firebase_auth.login(email, password)
                    if result['success']:
                        if 'user' in result and 'localId' in result['user']:
                            st.session_state.usuario_id = result['user']['localId']
                            from utils.database import Database
                            st.session_state.db = Database(usuario_id=result['user']['localId'])
                        st.session_state.authenticated = True
                        st.session_state.current_page = "Dashboard"
                        st.success("Login realizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("E-mail ou senha incorretos.")
            else:
                st.error("Sistema de autenticação indisponível.")

    # Botão Google
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin:6px 0 2px;">
      <div style="flex:1;height:1px;background:#E0DACB"></div>
      <span style="font-size:0.72rem;color:#6B7C94;letter-spacing:0.1em">ou</span>
      <div style="flex:1;height:1px;background:#E0DACB"></div>
    </div>
    """, unsafe_allow_html=True)

    try:
        from utils.google_auth_component import google_login_button
        google_login_button()
    except Exception:
        pass

    # Botões secundários
    st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Esqueci a senha", key="btn_recuperar_senha", use_container_width=True):
            st.session_state.login_page = "recuperar_senha"
            st.rerun()
    with col2:
        if st.button("Criar conta grátis", key="btn_criar_conta", use_container_width=True):
            st.session_state.login_page = "registrar"
            st.rerun()

    # App Android (Google Play)
    st.markdown(f"""
      <a class="login-android" href="{PLAY_URL_LOGIN}" target="_blank" rel="noopener">
        <img src="app/static/app-android-icon.png" alt="" width="26" height="26">
        <span>Use também no celular: <b>app para Android</b></span>
      </a>
      <style>
      .login-android {{ display:flex; align-items:center; justify-content:center; gap:10px; margin:14px auto 4px;
        padding:6px 14px 6px 6px; border:1px solid #E3D9C2; border-radius:999px; background:#fff; width:fit-content;
        color:#33507A !important; font-size:.84rem; text-decoration:none !important; }}
      .login-android:hover {{ border-color:#C9A84C; }}
      .login-android img {{ border-radius:6px; display:block; }}
      .login-android b {{ color:#0D1B2A; }}
      </style>
    """, unsafe_allow_html=True)

    # Footer
    st.markdown("""
      <div class="login-footer">
        <a href="https://promo.plannerorganiza.com.br" target="_blank">Voltar ao site</a>
        <span>·</span>
        <a href="?show_termos=true">Termos de uso</a>
        <span>·</span>
        <a href="?show_politica=true">Privacidade</a>
      </div>
    """, unsafe_allow_html=True)

    st.stop()

# ══════════════════════════════════════════════════════════
# RESTANTE DO APP (autenticado) — código original inalterado
# ══════════════════════════════════════════════════════════

if 'db' not in st.session_state:
    try:
        usuario_id = None
        if 'usuario_id' in st.session_state:
            usuario_id = st.session_state.usuario_id
        elif 'user' in st.session_state and st.session_state.user and 'localId' in st.session_state.user:
            usuario_id = st.session_state.user['localId']
        elif 'usuario' in st.session_state and st.session_state.usuario:
            if isinstance(st.session_state.usuario, dict) and 'id' in st.session_state.usuario:
                usuario_id = st.session_state.usuario['id']
        if usuario_id:
            st.session_state.db = Database(usuario_id=usuario_id)
        else:
            st.session_state.db = Database()
    except Exception as e:
        st.error(f"Erro ao conectar com o banco de dados: {str(e)}")
        st.stop()

from utils.design_tokens import GLOBAL_CSS_VARS
st.markdown(f"<style>{GLOBAL_CSS_VARS}</style>", unsafe_allow_html=True)

try:
    with open('.streamlit/style.css', 'r') as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except:
    pass

st.markdown("""
<style>
[data-testid="stSidebarNav"], [data-testid="stSidebarNavItems"],
[data-testid="stSidebarNavLink"], div[data-testid="stSidebar"] nav,
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stDeployButton"], [data-testid="stMainMenuButton"] {
    display: none !important; visibility: hidden !important;
}
section[data-testid="stSidebar"] > div { padding-top: 0 !important; }
/* UX-3: ancora o conteudo ao topo, removendo o espaco em branco morto */
.main .block-container, [data-testid="stMainBlockContainer"] {
padding-top: 2rem !important;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# GATE DE TRIAL — bloqueia o acesso após 7 dias sem assinatura
# (espelha o bloqueio do app em app/_layout.tsx)
# ══════════════════════════════════════════════════════════
def _render_bloqueio_trial(perfil=None, uid=None):
    from pages.perfil import STRIPE_CHECKOUT_MENSAL, STRIPE_CHECKOUT_ANUAL, STRIPE_PORTAL_LINK, checkout_url
    _email = (perfil or {}).get('email') or ''
    _url_mensal = checkout_url(STRIPE_CHECKOUT_MENSAL, _email, uid)
    _url_anual = checkout_url(STRIPE_CHECKOUT_ANUAL, _email, uid)

    st.markdown("""
    <style>
    /* Nesta tela ninguem chama st.sidebar.*() (o gate roda antes do menu ser
       montado), entao a <section> da sidebar fica vazia mas ainda reserva a
       largura padrao, descentralizando o conteudo principal. Escondida por
       completo so aqui — nas demais paginas autenticadas ela continua normal. */
    section[data-testid="stSidebar"] { display: none !important; }
    [data-testid="stAppViewContainer"] > .main, div[data-testid="stMain"] {
        margin-left: 0 !important; width: 100% !important; max-width: 100% !important;
    }
    /* Reduz o espaco reservado do topo (header/toolbar ocultos ainda deixam
       padding no block-container) so nesta tela de bloqueio. */
    div[data-testid="stMainBlockContainer"], .main .block-container,
    section.main > div.block-container, [data-testid="stAppViewBlockContainer"] {
        padding-top: 0.8rem !important;
    }
    .pw-wrap { width: 100%; max-width: 900px; margin: 0.5rem auto 0; text-align: center;
               box-sizing: border-box; }
    .pw-icon { font-size: 50px; }
    .pw-title { color: #C9A84C; font-size: 2rem; font-weight: 800; margin: 8px 0 6px; }
    .pw-sub { color: #94a3b8; font-size: 1.05rem; max-width: 560px; margin: 0 auto 28px; line-height: 1.6; }
    .pw-cards { width: 100%; display: flex; gap: 20px; justify-content: center; align-items: stretch;
                flex-wrap: wrap; margin: 0 auto 18px; }
    .pw-card { background: #0D1B2A; border: 1px solid #1E3A5F; border-radius: 16px; padding: 28px 24px 24px;
               width: 260px; text-align: left; position: relative; }
    .pw-card.featured { border: 2px solid #C9A84C; background: linear-gradient(180deg, #132a44 0%, #0D1B2A 60%);
                         transform: scale(1.04); box-shadow: 0 8px 30px rgba(201,168,76,0.25); }
    .pw-ribbon { position: absolute; top: -13px; left: 50%; transform: translateX(-50%); background: #C9A84C;
                 color: #0D1B2A; font-size: 11px; font-weight: 800; letter-spacing: .04em; padding: 4px 14px;
                 border-radius: 20px; white-space: nowrap; }
    .pw-plan { color: #fff; font-weight: 700; font-size: 15px; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 6px; }
    .pw-price { color: #fff; font-size: 2.1rem; font-weight: 800; margin: 0; line-height: 1.1; }
    .pw-price span { font-size: .95rem; font-weight: 500; color: #94a3b8; }
    .pw-save { display: inline-block; margin-top: 6px; background: rgba(201,168,76,.15); color: #C9A84C;
               font-size: 12px; font-weight: 700; padding: 3px 10px; border-radius: 10px; }
    .pw-features { list-style: none; padding: 0; margin: 18px 0 22px; color: #cbd5e1; font-size: 13.5px; line-height: 2; }
    .pw-features li:before { content: '✓  '; color: #27AE60; font-weight: 800; }
    .pw-cta { display: block; text-align: center; text-decoration: none; padding: 12px 0; border-radius: 10px;
              font-weight: 700; font-size: 14.5px; }
    .pw-cta:hover { opacity: .88; }
    .pw-cta.primary { background: #C9A84C; color: #0D1B2A; }
    .pw-cta.outline { background: transparent; color: #C9A84C; border: 1.5px solid #C9A84C; }
    .pw-trust { color: #64748b; font-size: 12.5px; margin: 6px 0 18px; }
    .pw-manage { font-size: .88rem; color: #64748b; }
    .pw-manage a { color: #9AA5B4; }
    @media (max-width: 620px) { .pw-cards { flex-direction: column; align-items: center; } .pw-card.featured { transform: none; } }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class='pw-wrap'>
      <div class='pw-icon'>⏰</div>
      <div class='pw-title'>Seu período de teste encerrou</div>
      <div class='pw-sub'>Seus 7 dias gratuitos terminaram — mas seus clientes, propostas e dados
        continuam salvos. Assine agora e volte a organizar tudo em segundos.</div>
      <div class='pw-cards'>
        <div class='pw-card'>
          <div class='pw-plan'>Mensal</div>
          <div class='pw-price'>R$ 39,90 <span>/mês</span></div>
          <ul class='pw-features'>
            <li>Propostas e clientes ilimitados</li>
            <li>Financeiro completo</li>
            <li>Relatórios e PDFs</li>
            <li>Pós-organização</li>
          </ul>
          <a class='pw-cta outline' href='{_url_mensal}' target='_blank' {rastreamento.onclick_checkout('mensal', 39.9)}>Assinar mensal</a>
        </div>
        <div class='pw-card featured'>
          <div class='pw-ribbon'>MELHOR CUSTO-BENEFÍCIO</div>
          <div class='pw-plan'>Anual</div>
          <div class='pw-price'>R$ 297 <span>/ano</span></div>
          <div class='pw-save'>38% mais barato que o mensal</div>
          <ul class='pw-features'>
            <li>Propostas e clientes ilimitados</li>
            <li>Financeiro completo</li>
            <li>Relatórios e PDFs</li>
            <li>Pós-organização</li>
          </ul>
          <a class='pw-cta primary' href='{_url_anual}' target='_blank' {rastreamento.onclick_checkout('anual', 297)}>Assinar anual</a>
        </div>
      </div>
      <div class='pw-trust'><b>Cupom de lançamento ORGANIZA:</b> R$ 10 de desconto na primeira cobrança para as 50 primeiras assinantes (o mensal sai por R$ 29,90 no 1º mês). Digite o cupom na tela de pagamento.</div>
      <div class='pw-trust'>Pagamento seguro via Stripe · Cancele quando quiser · Dados sempre preservados</div>
      <div class='pw-manage'>Após assinar, atualize a página (a liberação pode levar alguns minutos).<br>
        Já é assinante? <a href='{STRIPE_PORTAL_LINK}' target='_blank'>Gerencie sua assinatura</a></div>
    </div>
    """, unsafe_allow_html=True)

    st.write("")
    _esq, _meio, _dir = st.columns([2, 1, 2])
    with _meio:
        if st.button("Sair da conta", key="btn_sair_trial", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.pop('_confirmar_logout', None)
            st.rerun()

try:
    from pages.perfil import carregar_perfil
    from utils.trial import trial_expirado
    _uid_trial = None
    if st.session_state.get('usuario_id'):
        _uid_trial = st.session_state.usuario_id
    elif isinstance(st.session_state.get('user'), dict) and st.session_state.user.get('localId'):
        _uid_trial = st.session_state.user['localId']
    _perfil_trial = carregar_perfil(_uid_trial or '')
    # conta criada hoje = cadastro (e-mail ou Google); plano ativo pela 1ª vez = compra
    from datetime import date as _date
    from utils.trial import _data_cadastro_para_date
    if _uid_trial and _data_cadastro_para_date((_perfil_trial or {}).get("data_cadastro")) == _date.today():
        _origem = rastreamento.origem_da_visita()
        rastreamento.evento("sign_up", "CompleteRegistration", params=_origem, uma_vez=f"po_cadastro_{_uid_trial}")
        if _origem and not st.session_state.get("_origem_salva"):
            st.session_state["_origem_salva"] = True
            st.session_state.db.salvar_origem_cadastro(_origem)
    rastreamento.compra_se_assinante(_perfil_trial, _uid_trial)
    # Teste grátis acabou e sem assinatura: a conta continua entrando, em modo consulta
    # (vê tudo, não grava nem gera PDF; utils/somente_leitura.py)
    st.session_state["somente_leitura"] = bool(trial_expirado(_perfil_trial))
except Exception as _e_trial:
    # Fail-open: se der erro ao checar, NÃO bloqueia (não trava quem pagou).
    print(f"[trial] erro ao verificar bloqueio: {_e_trial}")

if ('usuario_id' in st.session_state and st.session_state.usuario_id) or \
   ('user' in st.session_state and st.session_state.user and 'localId' in st.session_state.user):

    st.markdown("""
    <style>
    @media screen and (min-width: 769px) {
        .block-container { margin-left: 280px !important; width: calc(100% - 280px) !important; max-width: calc(100% - 280px) !important; }
        .main .block-container { margin-left: 280px !important; }
        .block-container, .main .block-container, [data-testid="stMainBlockContainer"] { padding-top: 1.5rem !important; margin-top: 0 !important; }
        [data-testid="stAppViewContainer"] > .main { margin-left: 280px !important; }
    }
    </style>
    """, unsafe_allow_html=True)

    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Dashboard"

    # ── Menu lateral ─────────────────────────────────────────────
    # Agrupado pelo trabalho do dia a dia: o que é clicável é botão com ícone;
    # os títulos de grupo são só texto. A tela aberta fica destacada (type="primary").
    _perfil_menu = globals().get('_perfil_trial') or {}
    _usuario = st.session_state.get('usuario') or {}
    _nome_menu = (_usuario.get('nome') if isinstance(_usuario, dict) else getattr(_usuario, 'nome', '')) or _perfil_menu.get('nome') or ''
    _empresa_menu = _perfil_menu.get('empresa') or ''
    st.sidebar.markdown(
        '<div class="sb-marca"><div class="sb-logo">Planner Organiza</div>'
        + (f'<div class="sb-conta">{_empresa_menu or _nome_menu}</div>' if (_empresa_menu or _nome_menu) else '')
        + '</div>', unsafe_allow_html=True)
    # teste grátis: quantos dias faltam, sempre à vista, com o caminho para assinar
    try:
        from utils.trial import is_pro as _is_pro_menu, dias_restantes_trial as _dias_menu
        if _perfil_menu and not _is_pro_menu(_perfil_menu):
            _d = _dias_menu(_perfil_menu)
            with st.sidebar.container(key="cta_trial"):
                if st.session_state.get("somente_leitura"):
                    st.markdown('<div class="sb-trial">Teste grátis <b>encerrado</b> · modo consulta</div>',
                                unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="sb-trial">Teste grátis · <b>{_d} dia{"s" if _d != 1 else ""}</b> restante{"s" if _d != 1 else ""}</div>',
                                unsafe_allow_html=True)
                if st.button("Assinar agora", key="sb_assinar", icon=":material/workspace_premium:", use_container_width=True):
                    st.session_state.current_page = "Plano"
                    st.rerun()
    except Exception:
        pass

    MENU_PRINCIPAL = [
        (None, [("Início", "Dashboard", ":material/home:"),
                ("Agenda", "Agenda", ":material/calendar_month:")]),
        ("Comercial", [
            ("Clientes", "Clientes", ":material/group:"),
            ("Propostas", "Propostas", ":material/request_quote:"),
            ("Precificação", "Precificacao", ":material/calculate:"),
            ("Vendas", "Vendas", ":material/shopping_bag:"),
            ("Pós-organização", "PosOrganizacao", ":material/event_repeat:"),
        ]),
        ("Financeiro", [
            ("Financeiro", "Financeiro", ":material/account_balance_wallet:"),
            ("Relatórios", "Relatórios", ":material/bar_chart:"),
        ]),
        ("Conta", [
            ("Cadastros", "Cadastros", ":material/inventory_2:"),
            ("Perfil e marca", "Perfil", ":material/palette:"),
            ("Plano e cobrança", "Plano", ":material/credit_card:"),
        ]),
    ]

    for _grupo, _itens in MENU_PRINCIPAL:
        if _grupo:
            st.sidebar.markdown(f'<div class="sb-grupo">{_grupo}</div>', unsafe_allow_html=True)
        for label, page, icone in _itens:
            _ativo = st.session_state.current_page == page
            if st.sidebar.button(label, key=f"main_menu_{page.lower()}", icon=icone,
                                 type="primary" if _ativo else "secondary", use_container_width=True):
                st.session_state.current_page = page
                st.session_state.pop('_confirmar_logout', None)  # navegar cancela confirmação pendente
                st.rerun()

    # ações do botão "+" da barra de baixo no celular (botões escondidos, acionados pelo script da barra)
    with st.sidebar.container(key="acoes_rapidas"):
        for _chave, _pagina, _flag in (("acao_nova_proposta", "Propostas", "kanban_nova_proposta_open"),
                                       ("acao_nova_cliente", "Clientes", "abrir_nova_cliente"),
                                       ("acao_novo_compromisso", "Agenda", "ag_novo_open"),
                                       ("acao_novo_lancamento", "Financeiro", "fin_nova_transacao_open")):
            if st.button(_chave, key=_chave):
                st.session_state.current_page = _pagina
                st.session_state[_flag] = True
                st.rerun()

    st.sidebar.markdown('<div class="sb-sep"></div>', unsafe_allow_html=True)

    if 'manual_pdf_bytes' not in st.session_state or st.session_state.manual_pdf_bytes is None:
        try:
            from pages.manual_sistema import gerar_manual_sistema
            from utils.somente_leitura import liberar_pdf
            with liberar_pdf():  # o manual continua disponível no modo consulta
                _pdf_path = gerar_manual_sistema()
            with open(_pdf_path, "rb") as _f:
                st.session_state.manual_pdf_bytes = _f.read()
        except Exception:
            st.session_state.manual_pdf_bytes = None
    if st.session_state.get('manual_pdf_bytes'):
        st.sidebar.download_button(
            label="Manual do sistema",
            data=st.session_state.manual_pdf_bytes,
            file_name="Manual_Planner_Organiza.pdf",
            mime="application/pdf",
            icon=":material/menu_book:",
            use_container_width=True,
            key="btn_manual_sidebar"
        )

    st.sidebar.link_button("App para Android", PLAY_URL_MENU, icon=":material/smartphone:", use_container_width=True)
    if st.sidebar.button("Tutorial rápido", key="btn_tutorial_sidebar", icon=":material/play_circle:",
                         use_container_width=True):
        from utils import tour
        tour.abrir()

    # Logout com confirmação: um clique acidental NUNCA encerra a sessão — apenas abre a confirmação.
    if st.session_state.get('_confirmar_logout', False):
        st.sidebar.warning("Deseja realmente sair do sistema?")
        _c1, _c2 = st.sidebar.columns(2)
        if _c1.button("Sim, sair", key="btn_logout_sim", type="secondary", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.current_page = "Dashboard"
            st.session_state.pop('_confirmar_logout', None)
            st.rerun()
        if _c2.button("Cancelar", key="btn_logout_nao", use_container_width=True):
            st.session_state.pop('_confirmar_logout', None)
            st.rerun()
    else:
        if st.sidebar.button("Sair", key="btn_logout", icon=":material/logout:", type="secondary", use_container_width=True):
            st.session_state._confirmar_logout = True
            st.rerun()

if st.session_state.authenticated:
    if 'current_page' not in st.session_state or st.session_state.get('show_welcome', True):
        st.session_state.current_page = "Dashboard"
        st.session_state.show_welcome = False

# Cor de cada módulo: selo do ícone no menu, filete do título e aba ativa da tela aberta
from utils.design_tokens import CORES_MODULO, GOLD_DARK
st.markdown("<style>" + "".join(
    f'section[data-testid="stSidebar"] .st-key-main_menu_{re.sub(r"[^a-z0-9_-]", "-", _pg.lower())} {{ --cor-item: {_cor}; --cor-item-bg: {_cor}1F; }}'
    for _pg, _cor in CORES_MODULO.items())
    + f':root {{ --modulo: {CORES_MODULO.get(st.session_state.get("current_page"), GOLD_DARK)}; }}</style>',
    unsafe_allow_html=True)

from utils.page_config import apply_page_header, apply_page_footer
apply_page_header()
apply_page_footer()

from utils import somente_leitura
if st.session_state.get("authenticated") and st.session_state.get("current_page") != "Plano":
    st.markdown(somente_leitura.CSS, unsafe_allow_html=True)
    somente_leitura.faixa()

try:
    if st.session_state.current_page == "Dashboard":
        from pages.dashboard import show; show()
    elif st.session_state.current_page == "Agenda":
        from pages.agenda import show; show()
    elif st.session_state.current_page == "Clientes":
        from pages.cadastros import show; show(modo="clientes")
    elif st.session_state.current_page == "Cadastros":
        from pages.cadastros import show; show(modo="outros")
    elif st.session_state.current_page == "Propostas":
        from pages.propostas_unificado import show; show()
    elif st.session_state.current_page == "Precificacao":
        from pages.precificacao import show; show()
    elif st.session_state.current_page == "Vendas":
        from pages.vendas import show; show()
    elif st.session_state.current_page == "Financeiro":
        from pages.financeiro import show; show()
    elif st.session_state.current_page == "PosOrganizacao":
        from pages.pos_organizacao import show; show()
    elif st.session_state.current_page == "Relatórios":
        from pages.relatorios import show; show()
    elif st.session_state.current_page == "Perfil":
        from pages.perfil import show; show()
    elif st.session_state.current_page == "Plano":
        from pages.plano import show; show()
except Exception as e:
    st.error(f"Erro ao carregar página: {str(e)}")

# Marca qual página acabou de renderizar — permite às páginas detectarem
# "entrada" (navegação) vs. rerun por interação de widget.
st.session_state["_last_page_rendered"] = st.session_state.get("current_page")
if st.session_state.get("authenticated"):
    try:
        from utils import tour
        if not somente_leitura.janela_se_tentou():  # uma janela por vez: o convite para assinar vem antes
            tour.mostrar()  # na primeira entrada da conta, ou pelo botão "Tutorial rápido" do menu
    except Exception as _e_tour:
        print(f"[tour] {_e_tour}")
rastreamento.disparar()

if "mostrar_termos" not in st.session_state:
    st.session_state.mostrar_termos = False
if "mostrar_politica" not in st.session_state:
    st.session_state.mostrar_politica = False

if st.session_state.mostrar_termos:
    with st.container():
        st.markdown("#### Termos de Uso")
        st.markdown("---")
        from pages.termos_de_uso import get_termos_conteudo
        st.markdown(get_termos_conteudo(), unsafe_allow_html=True)
        if st.button("Fechar", key="fechar_termos", type="tertiary"):
            st.session_state.mostrar_termos = False

if st.session_state.mostrar_politica:
    with st.container():
        st.markdown("#### Política de Privacidade")
        st.markdown("---")
        from pages.politica_privacidade import get_politica_conteudo
        st.markdown(get_politica_conteudo(), unsafe_allow_html=True)
        if st.button("Fechar", key="fechar_politica", type="tertiary"):
            st.session_state.mostrar_politica = False
