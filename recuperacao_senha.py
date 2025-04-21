"""
Página simplificada para apresentar a funcionalidade de recuperação de senha
Esta versão usa a porta 5000 e configurações mínimas para garantir funcionalidade
"""
import streamlit as st
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Recuperação de Senha - Planner Organizer",
    page_icon="🔑",
    layout="centered"
)

# Inicializar variáveis de sessão
if "view" not in st.session_state:
    st.session_state.view = "login"  # login, signup, reset, success

# Estilos CSS
st.markdown("""
<style>
    .main-title {
        text-align: center;
        color: #2557D6;
        margin-bottom: 1rem;
    }
    
    .container {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    
    .footer {
        text-align: center;
        margin-top: 2rem;
        color: #666;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# Título principal
st.markdown("<h1 class='main-title'>Planner Organizer</h1>", unsafe_allow_html=True)

# Funções de visualização
def show_login():
    st.markdown("<div class='container'>", unsafe_allow_html=True)
    st.subheader("Login")
    
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Senha", type="password", key="login_password")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Entrar", use_container_width=True):
            st.success("Login simulado com sucesso!")
            st.session_state.view = "success"
            st.rerun()
    
    with col2:
        if st.button("Modo Demo", use_container_width=True):
            st.success("Modo de demonstração ativado!")
            st.session_state.view = "success"
            st.rerun()
    
    # Links para outras ações
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Criar conta", key="goto_signup", use_container_width=True):
            st.session_state.view = "signup"
            st.rerun()
    
    with col2:
        if st.button("Esqueci minha senha", key="goto_reset", use_container_width=True):
            st.session_state.view = "reset"
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

def show_signup():
    st.markdown("<div class='container'>", unsafe_allow_html=True)
    st.subheader("Criar Conta")
    
    email = st.text_input("Email", key="signup_email")
    password = st.text_input("Senha", type="password", key="signup_password",
                            help="Mínimo de 6 caracteres")
    confirm_password = st.text_input("Confirmar Senha", type="password", 
                                    key="signup_confirm_password")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Criar Conta", key="do_signup", use_container_width=True):
            if not email or not password:
                st.error("Email e senha são obrigatórios.")
            elif password != confirm_password:
                st.error("As senhas não coincidem.")
            elif len(password) < 6:
                st.error("A senha deve ter pelo menos 6 caracteres.")
            else:
                st.success("Conta criada com sucesso! Verifique seu email para ativar.")
                # Simulação de delay
                import time
                time.sleep(2)
                st.session_state.view = "login"
                st.rerun()
    
    with col2:
        if st.button("Voltar ao Login", key="back_to_login1", use_container_width=True):
            st.session_state.view = "login"
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

def show_reset_password():
    st.markdown("<div class='container'>", unsafe_allow_html=True)
    st.subheader("Recuperação de Senha")
    
    st.info("Digite seu email abaixo para receber um link de recuperação de senha.")
    
    email = st.text_input("Email", key="reset_email",
                         help="Digite o email cadastrado")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Enviar Link", key="do_reset", use_container_width=True):
            if not email:
                st.error("Por favor, digite seu email.")
            else:
                st.success(f"Email de recuperação enviado para {email}.")
                st.info("Verifique sua caixa de entrada (e a pasta de spam) para o link de recuperação.")
                
                # Simulação de delay
                import time
                time.sleep(2)
                st.session_state.view = "login"
                st.rerun()
    
    with col2:
        if st.button("Voltar ao Login", key="back_to_login2", use_container_width=True):
            st.session_state.view = "login"
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

def show_success():
    st.markdown("<div class='container'>", unsafe_allow_html=True)
    st.success("Login realizado com sucesso!")
    
    st.write("### Área do Usuário")
    st.write("Usuário: demo@example.com")
    st.write("Último acesso: ", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    
    if st.button("Sair", key="logout", use_container_width=True):
        st.session_state.view = "login"
        st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

# Mostrar a visualização adequada
if st.session_state.view == "login":
    show_login()
elif st.session_state.view == "signup":
    show_signup()
elif st.session_state.view == "reset":
    show_reset_password()
elif st.session_state.view == "success":
    show_success()

# Informações no rodapé
st.markdown("""
<div class="footer">
    <p>© 2025 Planner Organizer. Todos os direitos reservados.</p>
    <p>Este é um sistema de demonstração da funcionalidade de recuperação de senha.</p>
</div>
""", unsafe_allow_html=True)