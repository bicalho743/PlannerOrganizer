import streamlit as st
import json
import os
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Login com Verificação - Planner Organizer",
    page_icon="🔑",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Inicializar estado da sessão
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user = None

# Configurações do Firebase
firebase_config = {
    "apiKey": os.environ.get("FIREBASE_API_KEY", "AIzaSyDWb55-PRwdFkAgxoMd5-V_CVXvdP0FrpY"),
    "authDomain": "planner-organizer-68a23.firebaseapp.com",
    "projectId": "planner-organizer-68a23",
    "storageBucket": "planner-organizer-68a23.appspot.com",
    "messagingSenderId": "763383033284",
    "appId": "1:763383033284:web:5a5dc3b4d3f5bc63631ce7"
}

# CSS personalizado para estilização
st.markdown("""
<style>
    .gradient-heading {
        font-size: 48px;
        background: linear-gradient(45deg, #2193b0, #6dd5ed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 20px;
        font-weight: 700;
    }
    
    .login-box {
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        background-color: white;
    }
    
    .pricing-button {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100%;
        padding: 10px 15px;
        border-radius: 5px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s ease;
        border: none;
        margin-bottom: 10px;
        color: white;
    }
    
    .pricing-card {
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        background-color: white;
        position: relative;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    
    .pricing-card.highlight {
        border: 2px solid #2193b0;
    }
    
    .pricing-header {
        position: absolute;
        top: -10px;
        left: 50%;
        transform: translateX(-50%);
        background: linear-gradient(45deg, #2193b0, #6dd5ed);
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }
    
    .pricing-title {
        margin-top: 15px;
        font-size: 24px;
        font-weight: 600;
        color: #333;
        text-align: center;
    }
    
    .pricing-price {
        font-size: 36px;
        font-weight: 700;
        color: #2193b0;
        text-align: center;
        margin: 10px 0 5px;
    }
    
    .pricing-period {
        font-size: 14px;
        color: #666;
        text-align: center;
        margin-bottom: 20px;
    }
    
    .pricing-features {
        list-style-type: none;
        padding: 0;
        margin: 0 0 20px;
        flex-grow: 1;
    }
    
    .pricing-features li {
        padding: 8px 0;
        border-bottom: 1px solid #eee;
        font-size: 14px;
        position: relative;
        padding-left: 25px;
    }
    
    .pricing-features li:before {
        content: "✓";
        color: #2193b0;
        position: absolute;
        left: 0;
    }
    
    .pricing-button {
        background: linear-gradient(45deg, #2193b0, #6dd5ed);
        margin-top: auto;
        font-size: 16px;
    }
    
    .pricing-button:hover {
        opacity: 0.9;
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

# Verificar parâmetros de URL para autenticação
params = dict(st.query_params)
if "auth_success" in params and params["auth_success"] == "true":
    if "uid" in params and "email" in params:
        uid = params["uid"]
        email = params["email"]
        
        # Verificar se o email foi verificado (para logins com email/senha)
        # Manusear corretamente o valor que pode vir como string ou lista
        email_verified_param = params.get("email_verified", "false")
        if isinstance(email_verified_param, list):
            email_verified = email_verified_param[0] == "true"
        else:
            email_verified = email_verified_param == "true"
            
        provider = "email"  # Valor padrão
        
        # Verificar o provedor (mantemos apenas email)
        if "provider" in params:
            provider_param = params["provider"]
            if isinstance(provider_param, list):
                provider = provider_param[0]
            else:
                provider = provider_param
        
        # Salvar na sessão com informações adicionais
        st.session_state.authenticated = True
        st.session_state.user = {
            "uid": uid,
            "email": email,
            "email_verified": email_verified,
            "provider": provider,
            "login_time": datetime.now().isoformat()
        }

        # Limpar parâmetros
        st.query_params.clear()
        st.rerun()

# Javascript para Firebase Auth
firebase_js = f"""
// Configuração do Firebase
const firebaseConfig = {json.dumps(firebase_config)};

// Inicializar Firebase apenas uma vez
let firebaseInitialized = false;
let auth;

function initializeFirebase() {{
    if (!firebaseInitialized) {{
        firebase.initializeApp(firebaseConfig);
        auth = firebase.auth();
        firebaseInitialized = true;
        console.log("Firebase inicializado com sucesso");
    }}
}}

// Login com Email e Senha
function loginWithEmail(email, password) {{
    console.log("Iniciando login com email e senha...");
    initializeFirebase();
    
    auth.signInWithEmailAndPassword(email, password)
        .then((result) => {{
            console.log("Login com email bem-sucedido");
            const user = result.user;
            
            // Verificar se o email do usuário está verificado
            if (user.emailVerified) {{
                console.log("Email verificado, procedendo com o login");
                return user.getIdToken().then(token => {{
                    const url = new URL(window.location.href);
                    url.searchParams.set('auth_success', 'true');
                    url.searchParams.set('uid', user.uid);
                    url.searchParams.set('email', user.email);
                    url.searchParams.set('email_verified', 'true');
                    url.searchParams.set('provider', 'email');
                    
                    localStorage.setItem('firebase_user', JSON.stringify({{
                        uid: user.uid,
                        email: user.email,
                        emailVerified: true,
                        token: token,
                        provider: 'email'
                    }}));
                    
                    window.location.href = url.toString();
                }});
            }} else {{
                console.log("Email não verificado, enviando novo email de verificação");
                
                // Enviar novo email de verificação
                user.sendEmailVerification()
                    .then(() => {{
                        console.log("Novo email de verificação enviado");
                        alert("Seu email ainda não foi verificado. Uma nova mensagem de verificação foi enviada para " + 
                              email + ". Por favor, verifique seu email e tente fazer login novamente.");
                        
                        // Fazer logout do usuário
                        auth.signOut();
                    }})
                    .catch((error) => {{
                        console.error("Erro ao enviar novo email de verificação:", error);
                        alert("Seu email ainda não foi verificado, e houve um erro ao enviar uma nova verificação: " + 
                              error.message + ". Por favor, tente novamente mais tarde.");
                        
                        // Fazer logout do usuário
                        auth.signOut();
                    }});
            }}
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
            
            // Enviar email de verificação para o usuário
            user.sendEmailVerification()
                .then(() => {{
                    console.log("Email de verificação enviado com sucesso");
                    alert("Uma mensagem de verificação foi enviada para " + email + ". Por favor, verifique seu email antes de fazer login.");
                }})
                .catch((error) => {{
                    console.error("Erro ao enviar email de verificação:", error);
                    alert("Sua conta foi criada, mas houve um erro ao enviar o email de verificação: " + error.message);
                }});
            
            return user.getIdToken().then(token => {{
                const url = new URL(window.location.href);
                url.searchParams.set('auth_success', 'true');
                url.searchParams.set('uid', user.uid);
                url.searchParams.set('email', user.email);
                url.searchParams.set('email_verified', 'false');
                url.searchParams.set('provider', 'email');
                
                localStorage.setItem('firebase_user', JSON.stringify({{
                    uid: user.uid,
                    email: user.email,
                    emailVerified: false,
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
    
    // Configurações adicionais para recuperação de senha
    const actionCodeSettings = {{
        // URL de redirecionamento após recuperação
        url: window.location.origin + window.location.pathname,
        // Manipular código como código de recuperação de senha
        handleCodeInApp: false
    }};
    
    console.log("ActionCodeSettings:", actionCodeSettings);
    
    auth.sendPasswordResetEmail(email, actionCodeSettings)
        .then(() => {{
            console.log("Email de recuperação enviado com sucesso");
            alert("Um email de recuperação de senha foi enviado para " + email + ". Por favor, verifique sua caixa de entrada e siga as instruções para redefinir sua senha.");
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

// Reenviar email de verificação
function resendVerificationEmail() {{
    console.log("Reenviando email de verificação...");
    initializeFirebase();
    
    const user = auth.currentUser;
    if (user) {{
        user.sendEmailVerification()
            .then(() => {{
                console.log("Email de verificação reenviado com sucesso");
                alert("Um novo email de verificação foi enviado para " + user.email);
            }})
            .catch((error) => {{
                console.error("Erro ao reenviar email de verificação:", error);
                alert("Erro ao reenviar email de verificação: " + error.message);
            }});
    }} else {{
        console.error("Nenhum usuário autenticado para reenviar verificação");
        alert("Você precisa estar logado para reenviar o email de verificação");
    }}
}}
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
    
    # Verificar se o email está verificado
    if st.session_state.user.get('provider') == 'email' and not st.session_state.user.get('email_verified', False):
        st.warning("Seu email ainda não foi verificado. Por favor, verifique sua caixa de entrada e confirme seu email para acesso completo.")
        
        # Botão para reenviar email de verificação
        if st.button("Reenviar Email de Verificação", key="btn_reenviar_verificacao"):
            st.markdown("""
            <script>
            document.addEventListener('DOMContentLoaded', function() {
                if (typeof resendVerificationEmail === 'function') {
                    resendVerificationEmail();
                } else {
                    alert("Função de reenvio não disponível. Tente fazer login novamente.");
                }
            });
            </script>
            """, unsafe_allow_html=True)
    
    # Exibir informações do login
    st.info("Método de login: Email e Senha")
    
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
        # Login com email/senha
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        st.subheader("Login com Email e Senha")
        
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Senha", type="password", key="login_password")
            
            submit = st.form_submit_button("Entrar", use_container_width=True)
            
            if submit:
                if email and password:
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

# Executar aplicação
if __name__ == "__main__":
    main()