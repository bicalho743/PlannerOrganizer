"""
Página de login usando o Firebase Authentication integrado com Streamlit
"""
import streamlit as st
import requests
from streamlit_cookies_manager import CookieManager
from utils.firebase_auth_streamlit import firebase_auth, require_auth

# Configuração da página
st.set_page_config(
    page_title="Login - Planner Organizer",
    page_icon="🔒",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estilos CSS
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .block-container {
        max-width: 800px;
        padding: 1rem;
        margin-top: 2rem;
    }
    .login-box {
        background-color: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .social-button-google {
        background-color: #4285F4;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        cursor: pointer;
        width: 100%;
        font-weight: bold;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .social-button-facebook {
        background-color: #3b5998;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        cursor: pointer;
        width: 100%;
        font-weight: bold;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .divider {
        display: flex;
        align-items: center;
        text-align: center;
        margin: 1rem 0;
    }
    .divider::before, .divider::after {
        content: '';
        flex: 1;
        border-bottom: 1px solid #ddd;
    }
    .divider span {
        padding: 0 10px;
        color: #777;
    }
    .error-msg {
        background-color: #f8d7da;
        color: #721c24;
        padding: 0.75rem 1.25rem;
        border-radius: 0.25rem;
        margin-bottom: 1rem;
    }
    .success-msg {
        background-color: #d4edda;
        color: #155724;
        padding: 0.75rem 1.25rem;
        border-radius: 0.25rem;
        margin-bottom: 1rem;
    }
    .gradient-heading {
        background: linear-gradient(90deg, #007bff, #00c6ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
        text-align: center;
    }
    .form-group {
        margin-bottom: 1rem;
    }
    .form-control {
        width: 100%;
        padding: 0.5rem;
        border: 1px solid #ddd;
        border-radius: 4px;
    }
    .btn-primary {
        background-color: #007bff;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        cursor: pointer;
        width: 100%;
    }
    .logo-container {
        text-align: center;
        margin-bottom: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #e9ecef;
        padding: 10px 20px;
        border-radius: 4px 4px 0 0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #007bff;
        color: white;
    }
    button[data-testid="baseButton-header"] {
        background-color: #007bff;
        color: white;
    }
    button[data-testid="baseButton-header"]:hover {
        background-color: #0069d9;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar gerenciador de cookies se ainda não existir
if 'cookie_manager' not in st.session_state:
    st.session_state.cookie_manager = CookieManager()

# Função principal
def main():
    # Exibir logo e título
    st.markdown('<div class="logo-container"><h1 class="gradient-heading">Planner Organizer</h1></div>', unsafe_allow_html=True)
    
    # Verificar se o usuário já está autenticado
    if firebase_auth.is_authenticated():
        exibir_area_logada()
    else:
        exibir_login()
    
    # Processar callbacks de autenticação
    if firebase_auth.handle_auth_callback():
        st.rerun()

# Função para exibir quando o usuário já está logado
def exibir_area_logada():
    usuario = firebase_auth.get_current_user()
    nome = usuario.get('nome') or usuario.get('email', '').split('@')[0]
    
    st.markdown(f"""
    <div class="login-box">
        <h2>Bem-vindo(a), {nome}!</h2>
        <p>Você está conectado com o email: <strong>{usuario.get('email')}</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Verificar a conexão com a API
    try:
        response = requests.get("http://localhost:8000/status")
        if response.status_code == 200:
            st.success("API conectada! Status: Online")
        else:
            st.warning(f"API está respondendo com status {response.status_code}")
    except Exception as e:
        st.error(f"Erro ao conectar com a API: {e}")
    
    # Botão para ir para o aplicativo principal
    if st.button("Acessar o Sistema", key="acessar_sistema"):
        st.success("Redirecionando para o sistema...")
        st.switch_page("app.py")
    
    # Botão para sair
    if st.button("Sair", key="logout"):
        firebase_auth.sign_out()
        st.rerun()

# Função para exibir a página de login
def exibir_login():
    with st.container():
        # Mostrar erros de login
        if st.session_state.get('login_error'):
            error = st.session_state.get('login_error')
            st.error(f"Erro de autenticação: {error.get('message')}")
            # Limpar o erro após exibi-lo
            st.session_state['login_error'] = None
        
        # Abas de login/cadastro
        tab1, tab2, tab3 = st.tabs(["Login", "Criar Conta", "Recuperar Senha"])
        
        with tab1:
            st.markdown('<div class="login-box">', unsafe_allow_html=True)
            
            # Login com redes sociais
            st.subheader("Login com Redes Sociais")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Login com Google", key="google_login"):
                    firebase_auth.login_with_google()
            
            with col2:
                if st.button("Login com Facebook", key="facebook_login"):
                    firebase_auth.login_with_facebook()
                    
            # Separador
            st.markdown('<div class="divider"><span>ou</span></div>', unsafe_allow_html=True)
            
            # Login com email/senha
            st.subheader("Login com Email")
            
            with st.form("login_form"):
                email = st.text_input("Email", key="login_email")
                senha = st.text_input("Senha", type="password", key="login_senha")
                
                submit_login = st.form_submit_button("Entrar")
                
                if submit_login and email and senha:
                    firebase_auth.login_with_email(email, senha)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
        with tab2:
            st.markdown('<div class="login-box">', unsafe_allow_html=True)
            
            st.subheader("Criar Nova Conta")
            
            with st.form("signup_form"):
                nome = st.text_input("Nome", key="signup_nome")
                email = st.text_input("Email", key="signup_email")
                senha = st.text_input("Senha", type="password", key="signup_senha")
                confirma_senha = st.text_input("Confirmar Senha", type="password", key="signup_confirma")
                
                submit_signup = st.form_submit_button("Criar Conta")
                
                if submit_signup:
                    if not email or not senha:
                        st.error("Email e senha são obrigatórios")
                    elif senha != confirma_senha:
                        st.error("As senhas não coincidem")
                    elif len(senha) < 6:
                        st.error("A senha deve ter pelo menos 6 caracteres")
                    else:
                        firebase_auth.create_account(email, senha)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
        with tab3:
            st.markdown('<div class="login-box">', unsafe_allow_html=True)
            
            st.subheader("Recuperar Senha")
            
            # Mensagem de sucesso para reset de senha
            if st.session_state.get('auth_status') == 'password_reset':
                email = st.session_state.get('password_reset_email')
                st.success(f"Email de recuperação enviado para {email}. Verifique sua caixa de entrada.")
                st.session_state['auth_status'] = 'signed_out'
            
            with st.form("reset_form"):
                email = st.text_input("Informe seu Email", key="reset_email")
                
                submit_reset = st.form_submit_button("Enviar Email de Recuperação")
                
                if submit_reset and email:
                    firebase_auth.reset_password(email)
                    # Mensagem de feedback será exibida pelo callback após o sucesso
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Área de planos
    st.markdown("""
    <div style="margin-top: 2rem;">
        <h2 style="text-align: center; margin-bottom: 1rem;">Escolha o plano ideal para você</h2>
        <p style="text-align: center; margin-bottom: 2rem;">Organize suas propostas, atividades e negócios com o Planner Organizer</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Exibir planos
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="padding: 1.5rem; border-radius: 10px; border: 1px solid #ddd; height: 100%;">
            <h3 style="text-align: center; color: #333;">Mensal</h3>
            <h2 style="text-align: center; color: #007bff; margin: 1rem 0;">R$ 9,70</h2>
            <p style="text-align: center; color: #666;">por mês</p>
            <ul style="margin: 1rem 0; padding-left: 1.5rem;">
                <li>Acesso a todas as funcionalidades</li>
                <li>Suporte via email</li>
                <li>7 dias de teste grátis</li>
                <li>Cancele quando quiser</li>
            </ul>
            <div style="text-align: center; margin-top: 1.5rem;">
                <button style="background-color: #007bff; color: white; border: none; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer;">Assinar Plano</button>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="padding: 1.5rem; border-radius: 10px; border: 2px solid #007bff; height: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <div style="text-align: center; background-color: #007bff; color: white; padding: 0.5rem; margin: -1.5rem -1.5rem 1rem -1.5rem; border-radius: 10px 10px 0 0;">
                <span>Mais Popular</span>
            </div>
            <h3 style="text-align: center; color: #333;">Anual</h3>
            <h2 style="text-align: center; color: #007bff; margin: 1rem 0;">R$ 97,00</h2>
            <p style="text-align: center; color: #666;">por ano (economize 17%)</p>
            <ul style="margin: 1rem 0; padding-left: 1.5rem;">
                <li>Acesso a todas as funcionalidades</li>
                <li>Suporte prioritário</li>
                <li>7 dias de teste grátis</li>
                <li>Cancele quando quiser</li>
                <li>Economia de 2 meses no ano</li>
            </ul>
            <div style="text-align: center; margin-top: 1.5rem;">
                <button style="background-color: #007bff; color: white; border: none; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer; font-weight: bold;">Assinar Plano</button>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="padding: 1.5rem; border-radius: 10px; border: 1px solid #ddd; height: 100%;">
            <h3 style="text-align: center; color: #333;">Vitalício</h3>
            <h2 style="text-align: center; color: #007bff; margin: 1rem 0;">R$ 247,00</h2>
            <p style="text-align: center; color: #666;">pagamento único</p>
            <ul style="margin: 1rem 0; padding-left: 1.5rem;">
                <li>Acesso a todas as funcionalidades</li>
                <li>Suporte premium</li>
                <li>Acesso vitalício sem mensalidades</li>
                <li>Acesso a novas funcionalidades</li>
                <li>Prioridade nas atualizações</li>
            </ul>
            <div style="text-align: center; margin-top: 1.5rem;">
                <button style="background-color: #007bff; color: white; border: none; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer;">Comprar Acesso</button>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Rodapé
    st.markdown("""
    <div style="margin-top: 3rem; text-align: center; color: #666; font-size: 0.8rem;">
        <p>© 2025 Planner Organizer. Todos os direitos reservados.</p>
        <p>Dúvidas? Entre em contato: contato@plannerorganizer.com.br</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()