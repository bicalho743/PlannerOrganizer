"""
Página de login moderna com recursos avançados de autenticação
"""
import os
import logging

# Tentar importar componentes de autenticação, mas lidar graciosamente com erros
try:
    import streamlit as st
    from utils.auth_utils import login_user, reset_password, register_user
    from utils.session_manager import is_authenticated, initialize_session_state
    from utils.auth_audit import log_auth_event
    from utils.auth_security import protect_session
    
    auth_components_available = True
except ImportError as e:
    print(f"Erro ao importar componentes de autenticação: {str(e)}")
    auth_components_available = False

# Configurar logging
logger = logging.getLogger(__name__)

# Verificar se temos os componentes de autenticação disponíveis
if auth_components_available:
    # Inicializar estado da sessão
    initialize_session_state()
    
    # Verificar proteções de segurança
    protect_session()
else:
    # Não temos os componentes de autenticação
    print("Componentes de autenticação não disponíveis. Funcionalidades de login serão limitadas.")


def show():
    """Função principal para mostrar a página de login moderna"""
    
    # Verificar se os componentes de autenticação estão disponíveis
    if not auth_components_available:
        # Mensagem básica caso não tenha os componentes
        import streamlit as st
        st.title("Sistema de Login")
        st.error("Os componentes de autenticação não estão disponíveis. Por favor, instale as dependências necessárias.")
        st.code("pip install streamlit firebase-admin requests", language="bash")
        return
    
    # Verificar se já está autenticado
    if is_authenticated():
        st.warning("Você já está autenticado.")
        st.session_state.login_page = "login"
        st.rerun()
    
    # CSS personalizado para a tela de login
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
    
    body {
        font-family: 'Poppins', sans-serif;
        background-color: #f8f9fa;
    }
    
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
    
    .google-button:hover {
        background-color: #f8f9fa;
        transform: translateY(-2px);
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
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
    
    .auth-form-field {
        margin-bottom: 1.25rem;
    }
    
    .auth-label {
        display: block;
        margin-bottom: 0.5rem;
        font-weight: 500;
        color: #2d3748;
        font-size: 0.9rem;
    }
    
    .auth-input {
        width: 100%;
        padding: 0.75rem 1rem;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        font-size: 1rem;
        transition: all 0.2s ease;
    }
    
    .auth-input:focus {
        border-color: #3182ce;
        box-shadow: 0 0 0 2px rgba(49,130,206,0.2);
    }
    
    .auth-submit {
        width: 100%;
        padding: 0.75rem 1rem;
        background: linear-gradient(90deg, #1E88E5, #0063CC);
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
        margin-top: 1rem;
    }
    
    .auth-submit:hover {
        background: linear-gradient(90deg, #0063CC, #004C99);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,99,204,0.3);
    }
    
    .auth-footer {
        margin-top: 1.5rem;
        text-align: center;
        font-size: 0.9rem;
    }
    
    .auth-link {
        color: #2b6cb0;
        font-weight: 500;
        text-decoration: none;
        cursor: pointer;
    }
    
    .auth-link:hover {
        text-decoration: underline;
    }
    
    .auth-extra {
        margin-top: 1.5rem;
        display: flex;
        justify-content: space-between;
    }
    
    .auth-checkbox {
        display: flex;
        align-items: center;
    }
    
    .auth-checkbox input {
        margin-right: 0.5rem;
    }
    
    .auth-checkbox label {
        font-size: 0.85rem;
        color: #4a5568;
    }
    
    .auth-help {
        font-size: 0.85rem;
        color: #718096;
    }
    
    .auth-error {
        background-color: #fff5f5;
        color: #c53030;
        padding: 0.75rem 1rem;
        border-radius: 6px;
        margin-bottom: 1rem;
        font-size: 0.9rem;
        border-left: 4px solid #c53030;
    }
    
    .auth-success {
        background-color: #f0fff4;
        color: #2f855a;
        padding: 0.75rem 1rem;
        border-radius: 6px;
        margin-bottom: 1rem;
        font-size: 0.9rem;
        border-left: 4px solid #2f855a;
    }
    
    .auth-note {
        font-size: 0.85rem;
        color: #718096;
        text-align: center;
        margin-top: 1rem;
    }
    
    /* Responsive adjustments */
    @media screen and (max-width: 768px) {
        .auth-container {
            padding: 1.5rem;
            margin: 1rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Container principal centralizado
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    
    # Cabeçalho
    st.markdown('<div class="auth-header">', unsafe_allow_html=True)
    st.markdown('<h1 class="auth-title">Planner Organizer</h1>', unsafe_allow_html=True)
    
    # Verificar o modo da página
    page_mode = st.session_state.get("login_mode", "login")
    
    if page_mode == "login":
        # Subtítulo para login
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
        with st.form("login_form_modern"):
            email = st.text_input("Email", placeholder="Seu email...", key="login_email")
            password = st.text_input("Senha", placeholder="Sua senha...", type="password", key="login_password")
            
            # Remember me e Esqueceu sua senha
            st.markdown('<div class="auth-extra">', unsafe_allow_html=True)
            st.markdown('''
            <div class="auth-checkbox">
                <input type="checkbox" id="remember_me">
                <label for="remember_me">Lembrar de mim</label>
            </div>
            ''', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Botão de login
            login_submitted = st.form_submit_button("Entrar na minha conta", use_container_width=True)
            
            if login_submitted:
                # Tentar login
                result = login_user(email, password)
                
                if result["success"]:
                    st.success(result["message"])
                    # Redirecionar para a página principal
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error(result["message"])
        
        # Link para recuperar senha
        st.markdown('<div class="auth-footer">', unsafe_allow_html=True)
        if st.button("Esqueceu sua senha?", key="forgot_password_btn"):
            # Mudar para modo de recuperação de senha
            st.session_state.login_mode = "reset"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Botão para criar conta
        st.markdown('<div class="auth-footer">', unsafe_allow_html=True)
        st.markdown('Não tem uma conta?', unsafe_allow_html=True)
        if st.button("Criar nova conta", key="create_account_btn"):
            # Mudar para modo de criação de conta
            st.session_state.login_mode = "register"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Nota de demo
        st.markdown('''
        <div class="auth-note">
            Para demonstração, use: admin / admin
        </div>
        ''', unsafe_allow_html=True)
        
    elif page_mode == "register":
        # Subtítulo para registro
        st.markdown('<p class="auth-subtitle">Crie sua conta para começar</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)  # Fim do cabeçalho
        
        # Formulário de registro
        with st.form("register_form"):
            name = st.text_input("Nome completo", placeholder="Seu nome...", key="register_name")
            email = st.text_input("Email", placeholder="Seu email...", key="register_email")
            password = st.text_input("Senha", placeholder="Crie uma senha...", type="password", key="register_password")
            confirm_password = st.text_input("Confirmar senha", placeholder="Repita sua senha...", type="password", key="register_confirm")
            
            # Termos e condições
            st.markdown('''
            <div class="auth-checkbox" style="margin: 1rem 0;">
                <input type="checkbox" id="terms" checked>
                <label for="terms">Eu concordo com os <a href="#" class="auth-link">Termos e Condições</a></label>
            </div>
            ''', unsafe_allow_html=True)
            
            # Botão de registro
            register_submitted = st.form_submit_button("Criar minha conta", use_container_width=True)
            
            if register_submitted:
                # Verificar senhas
                if password != confirm_password:
                    st.error("As senhas não coincidem")
                else:
                    # Tentar registro
                    result = register_user(email, password, name)
                    
                    if result["success"]:
                        st.success(result["message"])
                        # Mudar para o modo de login
                        st.session_state.login_mode = "login"
                        st.rerun()
                    else:
                        st.error(result["message"])
        
        # Botão para voltar para login
        st.markdown('<div class="auth-footer">', unsafe_allow_html=True)
        st.markdown('Já tem uma conta?', unsafe_allow_html=True)
        if st.button("Voltar para o login", key="back_to_login_btn"):
            # Mudar para modo de login
            st.session_state.login_mode = "login"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    elif page_mode == "reset":
        # Subtítulo para recuperação de senha
        st.markdown('<p class="auth-subtitle">Recupere sua senha</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)  # Fim do cabeçalho
        
        # Texto explicativo
        st.markdown('''
        <p style="margin-bottom: 1.5rem;">
            Digite seu email abaixo e enviaremos um link para redefinir sua senha.
        </p>
        ''', unsafe_allow_html=True)
        
        # Formulário de recuperação
        with st.form("reset_form"):
            email = st.text_input("Email", placeholder="Seu email...", key="reset_email")
            
            # Botão de envio
            reset_submitted = st.form_submit_button("Enviar link de recuperação", use_container_width=True)
            
            if reset_submitted:
                # Tentar enviar email de recuperação
                result = reset_password(email)
                
                if result["success"]:
                    st.success(result["message"])
                else:
                    st.error(result["message"])
        
        # Botão para voltar para login
        st.markdown('<div class="auth-footer">', unsafe_allow_html=True)
        if st.button("Voltar para o login", key="back_to_login_from_reset"):
            # Mudar para modo de login
            st.session_state.login_mode = "login"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Opção para pular login em ambiente de desenvolvimento (apenas para devs)
    st.markdown('''
    <div style="position: fixed; bottom: 10px; right: 10px; z-index: 999;">
        <details style="background: transparent; border: none; color: #BDBDBD; font-size: 0.7rem;">
            <summary style="cursor: pointer; outline: none;">Dev</summary>
            <div style="padding: 10px; background: white; border-radius: 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-top: 5px;">
                <p style="margin: 0 0 10px 0; font-size: 0.8rem;">Acesso para desenvolvedores</p>
                <button id="dev-login-button" style="background: #E0E0E0; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-size: 0.8rem;">Pular login</button>
            </div>
        </details>
    </div>
    ''', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col3:
        if st.button("Acesso Dev", key="dev_login_access", use_container_width=True):
            # Registrar evento de login de desenvolvedor
            log_auth_event(
                "login", 
                user_email="dev@example.com",
                success=True,
                details={"method": "dev_access"}
            )
            
            # Definir usuário desenvolvedor
            st.session_state.user = {
                "email": "dev@example.com",
                "displayName": "Desenvolvedor",
                "dev_account": True
            }
            st.session_state.authenticated = True
            st.rerun()
    
    # Fechar container
    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    show()