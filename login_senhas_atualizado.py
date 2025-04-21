"""
Página de login com funcionalidade de recuperação de senha
Este módulo implementa um login simplificado usando Firebase Auth
com suporte para recuperação de senha e verificação de email
"""
import os
import streamlit as st
import json
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Login - Planner Organizer",
    page_icon="🔑",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Verificar autenticação
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Configuração do Firebase
firebase_config = {
    "apiKey": os.environ.get("FIREBASE_API_KEY", st.secrets.get("FIREBASE_API_KEY", "")),
    "authDomain": "planner-organizer-68a23.firebaseapp.com",
    "projectId": "planner-organizer-68a23",
    "storageBucket": "planner-organizer-68a23.appspot.com", 
    "messagingSenderId": "763383033284",
    "appId": "1:763383033284:web:5a5dc3b4d3f5bc63631ce7"
}

# Adicionar CSS personalizado
st.markdown("""
<style>
    .gradient-heading {
        background: linear-gradient(45deg, #2557D6, #8B31BC);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
        padding: 10px 0;
        font-size: 2.5rem;
    }
    
    .login-box {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    
    .button-primary {
        background-color: #4CAF50;
        color: white;
        padding: 10px 15px;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        width: 100%;
        font-size: 16px;
    }
    
    .button-secondary {
        background-color: #f8f9fa;
        color: #333;
        padding: 10px 15px;
        border: 1px solid #ddd;
        border-radius: 5px;
        cursor: pointer;
        width: 100%;
        font-size: 16px;
    }
</style>
""", unsafe_allow_html=True)

# Área de logo e título
st.markdown('<div style="text-align: center;"><h1 class="gradient-heading">Planner Organizer</h1></div>', unsafe_allow_html=True)

