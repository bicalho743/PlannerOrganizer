"""
Versão simplificada da página de login moderna
"""
import streamlit as st
import os

# Configuração
st.set_page_config(page_title="Login Simplificado", page_icon="🔐", layout="centered")

# Inicializar estado da sessão
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "login_mode" not in st.session_state:
    st.session_state.login_mode = "login"

# CSS customizado
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
    
    .auth-container {
        max-width: 450px;
        margin: 0 auto;
        padding: 2rem;
        background: white;
        border-radius: 10px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.08);
    }
    
    .auth-header {
        text-align: center;
        margin-bottom: 1.5rem;
    }
    
    .auth-title {
        font-size: 1.75rem;
        color: #1E366F;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .auth-subtitle {
        color: #6c757d;
        font-size: 0.95rem;
    }
    
    .auth-footer {
        margin-top: 1.5rem;
        text-align: center;
        font-size: 0.9rem;
    }
    
    .auth-divider {
        display: flex;
        align-items: center;
        margin: 1.5rem 0;
        color: #6c757d;
        font-size: 0.85rem;
    }
    
    .auth-divider:before, .auth-divider:after {
        content: "";
        flex: 1;
        border-bottom: 1px solid #e0e0e0;
    }
    
    .auth-divider:before {
        margin-right: 0.5rem;
    }
    
    .auth-divider:after {
        margin-left: 0.5rem;
    }
    
    .social-buttons {
        margin-bottom: 1.5rem;
    }
    
    .social-button {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100%;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        font-weight: 500;
        cursor: pointer;
        margin-bottom: 0.75rem;
        transition: all 0.2s ease;
    }
    
    .social-button img {
        width: 20px;
        height: 20px;
        margin-right: 10px;
    }
    
    .google-button {
        background-color: white;
        border: 1px solid #e0e0e0;
        color: #333;
    }
    
    .auth-note {
        font-size: 0.85rem;
        color: #718096;
        text-align: center;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def login_user_simple(email, password):
    """Versão simplificada da função de login"""
    if email == "admin" and password == "admin":
        return {"success": True, "message": "Login realizado com sucesso!"}
    return {"success": False, "message": "Email ou senha incorretos."}

def register_user_simple(email, password, name):
    """Versão simplificada da função de registro"""
    return {"success": True, "message": "Conta criada com sucesso! (simulação)"}

def reset_password_simple(email):
    """Versão simplificada da função de recuperação de senha"""
    return {"success": True, "message": "Email de recuperação enviado! (simulação)"}

# Verificar se já está autenticado
if st.session_state.authenticated:
    st.title("Área Restrita")
    st.success("Você está autenticado e tem acesso a esta área restrita.")
    
    if st.button("Sair"):
        st.session_state.authenticated = False
        st.rerun()
else:
    # Container principal para a área de autenticação
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    
    # Cabeçalho
    st.markdown('<div class="auth-header">', unsafe_allow_html=True)
    st.markdown('<h1 class="auth-title">Planner Organizer</h1>', unsafe_allow_html=True)
    
    # Verificar o modo da página
    page_mode = st.session_state.login_mode
    
    if page_mode == "login":
        # Login
        st.markdown('<p class="auth-subtitle">Acesse sua conta para continuar</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)  # Fim do cabeçalho
        
        # Botões de redes sociais
        st.markdown('<div class="social-buttons">', unsafe_allow_html=True)
        st.markdown('''
        <div class="social-button google-button">
            <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" alt="Google">
            <span>Continuar com Google</span>
        </div>
        ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Divisor
        st.markdown('<div class="auth-divider">ou entre com e-mail</div>', unsafe_allow_html=True)
        
        # Formulário de login
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="Seu email...", key="login_email")
            password = st.text_input("Senha", placeholder="Sua senha...", type="password", key="login_password")
            
            login_submitted = st.form_submit_button("Entrar na minha conta", use_container_width=True)
            
            if login_submitted:
                result = login_user_simple(email, password)
                
                if result["success"]:
                    st.success(result["message"])
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error(result["message"])
        
        # Botões secundários
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Esqueceu sua senha?", key="forgot_btn"):
                st.session_state.login_mode = "reset"
                st.rerun()
        
        with col2:
            if st.button("Criar uma conta", key="create_btn"):
                st.session_state.login_mode = "register"
                st.rerun()
        
        # Nota de demo
        st.markdown('''
        <div class="auth-note">
            Para demonstração, use: admin / admin
        </div>
        ''', unsafe_allow_html=True)
    
    elif page_mode == "register":
        # Registro
        st.markdown('<p class="auth-subtitle">Crie sua conta para começar</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)  # Fim do cabeçalho
        
        # Formulário de registro
        with st.form("register_form"):
            name = st.text_input("Nome completo", placeholder="Seu nome...", key="register_name")
            email = st.text_input("Email", placeholder="Seu email...", key="register_email")
            password = st.text_input("Senha", placeholder="Crie uma senha...", type="password", key="register_password")
            confirm_password = st.text_input("Confirmar senha", placeholder="Repita sua senha...", type="password", key="register_confirm")
            
            register_submitted = st.form_submit_button("Criar minha conta", use_container_width=True)
            
            if register_submitted:
                if password != confirm_password:
                    st.error("As senhas não coincidem")
                else:
                    result = register_user_simple(email, password, name)
                    
                    if result["success"]:
                        st.success(result["message"])
                        st.session_state.login_mode = "login"
                        st.rerun()
                    else:
                        st.error(result["message"])
        
        # Botão para voltar para login
        st.markdown('<div class="auth-footer">', unsafe_allow_html=True)
        if st.button("Já tem uma conta? Voltar para o login", key="back_to_login_btn"):
            st.session_state.login_mode = "login"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    elif page_mode == "reset":
        # Recuperação de senha
        st.markdown('<p class="auth-subtitle">Recuperação de senha</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)  # Fim do cabeçalho
        
        st.write("Digite seu email abaixo para receber instruções de recuperação de senha.")
        
        # Formulário de recuperação
        with st.form("reset_form"):
            email = st.text_input("Email", placeholder="Seu email...", key="reset_email")
            
            reset_submitted = st.form_submit_button("Enviar link de recuperação", use_container_width=True)
            
            if reset_submitted:
                result = reset_password_simple(email)
                
                if result["success"]:
                    st.success(result["message"])
                else:
                    st.error(result["message"])
        
        # Botão para voltar para login
        if st.button("Voltar para o login", key="back_to_login_from_reset"):
            st.session_state.login_mode = "login"
            st.rerun()
    
    # Fechar container
    st.markdown('</div>', unsafe_allow_html=True)