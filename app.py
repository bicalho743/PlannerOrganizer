import os
import sys
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
if "show_planos" not in st.session_state:
    st.session_state.show_planos = False
if "show_enviar_manual" not in st.session_state:
    st.session_state.show_enviar_manual = False
if "show_debug_propostas_finalizadas" not in st.session_state:
    st.session_state.show_debug_propostas_finalizadas = False

st.set_page_config(
    
    page_title="Planner Organizer | Sistema para Personal Organizers",
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
    '  #mobile-sidebar-fab { display:flex !important; }' +
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

  function isOpen() {
    var sb = getSidebar();
    return sb && sb.getAttribute('aria-expanded') === 'true';
  }

  function clickNativeBtn() {
    var btns = doc.querySelectorAll(
      'button[data-testid="collapsedControl"],' +
      'button[data-testid="stBaseButton-headerNoPadding"]'
    );
    for (var i = 0; i < btns.length; i++) { btns[i].click(); return true; }
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
    } else {
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

  overlay.addEventListener('click', function() {
    if (isOpen()) clickNativeBtn();
    setTimeout(syncState, 100);
  });

  var initRetries = 0;
  function initObserver() {
    var sb = getSidebar();
    if (sb) {
      new MutationObserver(function() { syncState(); }).observe(sb, {attributes: true, attributeFilter: ['aria-expanded']});
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
})();
</script>
""", height=0)

try:
    from utils.session_persistence import setup_session_persistence
    from utils.auto_login import check_and_restore_auto_login
    setup_session_persistence()
    check_and_restore_auto_login()
except Exception as e:
    logger.warning(f"Erro ao configurar persistência de sessão: {str(e)}")

# ══════════════════════════════════════════════════════════
# BLOCO DE LOGIN — visual novo, lógica original preservada
# ══════════════════════════════════════════════════════════
if not st.session_state.authenticated:

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=DM+Sans:wght@300;400;500&display=swap');

    section[data-testid="stSidebar"],
    [data-testid="collapsedControl"],
    header[data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stDeployButton"],
    footer { display: none !important; }

    /* Fundo escuro em tudo */
    html, body, .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stHeader"] {
        background: #0D1B35 !important;
        margin: 0 !important; padding: 0 !important;
    }
    .stApp {
        background:
            radial-gradient(ellipse 60% 50% at 30% 20%, rgba(201,168,76,0.08) 0%, transparent 60%),
            radial-gradient(ellipse 40% 60% at 70% 80%, rgba(26,48,96,0.4) 0%, transparent 60%),
            #0D1B35 !important;
        min-height: 100vh !important;
    }

    /* Container principal centralizado e estreito */
    .main .block-container,
    [data-testid="stMainBlockContainer"] {
        max-width: 420px !important;
        margin: 0 auto !important;
        padding: 3rem 1rem 2rem !important;
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(201,168,76,0.18) !important;
        border-radius: 20px !important;
        backdrop-filter: blur(20px) !important;
    }

    /* Logo acima do card — sem fundo */
    .login-logo {
        background: transparent !important;
        border: none !important;
    }

    /* Tirar gap entre elementos */
    [data-testid="stVerticalBlock"] { gap: 0 !important; }

    /* Logo centralizado */
    .login-logo { text-align: center; margin-bottom: 2rem; margin-top: 1rem; }
    .login-logo h1 {
        font-family: 'Cormorant Garamond', serif;
        font-size: 2rem; font-weight: 600;
        color: #F5F0E8; margin: 0; letter-spacing: 0.02em;
    }
    .login-logo p {
        font-size: 0.72rem; color: rgba(245,240,232,0.38);
        text-transform: uppercase; letter-spacing: 0.15em; margin: 5px 0 0;
    }

    .login-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(201,168,76,0.18);
        border-radius: 20px;
        padding: 2.5rem 2rem;
        width: 100%; max-width: 400px;
        backdrop-filter: blur(20px);
    }
    .login-card-title {
        font-family: 'Cormorant Garamond', serif;
        font-size: 1.5rem; font-weight: 500;
        color: #F5F0E8; text-align: center; margin: 0 0 0.2rem;
    }
    .login-card-sub {
        font-size: 0.8rem; color: rgba(245,240,232,0.38);
        text-align: center; margin: 0 0 1.75rem;
    }

    /* Inputs */
    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(201,168,76,0.22) !important;
        border-radius: 10px !important;
        color: #F5F0E8 !important;
        padding: 0.75rem 1rem !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 0.875rem !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: rgba(201,168,76,0.55) !important;
        background: rgba(255,255,255,0.08) !important;
        box-shadow: 0 0 0 3px rgba(201,168,76,0.08) !important;
    }
    .stTextInput > div > div > input::placeholder { color: rgba(245,240,232,0.22) !important; }
    .stTextInput label {
        color: rgba(245,240,232,0.55) !important;
        font-size: 0.72rem !important; font-weight: 500 !important;
        text-transform: uppercase !important; letter-spacing: 0.09em !important;
    }

    /* Botão submit (Entrar) */
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, #C9A84C, #9E7A10) !important;
        color: #0D1B35 !important; border: none !important;
        border-radius: 10px !important; font-weight: 700 !important;
        font-size: 0.875rem !important; letter-spacing: 0.06em !important;
        padding: 0.75rem !important; width: 100% !important;
        font-family: 'DM Sans', sans-serif !important;
        transition: opacity 0.2s !important;
    }
    .stFormSubmitButton > button:hover { opacity: 0.88 !important; }

    /* Botões secundários */
    div[data-testid="stHorizontalBlock"] .stButton > button {
        background: transparent !important;
        border: 1px solid rgba(201,168,76,0.22) !important;
        color: rgba(245,240,232,0.55) !important;
        border-radius: 10px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 0.78rem !important;
        padding: 0.65rem !important;
        transition: all 0.2s !important;
    }
    div[data-testid="stHorizontalBlock"] .stButton > button:hover {
        border-color: rgba(201,168,76,0.5) !important;
        color: #C9A84C !important;
        background: rgba(201,168,76,0.06) !important;
    }

    .stAlert { border-radius: 10px !important; font-size: 0.85rem !important; }

    /* Checkbox (termos de uso na tela de registro) */
    .stCheckbox label span,
    .stCheckbox label p,
    .stCheckbox label {
        color: rgba(245,240,232,0.7) !important;
        font-size: 0.85rem !important;
    }
    /* Botão genérico (Voltar ao login, etc) */
    .stButton > button {
        color: rgba(245,240,232,0.55) !important;
    }

    .login-footer {
        text-align: center; margin-top: 1.5rem; font-size: 0.75rem;
    }
    .login-footer a {
        color: rgba(245,240,232,0.3); text-decoration: none; transition: color 0.2s;
    }
    .login-footer a:hover { color: rgba(245,240,232,0.65); }
    .login-footer span { color: rgba(245,240,232,0.12); margin: 0 0.4rem; }

    @media (max-width: 480px) {
        .login-card { padding: 2rem 1.25rem; }
        .login-logo h1 { font-size: 1.6rem; }
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
        <h1>Planner Organizer</h1>
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
                        st.success("✅ Login realizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("E-mail ou senha incorretos.")
            else:
                st.error("Sistema de autenticação indisponível.")

    # Botão Google
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin:16px 0 6px;">
      <div style="flex:1;height:1px;background:rgba(245,240,232,0.1)"></div>
      <span style="font-size:0.72rem;color:rgba(245,240,232,0.3);letter-spacing:0.1em">OU</span>
      <div style="flex:1;height:1px;background:rgba(245,240,232,0.1)"></div>
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

    # Footer
    st.markdown("""
      <div class="login-footer">
        <a href="https://promo.plannerorganiza.com.br" target="_blank">← Voltar ao site</a>
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
def _render_bloqueio_trial(perfil=None):
    from pages.perfil import STRIPE_CHECKOUT_MENSAL, STRIPE_CHECKOUT_ANUAL, STRIPE_PORTAL_LINK, checkout_url
    _email = (perfil or {}).get('email') or ''
    _url_mensal = checkout_url(STRIPE_CHECKOUT_MENSAL, _email)
    _url_anual = checkout_url(STRIPE_CHECKOUT_ANUAL, _email)

    st.markdown("""
    <style>
    .pw-wrap { max-width: 900px; margin: 1rem auto 0; text-align: center; }
    .pw-icon { font-size: 50px; }
    .pw-title { color: #C9A84C; font-size: 2rem; font-weight: 800; margin: 8px 0 6px; }
    .pw-sub { color: #94a3b8; font-size: 1.05rem; max-width: 560px; margin: 0 auto 28px; line-height: 1.6; }
    .pw-cards { display: flex; gap: 20px; justify-content: center; align-items: stretch; flex-wrap: wrap; margin-bottom: 18px; }
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
          <div class='pw-price'>R$ 29,90 <span>/mês</span></div>
          <ul class='pw-features'>
            <li>Propostas e clientes ilimitados</li>
            <li>Financeiro completo</li>
            <li>Relatórios e PDFs</li>
            <li>Pós-organização</li>
            <li>Suporte prioritário</li>
          </ul>
          <a class='pw-cta outline' href='{_url_mensal}' target='_blank'>Assinar Mensal</a>
        </div>
        <div class='pw-card featured'>
          <div class='pw-ribbon'>MAIS POPULAR</div>
          <div class='pw-plan'>Anual</div>
          <div class='pw-price'>R$ 297 <span>/ano</span></div>
          <div class='pw-save'>💰 Economize 2 meses</div>
          <ul class='pw-features'>
            <li>Propostas e clientes ilimitados</li>
            <li>Financeiro completo</li>
            <li>Relatórios e PDFs</li>
            <li>Pós-organização</li>
            <li>Suporte prioritário</li>
          </ul>
          <a class='pw-cta primary' href='{_url_anual}' target='_blank'>🚀 Assinar Anual</a>
        </div>
      </div>
      <div class='pw-trust'>🔒 Pagamento seguro via Stripe · Cancele quando quiser · Dados sempre preservados</div>
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
    if trial_expirado(_perfil_trial):
        _render_bloqueio_trial(_perfil_trial)
        st.stop()
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

    st.sidebar.markdown('<div class="nav-buttons">', unsafe_allow_html=True)

    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Dashboard"

    MENU_PRINCIPAL = {
        "Dashboard": "Dashboard",
        "Cadastros": "Cadastros",
        "Propostas": "Propostas",
        "Vendas": "Vendas",
        "Financeiro": "Financeiro",
        "Pós-Organização": "PosOrganizacao",
        "Relatórios": "Relatórios",
        "Meu Perfil": "Perfil"
    }

    if st.session_state.get('autenticado', False) and getattr(st.session_state.get('usuario', None), 'tipo', '') == 'admin':
        MENU_PRINCIPAL["Administração"] = "Admin"

    if 'manual_pdf_bytes' not in st.session_state or st.session_state.manual_pdf_bytes is None:
        try:
            from pages.manual_sistema import gerar_manual_sistema
            _pdf_path = gerar_manual_sistema()
            with open(_pdf_path, "rb") as _f:
                st.session_state.manual_pdf_bytes = _f.read()
        except Exception:
            st.session_state.manual_pdf_bytes = None

    if st.session_state.get('manual_pdf_bytes'):
        st.sidebar.download_button(
            label="Manual do Sistema",
            data=st.session_state.manual_pdf_bytes,
            file_name="Manual_Planner_Organizer.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="btn_manual_sidebar"
        )

    st.sidebar.markdown('<div style="margin:4px 0;"><hr style="border:none;height:1px;background:#E0E0E0;"></div>', unsafe_allow_html=True)

    for label, page in MENU_PRINCIPAL.items():
        if st.sidebar.button(label, key=f"main_menu_{page.lower()}", use_container_width=True):
            st.session_state.current_page = page
            st.session_state.pop('_confirmar_logout', None)  # navegar cancela confirmação pendente

    # Separação extra entre o menu e o botão de sair (reduz clique acidental
    # por layout shift logo após o carregamento).
    st.sidebar.markdown('<div style="margin:14px 0;"><hr style="border:none;height:1px;background:#E0E0E0;"></div>', unsafe_allow_html=True)

    # Logout com confirmação: um clique acidental (por coordenada/overlap logo
    # após o load) NUNCA encerra a sessão — apenas abre a confirmação.
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
        if st.sidebar.button("Sair do Sistema", key="btn_logout", type="secondary", use_container_width=True):
            st.session_state._confirmar_logout = True
            st.rerun()

    st.sidebar.markdown('</div>', unsafe_allow_html=True)

if st.session_state.authenticated:
    if 'current_page' not in st.session_state or st.session_state.get('show_welcome', True):
        st.session_state.current_page = "Dashboard"
        st.session_state.show_welcome = False

from utils.page_config import apply_page_header, apply_page_footer
apply_page_header()
apply_page_footer()

try:
    if st.session_state.current_page == "Dashboard":
        from pages.dashboard import show; show()
    elif st.session_state.current_page == "Cadastros":
        from pages.cadastros import show; show()
    elif st.session_state.current_page == "Propostas":
        from pages.propostas_unificado import show; show()
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
    elif st.session_state.current_page == "Admin":
        st.title("Administração")
        st.info("Módulo de administração em desenvolvimento.")
except Exception as e:
    st.error(f"Erro ao carregar página: {str(e)}")

# Marca qual página acabou de renderizar — permite às páginas detectarem
# "entrada" (navegação) vs. rerun por interação de widget.
st.session_state["_last_page_rendered"] = st.session_state.get("current_page")

st.sidebar.markdown('<div style="margin:1.5rem 0;"><hr style="border:none;height:1px;background:#E0E0E0;"></div>', unsafe_allow_html=True)

with st.sidebar.expander("Sobre o Sistema"):
    st.markdown("**Planner Organizer** · Versão 1.0.4")
    st.markdown("""
**Módulos:**
- Dashboard — Métricas, alertas e indicadores
- Cadastros — Clientes, fornecedores, parceiros
- Propostas — Ciclo completo com relatórios PDF
- Vendas — Produtos vendidos por cliente
- Financeiro — Kanban de receitas e despesas
- Pós-Organização — Follow-up em 6 etapas
- Relatórios — Análises e gráficos interativas
- Perfil — Configurações da conta
    """)

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
        if st.button("Fechar", key="fechar_termos", use_container_width=True):
            st.session_state.mostrar_termos = False

if st.session_state.mostrar_politica:
    with st.container():
        st.markdown("#### Política de Privacidade")
        st.markdown("---")
        from pages.politica_privacidade import get_politica_conteudo
        st.markdown(get_politica_conteudo(), unsafe_allow_html=True)
        if st.button("Fechar", key="fechar_politica", use_container_width=True):
            st.session_state.mostrar_politica = False
