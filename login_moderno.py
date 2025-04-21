"""
Login com Firebase Auth usando a API moderna (v9)
Esta implementação inclui:
- Login com email/senha
- Criação de conta
- Verificação de email
- Recuperação de senha
"""
import streamlit as st
import os
import json
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Login - Planner Organizer",
    page_icon="🔒",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Inicializar sessão
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user" not in st.session_state:
    st.session_state.user = None

# Estilo CSS
st.markdown("""
<style>
    .main-title {
        text-align: center;
        color: #2557D6;
        margin-bottom: 1rem;
    }
    
    .login-box {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    
    .btn-primary {
        background-color: #2557D6;
        color: white;
        padding: 10px 15px;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        width: 100%;
    }
    
    .btn-secondary {
        background-color: #6c757d;
        color: white;
        padding: 10px 15px;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        width: 100%;
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

# Configuração do Firebase
firebase_config = {
    "apiKey": os.environ.get("FIREBASE_API_KEY", st.secrets.get("FIREBASE_API_KEY", "")),
    "authDomain": "planner-organizer-68a23.firebaseapp.com",
    "projectId": "planner-organizer-68a23",
    "storageBucket": "planner-organizer-68a23.appspot.com", 
    "messagingSenderId": "763383033284",
    "appId": "1:763383033284:web:5a5dc3b4d3f5bc63631ce7"
}

# Verificar parâmetros de autenticação na URL
query_params = st.query_params.to_dict()
if "auth_success" in query_params and query_params["auth_success"] == ["true"]:
    if "uid" in query_params and "email" in query_params:
        uid = query_params["uid"][0]
        email = query_params["email"][0]
        
        # Salvar dados do usuário na sessão
        st.session_state.authenticated = True
        st.session_state.user = {
            "user_id": uid,
            "email": email,
            "provider": "email",
            "login_time": datetime.now().isoformat()
        }
        
        # Limpar parâmetros da URL
        st.query_params.clear()
        st.rerun()

# Se não estiver autenticado, mostrar tela de login
if not st.session_state.authenticated:
    # Carregar scripts do Firebase
    st.markdown("""
    <!-- Firebase App (the core Firebase SDK) -->
    <script src="https://www.gstatic.com/firebasejs/9.22.0/firebase-app.js" type="module"></script>
    
    <!-- Firebase Authentication -->
    <script src="https://www.gstatic.com/firebasejs/9.22.0/firebase-auth.js" type="module"></script>
    
    <!-- Módulo de autenticação moderno -->
    <script src="/public/js/firebase-modern-auth.js" type="module"></script>
    """, unsafe_allow_html=True)
    
    # Script de inicialização
    st.markdown(f"""
    <script type="module">
        // Configuração do Firebase
        const firebaseConfig = {json.dumps(firebase_config)};
        
        // Inicialização depois que o DOM estiver pronto
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('Inicializando Firebase moderno...');
            
            // Verificar se o módulo está disponível
            if (window.firebaseModernAuth) {{
                const initialized = window.firebaseModernAuth.initialize(firebaseConfig);
                if (initialized) {{
                    console.log('Firebase inicializado com sucesso');
                    setupButtons();
                }} else {{
                    console.error('Falha ao inicializar Firebase');
                }}
            }} else {{
                console.error('Módulo de autenticação Firebase não encontrado');
            }}
        }});
        
        // Configurar botões
        function setupButtons() {{
            // Botão de login
            const loginBtn = document.getElementById('login_button');
            if (loginBtn) {{
                loginBtn.addEventListener('click', function() {{
                    const email = document.getElementById('login_email').value;
                    const password = document.getElementById('login_password').value;
                    
                    if (email && password) {{
                        window.firebaseModernAuth.loginWithEmail(email, password)
                            .catch(error => console.error('Erro de login:', error));
                    }} else {{
                        alert('Por favor, preencha email e senha');
                    }}
                }});
            }}
            
            // Botão de criação de conta
            const signupBtn = document.getElementById('signup_button');
            if (signupBtn) {{
                signupBtn.addEventListener('click', function() {{
                    const email = document.getElementById('signup_email').value;
                    const password = document.getElementById('signup_password').value;
                    const confirmPassword = document.getElementById('signup_confirm_password').value;
                    
                    if (!email || !password) {{
                        alert('Email e senha são obrigatórios');
                        return;
                    }}
                    
                    if (password !== confirmPassword) {{
                        alert('As senhas não coincidem');
                        return;
                    }}
                    
                    if (password.length < 6) {{
                        alert('A senha deve ter pelo menos 6 caracteres');
                        return;
                    }}
                    
                    window.firebaseModernAuth.createAccount(email, password)
                        .catch(error => console.error('Erro ao criar conta:', error));
                }});
            }}
            
            // Botão de recuperação de senha
            const resetBtn = document.getElementById('reset_button');
            if (resetBtn) {{
                resetBtn.addEventListener('click', function() {{
                    const email = document.getElementById('reset_email').value;
                    
                    if (email) {{
                        window.firebaseModernAuth.resetPassword(email)
                            .catch(error => console.error('Erro ao resetar senha:', error));
                    }} else {{
                        alert('Por favor, informe seu email');
                    }}
                }});
            }}
        }}
    </script>
    """, unsafe_allow_html=True)
    
    # Interface com abas
    tab1, tab2, tab3 = st.tabs(["Login", "Criar Conta", "Recuperar Senha"])
    
    with tab1:
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        
        # Campos de login
        st.text_input("Email", key="login_email_st", value="", 
                     help="Digite seu email cadastrado")
        st.text_input("Senha", type="password", key="login_password_st", value="", 
                     help="Digite sua senha")
        
        # Botões de ação
        col1, col2 = st.columns(2)
        with col1:
            st.button("Entrar", key="login_submit", use_container_width=True)
        with col2:
            # Modo de demonstração rápida
            if st.button("Modo Demo", key="demo_button", use_container_width=True):
                st.session_state.authenticated = True
                st.session_state.user = {
                    "email": "demo@example.com",
                    "name": "Usuário Demo",
                    "auth_method": "demo",
                    "demo": True,
                    "login_time": datetime.now().isoformat()
                }
                st.success("Modo demonstração ativado!")
                st.rerun()
        
        # Elementos HTML para integração com Firebase
        st.markdown("""
        <input type="hidden" id="login_email" />
        <input type="hidden" id="login_password" />
        <button id="login_button" style="display:none;">Login</button>
        
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Sincronizar campos Streamlit com campos ocultos
            const loginEmailSt = document.querySelector('input[aria-label="Email"]');
            const loginPasswordSt = document.querySelector('input[aria-label="Senha"]');
            const loginEmail = document.getElementById('login_email');
            const loginPassword = document.getElementById('login_password');
            const loginSubmit = document.querySelector('button[kind="primary"]:not([id])');
            const loginButton = document.getElementById('login_button');
            
            if (loginEmailSt && loginPasswordSt && loginEmail && loginPassword && loginSubmit && loginButton) {
                // Atualizar campos quando o usuário digitar
                loginEmailSt.addEventListener('input', function() {
                    loginEmail.value = this.value;
                });
                
                loginPasswordSt.addEventListener('input', function() {
                    loginPassword.value = this.value;
                });
                
                // Clicar no botão oculto quando o botão do Streamlit for clicado
                loginSubmit.addEventListener('click', function() {
                    loginButton.click();
                });
            }
        });
        </script>
        """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with tab2:
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        
        # Campos de criação de conta
        st.text_input("Email", key="signup_email_st", value="",
                    help="Digite seu email para cadastro")
        st.text_input("Senha", type="password", key="signup_password_st", value="",
                    help="Mínimo de 6 caracteres")
        st.text_input("Confirmar Senha", type="password", key="signup_confirm_password_st", value="",
                    help="Digite a senha novamente")
        
        # Botão de ação
        st.button("Criar Conta", key="signup_submit", use_container_width=True)
        
        # Elementos HTML para integração com Firebase
        st.markdown("""
        <input type="hidden" id="signup_email" />
        <input type="hidden" id="signup_password" />
        <input type="hidden" id="signup_confirm_password" />
        <button id="signup_button" style="display:none;">Signup</button>
        
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Sincronizar campos Streamlit com campos ocultos
            const signupEmailSt = document.querySelectorAll('input[aria-label="Email"]')[1];
            const signupPasswordSt = document.querySelectorAll('input[aria-label="Senha"]')[1];
            const signupConfirmSt = document.querySelector('input[aria-label="Confirmar Senha"]');
            
            const signupEmail = document.getElementById('signup_email');
            const signupPassword = document.getElementById('signup_password');
            const signupConfirm = document.getElementById('signup_confirm_password');
            
            const signupSubmit = document.querySelectorAll('button[kind="primary"]:not([id])')[1];
            const signupButton = document.getElementById('signup_button');
            
            if (signupEmailSt && signupPasswordSt && signupConfirmSt && 
                signupEmail && signupPassword && signupConfirm && 
                signupSubmit && signupButton) {
                
                // Atualizar campos quando o usuário digitar
                signupEmailSt.addEventListener('input', function() {
                    signupEmail.value = this.value;
                });
                
                signupPasswordSt.addEventListener('input', function() {
                    signupPassword.value = this.value;
                });
                
                signupConfirmSt.addEventListener('input', function() {
                    signupConfirm.value = this.value;
                });
                
                // Clicar no botão oculto quando o botão do Streamlit for clicado
                signupSubmit.addEventListener('click', function() {
                    signupButton.click();
                });
            }
        });
        </script>
        """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with tab3:
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        
        # Campo de email para recuperação
        st.text_input("Email para recuperação", key="reset_email_st", value="",
                    help="Digite o email cadastrado para receber o link de recuperação")
        
        # Botão de ação
        st.button("Enviar Email de Recuperação", key="reset_submit", use_container_width=True)
        
        # Elementos HTML para integração com Firebase
        st.markdown("""
        <input type="hidden" id="reset_email" />
        <button id="reset_button" style="display:none;">Reset</button>
        
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Sincronizar campos Streamlit com campos ocultos
            const resetEmailSt = document.querySelector('input[aria-label="Email para recuperação"]');
            const resetEmail = document.getElementById('reset_email');
            const resetSubmit = document.querySelectorAll('button[kind="primary"]:not([id])')[2];
            const resetButton = document.getElementById('reset_button');
            
            if (resetEmailSt && resetEmail && resetSubmit && resetButton) {
                // Atualizar campos quando o usuário digitar
                resetEmailSt.addEventListener('input', function() {
                    resetEmail.value = this.value;
                });
                
                // Clicar no botão oculto quando o botão do Streamlit for clicado
                resetSubmit.addEventListener('click', function() {
                    resetButton.click();
                });
            }
        });
        </script>
        """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Informação de uso
    st.markdown("""
    <div class="footer">
        <p>Este é um ambiente de demonstração para fins de desenvolvimento. Não utilize senhas reais.</p>
        <p>© 2025 Planner Organizer. Todos os direitos reservados.</p>
    </div>
    """, unsafe_allow_html=True)

# Se estiver autenticado, mostrar área do usuário
else:
    # Exibir mensagem de boas-vindas
    st.success(f"Login realizado com sucesso como {st.session_state.user.get('email')}")
    
    # Exibir informações do usuário
    st.write("### Dados do usuário")
    st.json(st.session_state.user)
    
    # Botões de ação
    col1, col2 = st.columns(2)
    
    with col1:
        # Botão para entrar no sistema
        if st.button("Acessar o Sistema", key="access_button", use_container_width=True):
            st.switch_page("app.py")
    
    with col2:
        # Botão para sair
        if st.button("Sair", key="logout_button", use_container_width=True):
            # Limpar dados da sessão
            st.session_state.authenticated = False
            st.session_state.user = None
            
            # Script para limpar localStorage
            st.markdown("""
            <script>
            localStorage.removeItem('firebase_user');
            localStorage.removeItem('firebase_user_temp');
            </script>
            """, unsafe_allow_html=True)
            
            st.rerun()