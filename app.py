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
        st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
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
    <div style="display:flex;align-items:center;gap:10px;margin:12px 0 4px;">
      <div style="flex:1;height:1px;background:rgba(245,240,232,0.1)"></div>
      <span style="font-size:0.72rem;color:rgba(245,240,232,0.3);letter-spacing:0.1em">OU</span>
      <div style="flex:1;height:1px;background:rgba(245,240,232,0.1)"></div>
    </div>
    """, unsafe_allow_html=True)

    try:
        from utils.google_auth_component import google_login_button
        google_login_button()
    except Exception as e:
        st.warning(f"Google login indisponível: {e}")

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
</style>
""", unsafe_allow_html=True)

if ('usuario_id' in st.session_state and st.session_state.usuario_id) or \
   ('user' in st.session_state and st.session_state.user and 'localId' in st.session_state.user):

    st.markdown("""
    <style>
    @media screen and (min-width: 769px) {
        .block-container { margin-left: 280px !important; width: calc(100% - 280px) !important; max-width: calc(100% - 280px) !important; }
        .main .block-container { margin-left: 280px !important; }
        [data-testid="stAppViewContainer"] > .main { margin-left: 280px !important; }
    }
    </style>
    """, unsafe_allow_html=True)

    st.sidebar.markdown('<div class="nav-buttons">', unsafe_allow_html=True)

    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Dashboard"

    MENU_PRINCIPAL = {
        "📊 Dashboard": "Dashboard",
        "👥 Cadastros": "Cadastros",
        "📝 Propostas": "Propostas",
        "🛒 Vendas": "Vendas",
        "💰 Financeiro": "Financeiro",
        "📋 Pós-Organização": "PosOrganizacao",
        "📈 Relatórios": "Relatórios",
        "🧑‍💼 Meu Perfil": "Perfil"
    }

    if st.session_state.get('autenticado', False) and getattr(st.session_state.get('usuario', None), 'tipo', '') == 'admin':
        MENU_PRINCIPAL["⚙️ Administração"] = "Admin"

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
            label="📥 Manual do Sistema",
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

    if st.sidebar.button("🚪 Sair do Sistema", key="btn_logout", type="secondary", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.current_page = "Dashboard"
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
        st.title("⚙️ Administração")
        st.info("Módulo de administração em desenvolvimento.")
except Exception as e:
    st.error(f"Erro ao carregar página: {str(e)}")

st.sidebar.markdown('<div style="margin:1.5rem 0;"><hr style="border:none;height:1px;background:#E0E0E0;"></div>', unsafe_allow_html=True)

with st.sidebar.expander("ℹ️ Sobre o Sistema"):
    st.markdown("**Planner Organizer** · Versão 1.0.4")
    st.markdown("""
**Módulos:**
- 📊 Dashboard — Métricas, alertas e indicadores
- 👥 Cadastros — Clientes, fornecedores, parceiros
- 📝 Propostas — Ciclo completo com relatórios PDF
- 🛒 Vendas — Produtos vendidos por cliente
- 💰 Financeiro — Kanban de receitas e despesas
- 📋 Pós-Organização — Follow-up em 6 etapas
- 📈 Relatórios — Análises e gráficos interativos
- 🧑‍💼 Perfil — Configurações da conta
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
