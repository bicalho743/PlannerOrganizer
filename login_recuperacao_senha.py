"""
Página minimalista de login com recuperação de senha usando Firebase Auth
"""
import streamlit as st 
from utils.firebase_auth import redefinir_senha
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Login - Planner Organizer",
    page_icon="🔒",
    layout="centered"
)

# Inicializar variáveis de sessão
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"  # login, reset_password, signup
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "message" not in st.session_state:
    st.session_state.message = None
if "message_type" not in st.session_state:
    st.session_state.message_type = None

# Funções para alterar o modo
def switch_to_login():
    st.session_state.auth_mode = "login"

def switch_to_reset():
    st.session_state.auth_mode = "reset_password"

def switch_to_signup():
    st.session_state.auth_mode = "signup"

def show_message(message, type="info"):
    st.session_state.message = message
    st.session_state.message_type = type

def login_user(email, password):
    """Função de login simulada (substitua pela integração real)"""
    if email == "demo@example.com" and password == "senha123":
        st.session_state.authenticated = True
        st.session_state.user = {
            "email": email,
            "login_time": datetime.now().isoformat()
        }
        show_message("Login bem-sucedido!", "success")
        return True
    else:
        show_message("Email ou senha incorretos.", "error")
        return False

def create_account(email, password, confirm_password):
    """Função de criação de conta simulada (substitua pela integração real)"""
    if not email or not password:
        show_message("Email e senha são obrigatórios.", "error")
        return False
    
    if password != confirm_password:
        show_message("As senhas não coincidem.", "error")
        return False
    
    if len(password) < 6:
        show_message("A senha deve ter pelo menos 6 caracteres.", "error")
        return False
    
    # Simulação de sucesso
    show_message("Conta criada com sucesso! Um email de verificação foi enviado.", "success")
    return True

def logout():
    """Função para fazer logout"""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.auth_mode = "login"
    show_message("Logout realizado com sucesso.", "info")

# Estilo CSS básico
st.markdown("""
<style>
    .main-title {
        text-align: center;
        color: #2557D6;
        margin-bottom: 1rem;
    }
    
    .auth-container {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Título principal
st.markdown("<h1 class='main-title'>Planner Organizer</h1>", unsafe_allow_html=True)

# Exibir mensagem se houver
if st.session_state.message:
    if st.session_state.message_type == "success":
        st.success(st.session_state.message)
    elif st.session_state.message_type == "error":
        st.error(st.session_state.message)
    elif st.session_state.message_type == "info":
        st.info(st.session_state.message)
    elif st.session_state.message_type == "warning":
        st.warning(st.session_state.message)
    
    # Limpar mensagem após exibição
    st.session_state.message = None
    st.session_state.message_type = None

# Renderizar a interface apropriada
if st.session_state.authenticated:
    # Área logada
    st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
    st.subheader(f"Bem-vindo, {st.session_state.user.get('email')}")
    
    # Informações do usuário
    st.write("### Dados do usuário")
    st.json(st.session_state.user)
    
    # Botões de ação
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Acessar Sistema", use_container_width=True):
            st.info("Redirecionando para o sistema...")
            # Aqui você adicionaria o redirecionamento
    
    with col2:
        if st.button("Sair", use_container_width=True):
            logout()
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

else:
    # Área de autenticação
    if st.session_state.auth_mode == "login":
        # Login
        st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
        st.subheader("Login")
        
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Senha", type="password", key="login_password")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Entrar", use_container_width=True):
                if login_user(email, password):
                    st.rerun()
        
        with col2:
            if st.button("Modo Demo", use_container_width=True):
                st.session_state.authenticated = True
                st.session_state.user = {
                    "email": "demo@example.com",
                    "name": "Usuário Demo",
                    "demo": True,
                    "login_time": datetime.now().isoformat()
                }
                st.rerun()
        
        # Opções adicionais
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Criar conta", use_container_width=True):
                switch_to_signup()
                st.rerun()
        
        with col2:
            if st.button("Esqueci a senha", use_container_width=True):
                switch_to_reset()
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    elif st.session_state.auth_mode == "reset_password":
        # Reset de senha
        st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
        st.subheader("Recuperação de Senha")
        
        email = st.text_input("Email", key="reset_email", 
                            help="Digite seu email cadastrado para receber o link de recuperação")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Enviar Link", use_container_width=True):
                if email:
                    if redefinir_senha(email):
                        show_message(f"Email de recuperação enviado para {email}.", "success")
                    else:
                        show_message("Erro ao enviar email de recuperação. Verifique o email informado.", "error")
                else:
                    show_message("Por favor, informe seu email.", "error")

        with col2:
            if st.button("Voltar ao Login", use_container_width=True):
                switch_to_login()
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    elif st.session_state.auth_mode == "signup":
        # Criar conta
        st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
        st.subheader("Criar Conta")
        
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Senha", type="password", key="signup_password", 
                               help="Mínimo de 6 caracteres")
        confirm_password = st.text_input("Confirmar Senha", type="password", 
                                       key="signup_confirm_password")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Criar Conta", use_container_width=True):
                if create_account(email, password, confirm_password):
                    # Mostrar mensagem e voltar para login em 3 segundos
                    import time
                    time.sleep(2)
                    switch_to_login()
                    st.rerun()
        
        with col2:
            if st.button("Voltar ao Login", use_container_width=True):
                switch_to_login()
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)

# Rodapé
st.markdown("""
<div style="text-align: center; margin-top: 2rem; color: #666; font-size: 0.8rem;">
    <p>© 2025 Planner Organizer. Todos os direitos reservados.</p>
</div>
""", unsafe_allow_html=True)