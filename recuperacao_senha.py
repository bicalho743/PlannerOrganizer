"""
Página minimalista de login com recuperação de senha usando Firebase Auth
"""
import streamlit as st
import os
import json
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Recuperação de Senha - Planner Organizer",
    page_icon="🔒",
    layout="centered"
)

# Inicializar variáveis de sessão
if "view" not in st.session_state:
    st.session_state.view = "login"  # login, reset, signup

# Funções para alternar entre visualizações
def switch_to_login():
    st.session_state.view = "login"
    
def switch_to_reset():
    st.session_state.view = "reset"
    
def switch_to_signup():
    st.session_state.view = "signup"

# Função para mostrar mensagens
def show_message(message, type="info"):
    if type == "info":
        st.info(message)
    elif type == "success":
        st.success(message)
    elif type == "error":
        st.error(message)
    elif type == "warning":
        st.warning(message)

# Estilos CSS
st.markdown("""
<style>
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 20px;
        border-radius: 10px;
        background-color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .title {
        text-align: center;
        color: #2557D6;
        margin-bottom: 20px;
    }
    
    .form-group {
        margin-bottom: 15px;
    }
    
    .form-group label {
        display: block;
        margin-bottom: 5px;
        font-weight: 500;
    }
    
    .form-control {
        width: 100%;
        padding: 8px;
        border: 1px solid #ddd;
        border-radius: 4px;
    }
    
    .btn-primary {
        background-color: #2557D6;
        color: white;
        border: none;
        padding: 10px 15px;
        border-radius: 4px;
        cursor: pointer;
        width: 100%;
    }
    
    .link {
        color: #2557D6;
        text-decoration: none;
        cursor: pointer;
    }
    
    .text-center {
        text-align: center;
    }
    
    .mt-3 {
        margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Configuração do Firebase
firebase_config = {
    "apiKey": os.environ.get("FIREBASE_API_KEY", st.secrets.get("FIREBASE_API_KEY")),
    "authDomain": "planner-organizer-68a23.firebaseapp.com",
    "projectId": "planner-organizer-68a23",
    "storageBucket": "planner-organizer-68a23.appspot.com",
    "messagingSenderId": "763383033284",
    "appId": "1:763383033284:web:5a5dc3b4d3f5bc63631ce7"
}

# Carregar scripts do Firebase
st.markdown("""
<script src="https://www.gstatic.com/firebasejs/9.22.0/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/9.22.0/firebase-auth-compat.js"></script>

<script>
    // Inicializar Firebase
    const firebaseConfig = {config_json};
    
    // Inicializar Firebase
    firebase.initializeApp(firebaseConfig);
    
    // Funções de autenticação
    function loginUser(email, password) {
        return firebase.auth().signInWithEmailAndPassword(email, password)
            .then((userCredential) => {
                // Login bem-sucedido
                const user = userCredential.user;
                
                // Verificar se o email foi verificado
                if (user.emailVerified) {
                    window.streamlitMessageSender.postToStreamlit({
                        type: "login_success",
                        data: {
                            uid: user.uid,
                            email: user.email,
                            emailVerified: user.emailVerified
                        }
                    });
                    return true;
                } else {
                    alert("Por favor, verifique seu email antes de fazer login.");
                    return false;
                }
            })
            .catch((error) => {
                console.error("Erro de login:", error);
                let message = "Falha no login. Verifique suas credenciais.";
                
                if (error.code === 'auth/user-not-found') {
                    message = "Email não cadastrado.";
                } else if (error.code === 'auth/wrong-password') {
                    message = "Senha incorreta.";
                }
                
                window.streamlitMessageSender.postToStreamlit({
                    type: "login_error",
                    data: { message: message }
                });
                
                return false;
            });
    }
    
    function resetPassword(email) {
        return firebase.auth().sendPasswordResetEmail(email)
            .then(() => {
                window.streamlitMessageSender.postToStreamlit({
                    type: "reset_success",
                    data: { email: email }
                });
                return true;
            })
            .catch((error) => {
                console.error("Erro de recuperação de senha:", error);
                let message = "Erro ao enviar email de recuperação.";
                
                if (error.code === 'auth/user-not-found') {
                    message = "Email não encontrado.";
                }
                
                window.streamlitMessageSender.postToStreamlit({
                    type: "reset_error",
                    data: { message: message }
                });
                
                return false;
            });
    }
    
    function createAccount(email, password) {
        return firebase.auth().createUserWithEmailAndPassword(email, password)
            .then((userCredential) => {
                // Cadastro bem-sucedido
                const user = userCredential.user;
                
                // Enviar email de verificação
                user.sendEmailVerification()
                    .then(() => {
                        window.streamlitMessageSender.postToStreamlit({
                            type: "signup_success",
                            data: {
                                uid: user.uid,
                                email: user.email
                            }
                        });
                    })
                    .catch((error) => {
                        console.error("Erro ao enviar email de verificação:", error);
                    });
                
                return true;
            })
            .catch((error) => {
                console.error("Erro de cadastro:", error);
                let message = "Erro ao criar conta.";
                
                if (error.code === 'auth/email-already-in-use') {
                    message = "Este email já está em uso.";
                } else if (error.code === 'auth/invalid-email') {
                    message = "Email inválido.";
                } else if (error.code === 'auth/weak-password') {
                    message = "Senha muito fraca.";
                }
                
                window.streamlitMessageSender.postToStreamlit({
                    type: "signup_error",
                    data: { message: message }
                });
                
                return false;
            });
    }
    
    // Adicionar um objeto para comunicação com o Streamlit
    window.streamlitMessageSender = {
        postToStreamlit: function(message) {
            // Uma forma de interagir com o Streamlit
            setTimeout(function() {
                window.parent.postMessage({
                    type: "streamlit:setComponentValue",
                    value: message
                }, "*");
            }, 100);
        }
    };
    
    // Escutar mensagens do Streamlit
    window.addEventListener("message", function(event) {
        if (event.data.type === "streamlit:componentReady") {
            console.log("Componente pronto para comunicação");
        }
        else if (event.data.type === "streamlit:doLogin") {
            const { email, password } = event.data;
            loginUser(email, password);
        }
        else if (event.data.type === "streamlit:doReset") {
            const { email } = event.data;
            resetPassword(email);
        }
        else if (event.data.type === "streamlit:doSignup") {
            const { email, password } = event.data;
            createAccount(email, password);
        }
    });
    
    document.addEventListener('DOMContentLoaded', function() {
        console.log("Firebase Auth inicializado");
    });
</script>
""".replace("{config_json}", json.dumps(firebase_config)), unsafe_allow_html=True)

# Componente para comunicação com JavaScript
st.components.v1.html("""
<div id="firebase-message-receiver" style="display: none;"></div>
<script>
    // Este componente atua como receptor de mensagens do Firebase
    const component = document.getElementById('firebase-message-receiver');
    
    // Quando receber mensagem do Firebase, envia para o Streamlit
    component.addEventListener('message', function(event) {
        window.parent.postMessage({
            type: "streamlit:setComponentValue",
            value: event.detail
        }, "*");
    });
    
    // Para simular um evento de componente pronto
    window.parent.postMessage({
        type: "streamlit:componentReady",
        componentId: "firebase-message-receiver"
    }, "*");
</script>
""", height=0)

# Título principal
st.markdown("<h1 class='title'>Planner Organizer</h1>", unsafe_allow_html=True)

# Mostrar tela de login
if st.session_state.view == "login":
    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    st.subheader("Login")
    
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Senha", type="password", key="login_password")
    
    if st.button("Entrar", use_container_width=True, key="login_button"):
        # Usando JavaScript para fazer login
        st.components.v1.html(f"""
        <script>
            window.parent.postMessage({{
                type: "streamlit:doLogin",
                email: "{email}",
                password: "{password}"
            }}, "*");
        </script>
        """, height=0)
    
    st.markdown("<div class='text-center mt-3'>", unsafe_allow_html=True)
    st.markdown(f"<a class='link' onclick='window.parent.postMessage({{\"type\":\"streamlit:userRerun\",\"args\":{{}},\"target\":\"*\",\"initialQueryParams\":\"?view=reset\"}}, \"*\");'>Esqueci minha senha</a>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='text-center mt-3'>", unsafe_allow_html=True)
    st.markdown(f"<a class='link' onclick='window.parent.postMessage({{\"type\":\"streamlit:userRerun\",\"args\":{{}},\"target\":\"*\",\"initialQueryParams\":\"?view=signup\"}}, \"*\");'>Não tenho uma conta</a>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# Mostrar tela de recuperação de senha
elif st.session_state.view == "reset":
    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    st.subheader("Recuperar Senha")
    
    st.write("Informe seu email para receber um link de recuperação de senha.")
    
    email = st.text_input("Email", key="reset_email")
    
    if st.button("Enviar Link de Recuperação", use_container_width=True, key="reset_button"):
        # Usando JavaScript para fazer a recuperação de senha
        st.components.v1.html(f"""
        <script>
            window.parent.postMessage({{
                type: "streamlit:doReset",
                email: "{email}"
            }}, "*");
        </script>
        """, height=0)
    
    st.markdown("<div class='text-center mt-3'>", unsafe_allow_html=True)
    st.markdown(f"<a class='link' onclick='window.parent.postMessage({{\"type\":\"streamlit:userRerun\",\"args\":{{}},\"target\":\"*\",\"initialQueryParams\":\"?view=login\"}}, \"*\");'>Voltar para o login</a>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# Mostrar tela de cadastro
elif st.session_state.view == "signup":
    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    st.subheader("Criar Conta")
    
    email = st.text_input("Email", key="signup_email")
    password = st.text_input("Senha", type="password", key="signup_password", help="Mínimo 6 caracteres")
    confirm_password = st.text_input("Confirmar Senha", type="password", key="signup_confirm_password")
    
    if st.button("Criar Conta", use_container_width=True, key="signup_button"):
        if password != confirm_password:
            st.error("As senhas não coincidem.")
        elif len(password) < 6:
            st.error("A senha deve ter pelo menos 6 caracteres.")
        else:
            # Usando JavaScript para criar conta
            st.components.v1.html(f"""
            <script>
                window.parent.postMessage({{
                    type: "streamlit:doSignup",
                    email: "{email}",
                    password: "{password}"
                }}, "*");
            </script>
            """, height=0)
    
    st.markdown("<div class='text-center mt-3'>", unsafe_allow_html=True)
    st.markdown(f"<a class='link' onclick='window.parent.postMessage({{\"type\":\"streamlit:userRerun\",\"args\":{{}},\"target\":\"*\",\"initialQueryParams\":\"?view=login\"}}, \"*\");'>Já tenho uma conta</a>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# Verificar parâmetros da URL
query_params = st.query_params.to_dict()
if "view" in query_params:
    st.session_state.view = query_params["view"]
    st.query_params.clear()
    st.rerun()

# Receber mensagens do JavaScript
component_value = st.empty()

if component_value:
    try:
        value = component_value
        
        if isinstance(value, dict) and "type" in value:
            message_type = value.get("type")
            data = value.get("data", {})
            
            if message_type == "login_success":
                st.success(f"Login realizado com sucesso! Bem-vindo, {data.get('email')}.")
                st.switch_page("app.py")
            
            elif message_type == "login_error":
                st.error(data.get("message", "Erro ao fazer login."))
            
            elif message_type == "reset_success":
                st.success(f"Email de recuperação enviado para {data.get('email')}. Verifique sua caixa de entrada.")
            
            elif message_type == "reset_error":
                st.error(data.get("message", "Erro ao enviar email de recuperação."))
            
            elif message_type == "signup_success":
                st.success(f"Conta criada com sucesso! Um email de verificação foi enviado para {data.get('email')}.")
                # Após alguns segundos, redirecionar para o login
                st.session_state.view = "login"
                st.rerun()
            
            elif message_type == "signup_error":
                st.error(data.get("message", "Erro ao criar conta."))
    except Exception as e:
        print(f"Erro ao processar mensagem: {e}")

# Mensagem de rodapé
st.markdown("""
<div style='text-align: center; margin-top: 20px; color: #666; font-size: 0.8rem;'>
    © 2025 Planner Organizer. Todos os direitos reservados.
</div>
""", unsafe_allow_html=True)