"""
Página de login com recuperação de senha restaurada
Esta versão foi configurada para usar as mesmas configurações
que estavam funcionando no dia 19/04
"""
import streamlit as st
import os
import json
import logging
import time
from datetime import datetime

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração da página
st.set_page_config(
    page_title="Planner Organizer - Login",
    page_icon="🔒",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Inicializar variáveis de sessão
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "current_tab" not in st.session_state:
    st.session_state.current_tab = "login"  # login, signup, reset

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
        width: 100%;
        background-color: #2557D6;
        color: white;
        padding: 10px 15px;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        text-align: center;
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
    "apiKey": os.environ.get("FIREBASE_API_KEY", st.secrets.get("FIREBASE_API_KEY")),
    "authDomain": "planner-organizer-68a23.firebaseapp.com",
    "projectId": "planner-organizer-68a23",
    "storageBucket": "planner-organizer-68a23.appspot.com",
    "messagingSenderId": "763383033284",
    "appId": "1:763383033284:web:5a5dc3b4d3f5bc63631ce7"
}

# Incorporar scripts do Firebase
st.markdown(f"""
<!-- Firebase App (the core Firebase SDK) -->
<script src="https://www.gstatic.com/firebasejs/9.22.0/firebase-app.js" type="module"></script>
<script src="https://www.gstatic.com/firebasejs/9.22.0/firebase-auth.js" type="module"></script>

<script type="module">
    // Import the functions you need from the SDKs
    import {{ initializeApp }} from "https://www.gstatic.com/firebasejs/9.22.0/firebase-app.js";
    import {{ 
        getAuth, 
        signInWithEmailAndPassword, 
        createUserWithEmailAndPassword,
        sendPasswordResetEmail,
        sendEmailVerification
    }} from "https://www.gstatic.com/firebasejs/9.22.0/firebase-auth.js";

    // Your web app's Firebase configuration
    const firebaseConfig = {json.dumps(firebase_config)};

    // Initialize Firebase
    const app = initializeApp(firebaseConfig);
    const auth = getAuth(app);
    
    // Make auth and functions available globally
    window.auth = auth;
    window.firebaseFunctions = {{
        login: async function(email, password) {{
            try {{
                const userCredential = await signInWithEmailAndPassword(auth, email, password);
                const user = userCredential.user;
                console.log("Login successful:", user.email);
                
                if (user.emailVerified) {{
                    // Salvar no localStorage
                    localStorage.setItem('firebase_user', JSON.stringify({{
                        uid: user.uid,
                        email: user.email,
                        emailVerified: user.emailVerified,
                        lastLogin: new Date().toISOString()
                    }}));
                    
                    // Redirecionar para a aplicação principal
                    window.location.href = "/app";
                    return true;
                }} else {{
                    alert("Por favor, verifique seu email antes de fazer login.");
                    return false;
                }}
            }} catch (error) {{
                console.error("Login error:", error);
                let errorMessage = "Erro ao fazer login. Verifique suas credenciais.";
                
                if (error.code === 'auth/user-not-found') {{
                    errorMessage = "Email não cadastrado. Crie uma conta primeiro.";
                }} else if (error.code === 'auth/wrong-password') {{
                    errorMessage = "Senha incorreta. Tente novamente ou use a opção 'Esqueci minha senha'.";
                }} else if (error.code === 'auth/too-many-requests') {{
                    errorMessage = "Muitas tentativas de login. Tente novamente mais tarde ou redefina sua senha.";
                }}
                
                alert(errorMessage);
                return false;
            }}
        }},
        
        signup: async function(email, password) {{
            try {{
                const userCredential = await createUserWithEmailAndPassword(auth, email, password);
                const user = userCredential.user;
                console.log("Account created for:", user.email);
                
                // Enviar email de verificação
                try {{
                    await sendEmailVerification(user);
                    alert("Conta criada com sucesso! Um email de verificação foi enviado para " + email + ".");
                    return true;
                }} catch (verifyError) {{
                    console.error("Email verification error:", verifyError);
                    alert("Conta criada, mas não foi possível enviar o email de verificação. Tente fazer login e solicitar reenvio.");
                    return true;
                }}
            }} catch (error) {{
                console.error("Signup error:", error);
                let errorMessage = "Erro ao criar conta.";
                
                if (error.code === 'auth/email-already-in-use') {{
                    errorMessage = "Este email já está em uso. Tente fazer login ou recuperar sua senha.";
                }} else if (error.code === 'auth/invalid-email') {{
                    errorMessage = "Email inválido. Por favor, verifique o formato do email.";
                }} else if (error.code === 'auth/weak-password') {{
                    errorMessage = "Senha fraca. Use pelo menos 6 caracteres.";
                }}
                
                alert(errorMessage);
                return false;
            }}
        }},
        
        resetPassword: async function(email) {{
            try {{
                await sendPasswordResetEmail(auth, email);
                console.log("Password reset email sent");
                alert("Um email de recuperação de senha foi enviado para " + email + ".");
                return true;
            }} catch (error) {{
                console.error("Password reset error:", error);
                let errorMessage = "Erro ao enviar email de recuperação.";
                
                if (error.code === 'auth/user-not-found') {{
                    errorMessage = "Email não encontrado. Verifique se o email está correto ou crie uma nova conta.";
                }} else if (error.code === 'auth/invalid-email') {{
                    errorMessage = "Email inválido. Por favor, verifique o formato do email.";
                }}
                
                alert(errorMessage);
                return false;
            }}
        }}
    }};
    
    // Setup form handlers when DOM is loaded
    document.addEventListener('DOMContentLoaded', function() {{
        setupFormHandlers();
        console.log("Firebase initialized successfully");
    }});
    
    function setupFormHandlers() {{
        // Login form
        const loginForm = document.getElementById('login-form');
        if (loginForm) {{
            loginForm.addEventListener('submit', function(event) {{
                event.preventDefault();
                
                const email = document.getElementById('login-email').value;
                const password = document.getElementById('login-password').value;
                
                if (email && password) {{
                    window.firebaseFunctions.login(email, password);
                }} else {{
                    alert("Por favor, preencha todos os campos.");
                }}
            }});
        }}
        
        // Signup form
        const signupForm = document.getElementById('signup-form');
        if (signupForm) {{
            signupForm.addEventListener('submit', function(event) {{
                event.preventDefault();
                
                const email = document.getElementById('signup-email').value;
                const password = document.getElementById('signup-password').value;
                const confirmPassword = document.getElementById('signup-confirm-password').value;
                
                if (!email || !password || !confirmPassword) {{
                    alert("Por favor, preencha todos os campos.");
                    return;
                }}
                
                if (password !== confirmPassword) {{
                    alert("As senhas não coincidem.");
                    return;
                }}
                
                if (password.length < 6) {{
                    alert("A senha deve ter pelo menos 6 caracteres.");
                    return;
                }}
                
                window.firebaseFunctions.signup(email, password);
            }});
        }}
        
        // Reset password form
        const resetForm = document.getElementById('reset-form');
        if (resetForm) {{
            resetForm.addEventListener('submit', function(event) {{
                event.preventDefault();
                
                const email = document.getElementById('reset-email').value;
                
                if (email) {{
                    window.firebaseFunctions.resetPassword(email);
                }} else {{
                    alert("Por favor, informe seu email.");
                }}
            }});
        }}
    }}
</script>
""", unsafe_allow_html=True)

