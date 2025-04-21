import streamlit as st
import os
import json
import requests
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Login - Planner Organizer",
    page_icon="🔑",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estilo personalizado
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
    .gradient-heading {
        background: linear-gradient(90deg, #007bff, #00c6ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
        text-align: center;
    }
    .pricing-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #ddd;
        height: 100%;
    }
    .pricing-card.highlight {
        border: 2px solid #007bff;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .pricing-header {
        background-color: #007bff;
        color: white;
        padding: 0.5rem;
        margin: -1.5rem -1.5rem 1rem -1.5rem;
        border-radius: 10px 10px 0 0;
        text-align: center;
    }
    .pricing-title {
        font-size: 1.25rem;
        font-weight: bold;
        text-align: center;
        color: #333;
    }
    .pricing-price {
        font-size: 1.75rem;
        font-weight: bold;
        text-align: center;
        color: #007bff;
        margin: 0.5rem 0;
    }
    .pricing-period {
        text-align: center;
        color: #666;
        margin-bottom: 1rem;
    }
    .pricing-features {
        margin: 1rem 0;
    }
    .pricing-button {
        background-color: #007bff;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        cursor: pointer;
        font-weight: bold;
        width: 100%;
        text-align: center;
        margin-top: 1rem;
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
    /* Botões estilizados para login social */
    .social-button-google {
        width: 100%;
        padding: 10px;
        margin-bottom: 10px;
        background-color: white;
        color: #444;
        border: 1px solid #ddd;
        border-radius: 5px;
        font-size: 16px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .social-button-facebook {
        width: 100%;
        padding: 10px;
        margin-bottom: 10px;
        background-color: #3b5998;
        color: white;
        border: none;
        border-radius: 5px;
        font-size: 16px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar variáveis de sessão
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user" not in st.session_state:
    st.session_state.user = None

if "auth_error" not in st.session_state:
    st.session_state.auth_error = None

# Carregar configuração do Firebase
firebase_config = {
    "apiKey": os.environ.get("FIREBASE_API_KEY", "AIzaSyDNvFRG_LcmnrQlvGzHx5_dR16vCUTp13I"),
    "authDomain": "planner-organizer-68a23.firebaseapp.com",
    "projectId": "planner-organizer-68a23",
    "storageBucket": "planner-organizer-68a23.appspot.com",
    "messagingSenderId": "763383033284",
    "appId": "1:763383033284:web:5a5dc3b4d3f5bc63631ce7"
}

# Verificar parâmetros de URL para autenticação
params = dict(st.query_params)
if "auth_success" in params and params["auth_success"] == "true":
    if "uid" in params and "email" in params:
        uid = params["uid"]
        email = params["email"]

        # Salvar na sessão
        st.session_state.authenticated = True
        st.session_state.user = {
            "uid": uid,
            "email": email,
            "login_time": datetime.now().isoformat()
        }

        # Limpar parâmetros
        st.query_params.clear()
        st.rerun()

# Funções de autenticação para integração com backend
def register_user_with_backend(uid, email, name=None):
    """Registra o usuário no backend após autenticação com Firebase"""
    try:
        # Faz requisição para o backend
        response = requests.post(
            "http://localhost:8000/api/users/register",
            json={
                "uid": uid,
                "email": email,
                "name": name or email.split('@')[0]
            }
        )
        return response.json()
    except Exception as e:
        st.error(f"Erro ao registrar usuário no backend: {e}")
        return None

def verify_admin_credentials(email, password):
    """Modo administrador para testes (apenas para desenvolvimento)"""
    if email.lower() == "admin" and password == "admin":
        return {
            "uid": "admin-user",
            "email": "admin@example.com",
            "name": "Administrador",
            "demo": True
        }
    return None

# Javascript para Firebase Auth
firebase_js = f"""
// Configuração do Firebase
const firebaseConfig = {json.dumps(firebase_config)};

// Inicializar Firebase apenas uma vez
let firebaseInitialized = false;
let auth;
let googleProvider;
let facebookProvider;

function initializeFirebase() {{
    if (!firebaseInitialized) {{
        firebase.initializeApp(firebaseConfig);
        auth = firebase.auth();
        googleProvider = new firebase.auth.GoogleAuthProvider();
        facebookProvider = new firebase.auth.FacebookAuthProvider();
        firebaseInitialized = true;
        console.log("Firebase inicializado com sucesso");
    }}
}}

// Login com Google
function loginWithGoogle() {{
    console.log("Iniciando login com Google...");
    initializeFirebase();
    
    // Configurar parâmetros adicionais
    googleProvider.setCustomParameters({{
        'prompt': 'select_account'
    }});
    
    auth.signInWithPopup(googleProvider)
        .then((result) => {{
            console.log("Login com Google bem-sucedido");
            const user = result.user;
            
            // Enviar para o backend
            return user.getIdToken().then(token => {{
                const url = new URL(window.location.href);
                url.searchParams.set('auth_success', 'true');
                url.searchParams.set('uid', user.uid);
                url.searchParams.set('email', user.email);
                
                // Salvar no localStorage
                localStorage.setItem('firebase_user', JSON.stringify({{
                    uid: user.uid,
                    email: user.email,
                    token: token,
                    provider: 'google'
                }}));
                
                // Redirecionar
                window.location.href = url.toString();
            }});
        }})
        .catch((error) => {{
            console.error("Erro no login com Google:", error);
            if (error.code === 'auth/popup-blocked') {{
                alert("O pop-up foi bloqueado pelo navegador. Por favor, permita pop-ups para este site e tente novamente.");
            }} else {{
                alert("Erro no login com Google: " + error.message);
            }}
        }});
}}

// Login com Facebook
function loginWithFacebook() {{
    console.log("Iniciando login com Facebook...");
    initializeFirebase();
    
    auth.signInWithPopup(facebookProvider)
        .then((result) => {{
            console.log("Login com Facebook bem-sucedido");
            const user = result.user;
            
            return user.getIdToken().then(token => {{
                const url = new URL(window.location.href);
                url.searchParams.set('auth_success', 'true');
                url.searchParams.set('uid', user.uid);
                url.searchParams.set('email', user.email);
                
                localStorage.setItem('firebase_user', JSON.stringify({{
                    uid: user.uid,
                    email: user.email,
                    token: token,
                    provider: 'facebook'
                }}));
                
                window.location.href = url.toString();
            }});
        }})
        .catch((error) => {{
            console.error("Erro no login com Facebook:", error);
            if (error.code === 'auth/popup-blocked') {{
                alert("O pop-up foi bloqueado pelo navegador. Por favor, permita pop-ups para este site e tente novamente.");
            }} else {{
                alert("Erro no login com Facebook: " + error.message);
            }}
        }});
}}

// Login com Email e Senha
function loginWithEmail(email, password) {{
    console.log("Iniciando login com email e senha...");
    initializeFirebase();
    
    auth.signInWithEmailAndPassword(email, password)
        .then((result) => {{
            console.log("Login com email bem-sucedido");
            const user = result.user;
            
            return user.getIdToken().then(token => {{
                const url = new URL(window.location.href);
                url.searchParams.set('auth_success', 'true');
                url.searchParams.set('uid', user.uid);
                url.searchParams.set('email', user.email);
                
                localStorage.setItem('firebase_user', JSON.stringify({{
                    uid: user.uid,
                    email: user.email,
                    token: token,
                    provider: 'email'
                }}));
                
                window.location.href = url.toString();
            }});
        }})
        .catch((error) => {{
            console.error("Erro no login com email:", error);
            alert("Erro no login: " + error.message);
        }});
}}

// Criar conta com Email e Senha
function createAccount(email, password) {{
    console.log("Criando conta com email e senha...");
    initializeFirebase();
    
    auth.createUserWithEmailAndPassword(email, password)
        .then((result) => {{
            console.log("Conta criada com sucesso");
            const user = result.user;
            
            return user.getIdToken().then(token => {{
                const url = new URL(window.location.href);
                url.searchParams.set('auth_success', 'true');
                url.searchParams.set('uid', user.uid);
                url.searchParams.set('email', user.email);
                
                localStorage.setItem('firebase_user', JSON.stringify({{
                    uid: user.uid,
                    email: user.email,
                    token: token,
                    provider: 'email'
                }}));
                
                window.location.href = url.toString();
            }});
        }})
        .catch((error) => {{
            console.error("Erro ao criar conta:", error);
            alert("Erro ao criar conta: " + error.message);
        }});
}}

// Recuperar senha
function resetPassword(email) {{
    console.log("Enviando email de recuperação...");
    initializeFirebase();
    
    auth.sendPasswordResetEmail(email)
        .then(() => {{
            console.log("Email de recuperação enviado com sucesso");
            alert("Um email de recuperação de senha foi enviado para " + email);
        }})
        .catch((error) => {{
            console.error("Erro ao enviar email de recuperação:", error);
            alert("Erro ao enviar email de recuperação: " + error.message);
        }});
}}

// Encerrar sessão
function signOut() {{
    console.log("Encerrando sessão...");
    initializeFirebase();
    
    auth.signOut().then(() => {{
        console.log("Logout realizado com sucesso");
        localStorage.removeItem('firebase_user');
        
        // Redirecionar para a página de login
        window.location.href = window.location.pathname;
    }}).catch((error) => {{
        console.error("Erro ao encerrar sessão:", error);
    }});
}}

// Configurar event listeners quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {{
    console.log("Configurando event listeners para autenticação...");
    
    // Botão de login com Google
    const googleBtn = document.getElementById('googleLoginBtn');
    if (googleBtn) {{
        googleBtn.addEventListener('click', function(e) {{
            e.preventDefault();
            loginWithGoogle();
        }});
    }}
    
    // Botão de login com Facebook
    const facebookBtn = document.getElementById('facebookLoginBtn');
    if (facebookBtn) {{
        facebookBtn.addEventListener('click', function(e) {{
            e.preventDefault();
            loginWithFacebook();
        }});
    }}
}});
"""

# Função principal
def main():
    # Área de logo e título
    st.markdown('<div style="text-align: center;"><h1 class="gradient-heading">Planner Organizer</h1></div>', unsafe_allow_html=True)
    
    # Verificar se o usuário está autenticado
    if st.session_state.authenticated:
        mostrar_area_logada()
    else:
        mostrar_login()

# Exibir área de usuário logado
def mostrar_area_logada():
    st.success(f"Login realizado com sucesso como {st.session_state.user.get('email')}")
    
    # Botão para acessar o sistema
    if st.button("Acessar o Sistema", key="btn_acessar_sistema"):
        st.switch_page("app.py")
    
    # Botão para sair
    if st.button("Sair", key="btn_logout"):
        # Limpar sessão
        st.session_state.authenticated = False
        st.session_state.user = None
        
        # Limpar localStorage
        st.markdown("""
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Limpar dados do usuário
            localStorage.removeItem('firebase_user');
            
            // Chamar função de logout
            if (typeof signOut === 'function') {
                signOut();
            }
        });
        </script>
        """, unsafe_allow_html=True)
        
        st.rerun()
    
    # Mostrar detalhes do usuário
    with st.expander("Detalhes do Usuário"):
        st.json(st.session_state.user)
    
    # Verificar conexão com API
    with st.expander("Diagnóstico de Conexão"):
        try:
            response = requests.get("http://localhost:8000/status")
            if response.status_code == 200:
                st.success(f"API conectada! Status: {response.json().get('status', 'Online')}")
            else:
                st.warning(f"API está respondendo com status {response.status_code}")
        except Exception as e:
            st.error(f"Erro ao conectar com a API: {e}")

# Exibir tela de login
def mostrar_login():
    # Carregar bibliotecas do Firebase
    st.markdown("""
    <script src="https://www.gstatic.com/firebasejs/8.10.1/firebase-app.js"></script>
    <script src="https://www.gstatic.com/firebasejs/8.10.1/firebase-auth.js"></script>
    """, unsafe_allow_html=True)
    
    # Adicionar script de autenticação
    st.markdown(f"<script>{firebase_js}</script>", unsafe_allow_html=True)
    
    # Exibir abas de login, cadastro e recuperação
    tab1, tab2, tab3 = st.tabs(["Login", "Criar Conta", "Recuperar Senha"])
    
    with tab1:
        # Login com redes sociais
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        st.subheader("Login com Redes Sociais")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <button id="googleLoginBtn" class="social-button-google">
                <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" 
                     style="width: 18px; height: 18px; margin-right: 10px;">
                Login com Google
            </button>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <button id="facebookLoginBtn" class="social-button-facebook">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="white" 
                     style="margin-right: 10px;">
                    <path d="M12 0c-6.627 0-12 5.373-12 12s5.373 12 12 12 12-5.373 12-12-5.373-12-12-12zm3 8h-1.35c-.538 0-.65.221-.65.778v1.222h2l-.209 2h-1.791v7h-3v-7h-2v-2h2v-2.308c0-1.769.931-2.692 3.029-2.692h1.971v3z"/>
                </svg>
                Login com Facebook
            </button>
            """, unsafe_allow_html=True)
        
        # Separador
        st.markdown("<div style='text-align: center; margin: 20px 0;'>ou</div>", unsafe_allow_html=True)
        
        # Login com email/senha
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Senha", type="password", key="login_password")
            
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("Entrar", use_container_width=True)
            with col2:
                demo_mode = st.form_submit_button("Modo Demo", use_container_width=True)
            
            if submit:
                if email and password:
                    # Verificar modo administrador
                    admin_user = verify_admin_credentials(email, password)
                    if admin_user:
                        st.session_state.authenticated = True
                        st.session_state.user = admin_user
                        st.success("Login de administrador realizado com sucesso!")
                        st.rerun()
                    else:
                        # Adicionar script para login com Firebase
                        st.markdown(f"""
                        <script>
                        document.addEventListener('DOMContentLoaded', function() {{
                            loginWithEmail("{email}", "{password}");
                        }});
                        </script>
                        """, unsafe_allow_html=True)
                else:
                    st.error("Por favor, preencha email e senha.")
            
            if demo_mode:
                st.session_state.authenticated = True
                st.session_state.user = {
                    "uid": "demo-user",
                    "email": "demo@example.com",
                    "name": "Usuário Demo",
                    "demo": True
                }
                st.success("Modo de demonstração ativado!")
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with tab2:
        # Formulário de criação de conta
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        st.subheader("Criar Nova Conta")
        
        with st.form("signup_form"):
            name = st.text_input("Nome", key="signup_name")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Senha", type="password", key="signup_password")
            confirm_password = st.text_input("Confirmar Senha", type="password", key="signup_confirm")
            
            submit = st.form_submit_button("Criar Conta", use_container_width=True)
            
            if submit:
                if not email or not password:
                    st.error("Email e senha são obrigatórios.")
                elif password != confirm_password:
                    st.error("As senhas não correspondem.")
                elif len(password) < 6:
                    st.error("A senha deve ter pelo menos 6 caracteres.")
                else:
                    # Adicionar script para criar conta com Firebase
                    st.markdown(f"""
                    <script>
                    document.addEventListener('DOMContentLoaded', function() {{
                        createAccount("{email}", "{password}");
                    }});
                    </script>
                    """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with tab3:
        # Formulário de recuperação de senha
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        st.subheader("Recuperar Senha")
        
        with st.form("recovery_form"):
            email = st.text_input("Email", key="recovery_email")
            
            submit = st.form_submit_button("Enviar Email de Recuperação", use_container_width=True)
            
            if submit:
                if email:
                    # Adicionar script para recuperar senha
                    st.markdown(f"""
                    <script>
                    document.addEventListener('DOMContentLoaded', function() {{
                        resetPassword("{email}");
                    }});
                    </script>
                    """, unsafe_allow_html=True)
                else:
                    st.error("Por favor, informe seu email.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Exibir planos de preço
    st.markdown("<h2 style='text-align: center; margin: 2rem 0 1rem;'>Planos e Preços</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="pricing-card">
            <h3 class="pricing-title">Mensal</h3>
            <div class="pricing-price">R$ 9,70</div>
            <div class="pricing-period">por mês</div>
            <ul class="pricing-features">
                <li>Acesso a todas as funcionalidades</li>
                <li>Suporte via email</li>
                <li>7 dias de teste grátis</li>
                <li>Cancele quando quiser</li>
            </ul>
            <button class="pricing-button">Assinar Plano</button>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="pricing-card highlight">
            <div class="pricing-header">
                <span>Mais Popular</span>
            </div>
            <h3 class="pricing-title">Anual</h3>
            <div class="pricing-price">R$ 97,00</div>
            <div class="pricing-period">por ano (economize 17%)</div>
            <ul class="pricing-features">
                <li>Acesso a todas as funcionalidades</li>
                <li>Suporte prioritário</li>
                <li>7 dias de teste grátis</li>
                <li>Cancele quando quiser</li>
                <li>Economia de 2 meses no ano</li>
            </ul>
            <button class="pricing-button">Assinar Plano</button>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="pricing-card">
            <h3 class="pricing-title">Vitalício</h3>
            <div class="pricing-price">R$ 247,00</div>
            <div class="pricing-period">pagamento único</div>
            <ul class="pricing-features">
                <li>Acesso a todas as funcionalidades</li>
                <li>Suporte premium</li>
                <li>Acesso vitalício sem mensalidades</li>
                <li>Acesso a novas funcionalidades</li>
                <li>Prioridade nas atualizações</li>
            </ul>
            <button class="pricing-button">Comprar Acesso</button>
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