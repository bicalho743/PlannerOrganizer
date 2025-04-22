import streamlit as st
import time

# Configuração da página
st.set_page_config(
    page_title="Planner Organizer - Login",
    page_icon="favicon.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS para a página de login
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    
    body {
        font-family: 'Poppins', sans-serif;
        background: linear-gradient(135deg, #f9fafc, #eef5ff);
        color: #333;
    }
    
    .login-container {
        background: white;
        border-radius: 10px;
        padding: 2rem;
        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
        max-width: 500px;
        margin: 0 auto;
    }
    
    .login-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .login-title {
        color: #1E366F;
        font-size: 1.8rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .login-subtitle {
        color: #6c757d;
        font-size: 1rem;
    }
    
    .form-group {
        margin-bottom: 1.5rem;
    }
    
    /* Remove cabeçalho do Streamlit */
    header {visibility: hidden;}
    
    /* Remove menu, footer e botão de deploy */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    
    /* Ajusta o layout para ficar mais compacto */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
    
    /* Centraliza o conteúdo */
    .element-container {
        max-width: 550px;
        margin-left: auto;
        margin-right: auto;
    }
    
    /* Botão estilizado */
    .stButton > button {
        background: linear-gradient(135deg, #2d8cff, #0063cc);
        color: white;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #0063cc, #004a99);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Links */
    a {
        color: #2d8cff;
        text-decoration: none;
    }
    
    a:hover {
        text-decoration: underline;
    }
    
    /* Divisor */
    .divider {
        display: flex;
        align-items: center;
        text-align: center;
        margin: 1.5rem 0;
    }
    
    .divider::before,
    .divider::after {
        content: '';
        flex: 1;
        border-bottom: 1px solid #e0e0e0;
    }
    
    .divider::before {
        margin-right: .5em;
    }
    
    .divider::after {
        margin-left: .5em;
    }
    
    /* Centralize o formulário */
    .centered-form {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 80vh;
    }
    
    /* Logo estilizado */
    .logo {
        margin-bottom: 1.5rem;
        text-align: center;
    }
    
    .logo h1 {
        color: #1E366F;
        font-weight: 700;
        font-size: 2.2rem;
        margin-bottom: 0;
    }
    
    .logo span {
        color: #2d8cff;
    }
</style>
""", unsafe_allow_html=True)

# Verificar autenticação
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if st.session_state.authenticated:
    st.success("Login realizado com sucesso! Redirecionando...")
    st.switch_page("app_simple.py")

# Layout da página de login
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown('<div class="centered-form">', unsafe_allow_html=True)
    
    # Logo
    st.markdown("""
    <div class="logo">
        <h1>Planner<span>Organizer</span></h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Container de login
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    # Cabeçalho do login
    st.markdown("""
    <div class="login-header">
        <h2 class="login-title">Bem-vindo de volta</h2>
        <p class="login-subtitle">Faça login para acessar sua conta</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Formulário de login
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="Seu endereço de email")
        password = st.text_input("Senha", type="password", placeholder="Sua senha")
        
        # Lembrar-me e Esqueceu a senha
        cols = st.columns([1, 1])
        with cols[0]:
            remember = st.checkbox("Lembrar-me")
        with cols[1]:
            st.markdown('<div style="text-align: right;"><a href="#">Esqueceu a senha?</a></div>', unsafe_allow_html=True)
        
        st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
        login_button = st.form_submit_button("Entrar", use_container_width=True)
        
        if login_button:
            if email == "admin" and password == "admin":
                with st.spinner("Autenticando..."):
                    time.sleep(1)
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Email ou senha incorretos")
    
    # Divisor "ou"
    st.markdown('<div class="divider">ou</div>', unsafe_allow_html=True)
    
    # Botões de login social
    if st.button("Continuar com Google", key="google"):
        with st.spinner("Redirecionando para autenticação do Google..."):
            time.sleep(1)
        st.info("Modo de manutenção: O login com Google está temporariamente indisponível")
    
    if st.button("Continuar com Facebook", key="facebook"):
        with st.spinner("Redirecionando para autenticação do Facebook..."):
            time.sleep(1)
        st.info("Modo de manutenção: O login com Facebook está temporariamente indisponível")
    
    # Link para criar conta
    st.markdown("""
    <div style="text-align: center; margin-top: 1.5rem;">
        Não tem uma conta? <a href="#">Criar Conta</a>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)  # Fecha o login-container
    st.markdown('</div>', unsafe_allow_html=True)  # Fecha o centered-form

# Link para acessar o modo de demonstração
st.markdown("""
<div style="text-align: center; margin-top: 1rem; font-size: 0.9rem; color: #6c757d;">
    Para demonstração, use: <b>admin</b> / <b>admin</b>
</div>
""", unsafe_allow_html=True)