# Interface baseada na aba selecionada
if st.session_state.authenticated:
    # Área logada
    st.success(f"Login realizado com sucesso como {st.session_state.user.get('email', 'usuário')}")
    
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
            st.rerun()
else:
    # Seleção de abas
    tab1, tab2, tab3 = st.tabs(["Login", "Criar Conta", "Recuperar Senha"])
    
    with tab1:
        # Formulário de login
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        
        # Campos HTML para login
        st.markdown("""
        <form id="login-form">
            <div style="margin-bottom: 15px;">
                <label for="login-email">Email</label>
                <input type="email" id="login-email" required 
                       style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
            </div>
            
            <div style="margin-bottom: 15px;">
                <label for="login-password">Senha</label>
                <input type="password" id="login-password" required
                       style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
            </div>
            
            <button type="submit" class="btn-primary">Entrar</button>
        </form>
        """, unsafe_allow_html=True)
        
        # Informações para o modo de demonstração
        st.info("Para acessar o modo de demonstração, utilize as credenciais: admin/admin")
        
        # Botão para modo de demonstração
        if st.button("Entrar como Admin (Demo)", key="demo_button", use_container_width=True):
            st.session_state.authenticated = True
            st.session_state.user = {
                "user_id": "demo-123",
                "email": "admin@example.com",
                "provider": "demo",
                "demo_mode": True,
                "login_time": datetime.now().isoformat()
            }
            st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with tab2:
        # Formulário de criação de conta
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        
        st.markdown("""
        <form id="signup-form">
            <div style="margin-bottom: 15px;">
                <label for="signup-email">Email</label>
                <input type="email" id="signup-email" required
                       style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
            </div>
            
            <div style="margin-bottom: 15px;">
                <label for="signup-password">Senha</label>
                <input type="password" id="signup-password" required
                       style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;"
                       placeholder="Mínimo 6 caracteres">
            </div>
            
            <div style="margin-bottom: 15px;">
                <label for="signup-confirm-password">Confirmar Senha</label>
                <input type="password" id="signup-confirm-password" required
                       style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
            </div>
            
            <button type="submit" class="btn-primary">Criar Conta</button>
        </form>
        """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with tab3:
        # Formulário de recuperação de senha
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        
        st.markdown("""
        <form id="reset-form">
            <div style="margin-bottom: 15px;">
                <p>Informe seu email para receber um link de recuperação de senha.</p>
                <label for="reset-email">Email</label>
                <input type="email" id="reset-email" required
                       style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
            </div>
            
            <button type="submit" class="btn-primary">Enviar Link de Recuperação</button>
        </form>
        """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

# Informações no rodapé
st.markdown("""
<div class="footer">
    <p>© 2025 Planner Organizer. Todos os direitos reservados.</p>
</div>
""", unsafe_allow_html=True)