# Scripts do Firebase
firebase_js = """
// Inicializar Firebase
function initializeFirebase() {
    if (typeof firebase === 'undefined') {
        console.error('Firebase não está carregado!');
        return false;
    }

    // Verificar se já está inicializado
    if (firebase.apps.length === 0) {
        try {
            firebase.initializeApp({
                apiKey: "%s",
                authDomain: "planner-organizer-68a23.firebaseapp.com",
                projectId: "planner-organizer-68a23",
                storageBucket: "planner-organizer-68a23.appspot.com",
                messagingSenderId: "763383033284",
                appId: "1:763383033284:web:5a5dc3b4d3f5bc63631ce7"
            });
            console.log('Firebase inicializado com sucesso');
            return true;
        } catch (error) {
            console.error('Erro ao inicializar Firebase:', error);
            return false;
        }
    } else {
        console.log('Firebase já está inicializado');
        return true;
    }
}

// Variáveis globais
var auth;

// Login com email e senha
function loginWithEmail(email, password) {
    console.log("Tentando login com email:", email);
    initializeFirebase();
    
    auth = firebase.auth();
    
    auth.signInWithEmailAndPassword(email, password)
        .then((userCredential) => {
            // Login bem-sucedido
            const user = userCredential.user;
            console.log("Login bem-sucedido para:", user.email);
            
            // Verificar se o email está verificado
            if (user.emailVerified) {
                console.log("Email verificado, redirecionando...");
                saveUserAndRedirect(user);
            } else {
                console.log("Email não verificado. Exibindo alerta.");
                alert("Por favor, verifique seu email antes de fazer login. Se não recebeu o email de verificação, use a opção 'Reenviar'.");
                
                // Salvar usuário mesmo sem verificação para permitir reenvio
                localStorage.setItem('firebase_user_temp', JSON.stringify({
                    uid: user.uid,
                    email: user.email,
                    emailVerified: user.emailVerified
                }));
            }
        })
        .catch((error) => {
            // Erro no login
            console.error("Erro ao fazer login:", error);
            
            let mensagem = "Erro ao fazer login. Verifique suas credenciais.";
            if (error.code === 'auth/user-not-found') {
                mensagem = "Email não cadastrado. Crie uma conta primeiro.";
            } else if (error.code === 'auth/wrong-password') {
                mensagem = "Senha incorreta. Tente novamente ou use a opção 'Esqueci minha senha'.";
            } else if (error.code === 'auth/too-many-requests') {
                mensagem = "Muitas tentativas de login. Tente novamente mais tarde ou redefina sua senha.";
            }
            
            alert(mensagem);
        });
}

// Criar nova conta
function createAccount(email, password) {
    console.log("Criando nova conta para:", email);
    initializeFirebase();
    
    auth = firebase.auth();
    
    auth.createUserWithEmailAndPassword(email, password)
        .then((userCredential) => {
            // Conta criada com sucesso
            const user = userCredential.user;
            console.log("Conta criada com sucesso para:", user.email);
            
            // Enviar email de verificação
            user.sendEmailVerification()
                .then(() => {
                    console.log("Email de verificação enviado");
                    alert("Conta criada com sucesso! Um email de verificação foi enviado para " + email + ". Por favor, verifique sua caixa de entrada e confirme seu email antes de fazer login.");
                })
                .catch((error) => {
                    console.error("Erro ao enviar email de verificação:", error);
                    alert("Conta criada, mas não foi possível enviar o email de verificação. Tente fazer login e reenviar o email de verificação.");
                });
        })
        .catch((error) => {
            // Erro na criação de conta
            console.error("Erro ao criar conta:", error);
            
            let mensagem = "Erro ao criar conta.";
            if (error.code === 'auth/email-already-in-use') {
                mensagem = "Este email já está em uso. Tente fazer login ou recuperar sua senha.";
            } else if (error.code === 'auth/invalid-email') {
                mensagem = "Email inválido. Por favor, verifique o formato do email.";
            } else if (error.code === 'auth/weak-password') {
                mensagem = "Senha fraca. Use pelo menos 6 caracteres.";
            }
            
            alert(mensagem);
        });
}

// Reenviar email de verificação
function resendVerificationEmail() {
    console.log("Reenviando email de verificação...");
    initializeFirebase();
    
    const user = auth.currentUser;
    if (user) {
        user.sendEmailVerification()
            .then(() => {
                console.log("Email de verificação reenviado com sucesso");
                alert("Um novo email de verificação foi enviado para " + user.email);
            })
            .catch((error) => {
                console.error("Erro ao reenviar email de verificação:", error);
                alert("Erro ao reenviar email de verificação: " + error.message);
            });
    } else {
        console.error("Nenhum usuário autenticado para reenviar verificação");
        alert("Você precisa estar logado para reenviar o email de verificação");
    }
}

// Recuperação de senha
function resetPassword(email) {
    console.log("Enviando email de recuperação...");
    initializeFirebase();
    
    // Configurações adicionais para recuperação de senha
    const actionCodeSettings = {
        // URL de redirecionamento após recuperação
        url: window.location.origin + window.location.pathname,
        // Manipular código como código de recuperação de senha
        handleCodeInApp: false
    };
    
    console.log("ActionCodeSettings:", actionCodeSettings);
    
    auth.sendPasswordResetEmail(email, actionCodeSettings)
        .then(() => {
            console.log("Email de recuperação enviado com sucesso");
            alert("Um email de recuperação de senha foi enviado para " + email + ". Por favor, verifique sua caixa de entrada e siga as instruções para redefinir sua senha.");
        })
        .catch((error) => {
            console.error("Erro ao enviar email de recuperação:", error);
            
            let mensagem = "Erro ao enviar email de recuperação: " + error.message;
            if (error.code === 'auth/user-not-found') {
                mensagem = "Email não encontrado. Verifique se o email está correto ou crie uma nova conta.";
            } else if (error.code === 'auth/invalid-email') {
                mensagem = "Email inválido. Por favor, verifique o formato do email.";
            }
            
            alert(mensagem);
        });
}

// Salvar dados do usuário e redirecionar
function saveUserAndRedirect(user) {
    // Salvar no localStorage 
    localStorage.setItem('firebase_user', JSON.stringify({
        uid: user.uid,
        email: user.email,
        emailVerified: user.emailVerified,
        lastLogin: new Date().toISOString()
    }));
    
    // Redirecionar com parâmetros para o Streamlit
    let url = new URL(window.location.href);
    url.searchParams.set('auth_success', 'true');
    url.searchParams.set('uid', user.uid);
    url.searchParams.set('email', user.email);
    
    // Redirecionar
    console.log("Redirecionando para:", url.toString());
    window.location.href = url.toString();
}

// Encerrar sessão
function signOut() {
    console.log("Encerrando sessão...");
    initializeFirebase();
    
    auth.signOut().then(() => {
        console.log("Logout realizado com sucesso");
        localStorage.removeItem('firebase_user');
        
        // Redirecionar para a página de login
        window.location.href = window.location.pathname;
    }).catch((error) => {
        console.error("Erro ao encerrar sessão:", error);
    });
}
""" % firebase_config["apiKey"]

# Verificar parâmetros de autenticação
query_params = st.query_params.to_dict()
if "auth_success" in query_params and query_params["auth_success"][0] == "true":
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

# Função principal
def main():
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