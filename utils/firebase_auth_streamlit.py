"""
Módulo para integração do Firebase Authentication com Streamlit
Usando uma abordagem híbrida JavaScript/Python
"""
import streamlit as st
import requests
import os
import json
import time
import uuid
from datetime import datetime, timedelta

# Constantes para configuração
BASE_API_URL = "http://localhost:8000"
COOKIE_NAME = "firebase_auth"
COOKIE_EXPIRY = 14  # Dias para expiração do cookie

class FirebaseAuth:
    """
    Classe para gerenciar autenticação Firebase no Streamlit
    Usando componentes JavaScript e callbacks Python
    """
    def __init__(self, api_url=BASE_API_URL):
        """
        Inicializa o gerenciador de autenticação
        
        Args:
            api_url (str): URL base da API para comunicação com o backend
        """
        self.api_url = api_url
        self.cookie_manager_ready = 'cookie_manager' in st.session_state
        
        # Inicializar o estado da sessão para autenticação
        if 'firebase_user' not in st.session_state:
            st.session_state['firebase_user'] = None
        if 'auth_status' not in st.session_state:
            st.session_state['auth_status'] = 'signed_out'
        if 'login_error' not in st.session_state:
            st.session_state['login_error'] = None
            
        # Verificar se o usuário já está autenticado via cookie
        self._check_auth_cookie()
    
    def _check_auth_cookie(self):
        """Verifica se existe um cookie de autenticação válido"""
        if self.cookie_manager_ready:
            cookie_data = st.session_state.cookie_manager.get(COOKIE_NAME)
            if cookie_data:
                try:
                    auth_data = json.loads(cookie_data)
                    # Verificar se o token não expirou
                    if 'expiry' in auth_data and auth_data['expiry'] > time.time():
                        # Tentar verificar no backend
                        if self._verify_user_in_backend(auth_data.get('uid')):
                            st.session_state['firebase_user'] = auth_data
                            st.session_state['auth_status'] = 'signed_in'
                            return True
                except Exception as e:
                    print(f"Erro ao verificar cookie de autenticação: {e}")
            
            # Se chegou aqui, o cookie não é válido ou não existe
            if self.cookie_manager_ready:
                st.session_state.cookie_manager.delete(COOKIE_NAME)
        return False
    
    def _verify_user_in_backend(self, uid):
        """
        Verifica se um usuário existe no backend
        
        Args:
            uid (str): UID do usuário Firebase
            
        Returns:
            bool: True se o usuário existe no backend, False caso contrário
        """
        if not uid:
            return False
            
        try:
            response = requests.get(f"{self.api_url}/api/usuario/{uid}")
            if response.status_code == 200:
                return True
        except Exception as e:
            print(f"Erro ao verificar usuário no backend: {e}")
        return False
    
    def _save_auth_cookie(self, user_data):
        """
        Salva os dados de autenticação em um cookie
        
        Args:
            user_data (dict): Dados do usuário autenticado
        """
        if self.cookie_manager_ready:
            # Adicionar tempo de expiração
            expiry_time = time.time() + (COOKIE_EXPIRY * 24 * 60 * 60)
            cookie_data = {**user_data, 'expiry': expiry_time}
            
            # Salvar no cookie
            st.session_state.cookie_manager.set(
                COOKIE_NAME, 
                json.dumps(cookie_data),
                expires_at=datetime.now() + timedelta(days=COOKIE_EXPIRY)
            )
    
    def render_login_ui(self):
        """
        Renderiza a UI de login com Firebase
        Esta função deve ser chamada na página de login
        """
        # Componente JavaScript para autenticação Firebase
        firebase_auth_component = """
        <script type="module">
          // Firebase App (the core Firebase SDK) is always required and must be listed first
          import { initializeApp } from "https://www.gstatic.com/firebasejs/10.9.0/firebase-app.js";
          import { getAuth, signInWithPopup, GoogleAuthProvider, FacebookAuthProvider, 
                   GithubAuthProvider, signInWithEmailAndPassword, createUserWithEmailAndPassword, 
                   sendPasswordResetEmail } from "https://www.gstatic.com/firebasejs/10.9.0/firebase-auth.js";
          
          // Firebase configuration
          const firebaseConfig = {
            apiKey: "%s",
            authDomain: "%s",
            projectId: "%s",
            storageBucket: "%s",
            messagingSenderId: "%s",
            appId: "%s"
          };
          
          // Initialize Firebase
          const app = initializeApp(firebaseConfig);
          const auth = getAuth(app);
          
          // Provider setup
          const googleProvider = new GoogleAuthProvider();
          const facebookProvider = new FacebookAuthProvider();
          const githubProvider = new GithubProvider();
          
          // Login with Google
          window.loginWithGoogle = function() {
            signInWithPopup(auth, googleProvider)
              .then((result) => {
                const user = result.user;
                sendUserToStreamlit(user);
              }).catch((error) => {
                sendErrorToStreamlit(error.code, error.message);
              });
          }
          
          // Login with Facebook  
          window.loginWithFacebook = function() {
            signInWithPopup(auth, facebookProvider)
              .then((result) => {
                const user = result.user;
                sendUserToStreamlit(user);
              }).catch((error) => {
                sendErrorToStreamlit(error.code, error.message);
              });
          }
          
          // Login with GitHub
          window.loginWithGithub = function() {
            signInWithPopup(auth, githubProvider)
              .then((result) => {
                const user = result.user;
                sendUserToStreamlit(user);
              }).catch((error) => {
                sendErrorToStreamlit(error.code, error.message);
              });
          }
          
          // Login with Email/Password
          window.loginWithEmail = function(email, password) {
            signInWithEmailAndPassword(auth, email, password)
              .then((userCredential) => {
                const user = userCredential.user;
                sendUserToStreamlit(user);
              })
              .catch((error) => {
                sendErrorToStreamlit(error.code, error.message);
              });
          }
          
          // Create account with Email/Password
          window.createAccount = function(email, password) {
            createUserWithEmailAndPassword(auth, email, password)
              .then((userCredential) => {
                const user = userCredential.user;
                sendUserToStreamlit(user);
              })
              .catch((error) => {
                sendErrorToStreamlit(error.code, error.message);
              });
          }
          
          // Send password reset email
          window.resetPassword = function(email) {
            sendPasswordResetEmail(auth, email)
              .then(() => {
                // Reset email sent successfully
                window.parent.postMessage({
                  type: "streamlit:firebase:passwordReset",
                  status: "success",
                  email: email
                }, "*");
              })
              .catch((error) => {
                sendErrorToStreamlit(error.code, error.message);
              });
          }
          
          // Listen for auth state changes
          auth.onAuthStateChanged((user) => {
            if (user) {
              sendUserToStreamlit(user);
            } else {
              // User is signed out
              window.parent.postMessage({
                type: "streamlit:firebase:signOut",
              }, "*");
            }
          });
          
          // Function to send user data to Streamlit
          function sendUserToStreamlit(user) {
            // Format JSON to match backend expectations
            const userData = {
              uid: user.uid,
              email: user.email,
              nome: user.displayName || '',
              provedor: user.providerData[0].providerId,
              foto_url: user.photoURL || '',
              email_verificado: user.emailVerified
            };
            
            // Send to Streamlit via postMessage
            window.parent.postMessage({
              type: "streamlit:firebase:user",
              user: userData
            }, "*");
          }
          
          // Function to send errors to Streamlit
          function sendErrorToStreamlit(code, message) {
            window.parent.postMessage({
              type: "streamlit:firebase:error",
              error: {
                code: code,
                message: message
              }
            }, "*");
          }
          
          // Handle messages from Streamlit
          window.addEventListener("message", function(event) {
            const data = event.data;
            
            if (data.type === "streamlit:firebase:loginWithEmail") {
              window.loginWithEmail(data.email, data.password);
            } else if (data.type === "streamlit:firebase:createAccount") {
              window.createAccount(data.email, data.password);
            } else if (data.type === "streamlit:firebase:resetPassword") {
              window.resetPassword(data.email);
            } else if (data.type === "streamlit:firebase:loginWithGoogle") {
              window.loginWithGoogle();
            } else if (data.type === "streamlit:firebase:loginWithFacebook") {
              window.loginWithFacebook();
            } else if (data.type === "streamlit:firebase:loginWithGithub") {
              window.loginWithGithub();
            } else if (data.type === "streamlit:firebase:signOut") {
              auth.signOut();
            }
          });
        </script>
        """ % (
            os.environ.get("FIREBASE_API_KEY", ""),
            os.environ.get("FIREBASE_AUTH_DOMAIN", ""),
            os.environ.get("FIREBASE_PROJECT_ID", ""),
            os.environ.get("FIREBASE_STORAGE_BUCKET", ""),
            os.environ.get("FIREBASE_MESSAGING_SENDER_ID", ""),
            os.environ.get("FIREBASE_APP_ID", "")
        )
        
        # Renderizar o componente JavaScript
        st.components.v1.html(firebase_auth_component, height=0)
        
        # Adicionar JavaScript para lidar com eventos dos botões
        st.markdown("""
        <script>
          // Função para enviar mensagem ao Firebase
          function sendToFirebase(type, data) {
            window.postMessage({
              type: type,
              ...data
            }, "*");
          }
          
          // Configuração dos botões ao carregar a página
          document.addEventListener("DOMContentLoaded", function() {
            // Botões de login social podem ser configurados aqui
            // Este script é executado após a renderização do Streamlit
          });
        </script>
        """, unsafe_allow_html=True)
        
        # Verificar e processar mensagens JavaScript
        if st.session_state.get('auth_status') == 'signed_in':
            return True
        
        return False
    
    def handle_auth_callback(self, key=None):
        """
        Processa o callback de autenticação (deve ser chamado em cada página)
        
        Args:
            key (str, optional): Chave única para o componente. Defaults to None.
        
        Returns:
            bool: True se o usuário está autenticado, False caso contrário
        """
        # Gerar chave única se não fornecida
        if key is None:
            key = f"firebase_auth_{str(uuid.uuid4())}"
        
        # Componente invisível para receber callbacks
        callback_code = """
        <script>
          // Função para processar mensagens do Firebase Auth
          window.addEventListener("message", function(event) {
            const data = event.data;
            
            if (data.type === "streamlit:firebase:user") {
              // Salvar no Streamlit via session state
              const username = data.user.nome || data.user.email.split('@')[0];
              const streamlitData = {
                action: "firebase_auth_callback",
                status: "signed_in",
                user: data.user,
                error: null
              };
              
              // Enviar para Streamlit usando o widget gerado
              window.parent.postMessage({
                type: "streamlit:setComponentValue",
                value: streamlitData,
                dataType: "json",
                componentInstance: "%s"
              }, "*");
            } else if (data.type === "streamlit:firebase:error") {
              // Processar erro de autenticação
              const streamlitData = {
                action: "firebase_auth_callback",
                status: "error",
                user: null,
                error: data.error
              };
              
              window.parent.postMessage({
                type: "streamlit:setComponentValue",
                value: streamlitData,
                dataType: "json",
                componentInstance: "%s"
              }, "*");
            } else if (data.type === "streamlit:firebase:signOut") {
              // Processar logout
              const streamlitData = {
                action: "firebase_auth_callback",
                status: "signed_out",
                user: null,
                error: null
              };
              
              window.parent.postMessage({
                type: "streamlit:setComponentValue",
                value: streamlitData,
                dataType: "json",
                componentInstance: "%s"
              }, "*");
            } else if (data.type === "streamlit:firebase:passwordReset") {
              // Processar reset de senha
              const streamlitData = {
                action: "firebase_auth_callback",
                status: "password_reset",
                email: data.email,
                error: null
              };
              
              window.parent.postMessage({
                type: "streamlit:setComponentValue",
                value: streamlitData,
                dataType: "json",
                componentInstance: "%s"
              }, "*");
            }
          });
        </script>
        """ % (key, key, key, key)
        
        # Componente invisível para callbacks
        callback_data = st.components.v1.html(callback_code, height=0, key=key)
        
        if callback_data and isinstance(callback_data, dict):
            action = callback_data.get('action')
            
            if action == 'firebase_auth_callback':
                status = callback_data.get('status')
                
                if status == 'signed_in':
                    user_data = callback_data.get('user')
                    if user_data:
                        # Salvar na sessão
                        st.session_state['firebase_user'] = user_data
                        st.session_state['auth_status'] = 'signed_in'
                        st.session_state['login_error'] = None
                        
                        # Salvar no cookie para persistência
                        self._save_auth_cookie(user_data)
                        
                        # Salvar no backend
                        self._save_user_to_backend(user_data)
                        
                        return True
                        
                elif status == 'error':
                    error = callback_data.get('error')
                    if error:
                        st.session_state['login_error'] = error
                        st.session_state['auth_status'] = 'error'
                    
                elif status == 'signed_out':
                    # Limpar dados de autenticação
                    st.session_state['firebase_user'] = None
                    st.session_state['auth_status'] = 'signed_out'
                    
                    # Limpar cookie
                    if self.cookie_manager_ready:
                        st.session_state.cookie_manager.delete(COOKIE_NAME)
                
                elif status == 'password_reset':
                    email = callback_data.get('email')
                    if email:
                        st.session_state['password_reset_email'] = email
                        st.session_state['auth_status'] = 'password_reset'
        
        # Verificar estado atual da autenticação
        return st.session_state.get('auth_status') == 'signed_in'
    
    def _save_user_to_backend(self, user_data):
        """
        Salva os dados do usuário no backend
        
        Args:
            user_data (dict): Dados do usuário
        
        Returns:
            bool: True se o usuário foi salvo com sucesso, False caso contrário
        """
        try:
            response = requests.post(
                f"{self.api_url}/api/salvar-usuario",
                json=user_data
            )
            
            if response.status_code in [200, 201]:
                return True
                
        except Exception as e:
            print(f"Erro ao salvar usuário no backend: {e}")
            
        return False
    
    def is_authenticated(self):
        """
        Verifica se o usuário está autenticado
        
        Returns:
            bool: True se autenticado, False caso contrário
        """
        return st.session_state.get('auth_status') == 'signed_in'
    
    def get_current_user(self):
        """
        Retorna os dados do usuário atual
        
        Returns:
            dict: Dados do usuário ou None se não autenticado
        """
        return st.session_state.get('firebase_user')
    
    def login_with_email(self, email, password):
        """
        Faz login com email e senha via JavaScript
        
        Args:
            email (str): Email do usuário
            password (str): Senha do usuário
        """
        js_code = f"""
        <script>
          window.parent.postMessage({{
            type: "streamlit:firebase:loginWithEmail",
            email: "{email}",
            password: "{password}"
          }}, "*");
        </script>
        """
        st.components.v1.html(js_code, height=0)
    
    def create_account(self, email, password):
        """
        Cria uma conta com email e senha via JavaScript
        
        Args:
            email (str): Email do usuário
            password (str): Senha do usuário
        """
        js_code = f"""
        <script>
          window.parent.postMessage({{
            type: "streamlit:firebase:createAccount",
            email: "{email}",
            password: "{password}"
          }}, "*");
        </script>
        """
        st.components.v1.html(js_code, height=0)
    
    def reset_password(self, email):
        """
        Envia email de redefinição de senha via JavaScript
        
        Args:
            email (str): Email do usuário
        """
        js_code = f"""
        <script>
          window.parent.postMessage({{
            type: "streamlit:firebase:resetPassword",
            email: "{email}"
          }}, "*");
        </script>
        """
        st.components.v1.html(js_code, height=0)
    
    def login_with_google(self):
        """Inicia login com Google via JavaScript"""
        js_code = """
        <script>
          window.parent.postMessage({
            type: "streamlit:firebase:loginWithGoogle"
          }, "*");
        </script>
        """
        st.components.v1.html(js_code, height=0)
    
    def login_with_facebook(self):
        """Inicia login com Facebook via JavaScript"""
        js_code = """
        <script>
          window.parent.postMessage({
            type: "streamlit:firebase:loginWithFacebook"
          }, "*");
        </script>
        """
        st.components.v1.html(js_code, height=0)
    
    def login_with_github(self):
        """Inicia login com GitHub via JavaScript"""
        js_code = """
        <script>
          window.parent.postMessage({
            type: "streamlit:firebase:loginWithGithub"
          }, "*");
        </script>
        """
        st.components.v1.html(js_code, height=0)
    
    def sign_out(self):
        """Faz logout do usuário via JavaScript"""
        js_code = """
        <script>
          window.parent.postMessage({
            type: "streamlit:firebase:signOut"
          }, "*");
        </script>
        """
        st.components.v1.html(js_code, height=0)
        
        # Limpar dados de sessão
        st.session_state['firebase_user'] = None
        st.session_state['auth_status'] = 'signed_out'
        
        # Limpar cookie
        if self.cookie_manager_ready:
            st.session_state.cookie_manager.delete(COOKIE_NAME)

# Criar uma instância global para uso simplificado
firebase_auth = FirebaseAuth()

# Funções auxiliares para uso simplificado
def is_authenticated():
    """Verifica se o usuário está autenticado"""
    return firebase_auth.is_authenticated()

def get_current_user():
    """Retorna os dados do usuário atual"""
    return firebase_auth.get_current_user()

def require_auth(page_func=None):
    """
    Decorador para exigir autenticação em uma página
    
    Uso:
        @require_auth
        def my_page():
            st.write("Conteúdo protegido")
    
    Ou:
        if require_auth():
            st.write("Conteúdo protegido")
    """
    # Verificar se o usuário está autenticado
    authenticated = firebase_auth.is_authenticated()
    
    # Processar callbacks de autenticação (necessário em cada página)
    firebase_auth.handle_auth_callback()
    
    # Se usado como verificador simples
    if page_func is None:
        return authenticated
    
    # Se usado como decorador
    def wrapper(*args, **kwargs):
        if authenticated:
            return page_func(*args, **kwargs)
        else:
            st.warning("Você precisa fazer login para acessar esta página.")
            st.stop()
    
    return wrapper

# Exemplo de uso:
# 
# import streamlit as st
# from utils.firebase_auth_streamlit import firebase_auth, require_auth
#
# def main():
#     st.title("Página de Login")
#     
#     # Inicializar gerenciador de cookies
#     from streamlit_cookies_manager import CookieManager
#     st.session_state.cookie_manager = CookieManager()
#     
#     # Verificar se já está autenticado
#     if firebase_auth.is_authenticated():
#         st.success("Você já está logado!")
#         st.write(f"Bem-vindo, {firebase_auth.get_current_user().get('nome')}")
#         
#         if st.button("Logout"):
#             firebase_auth.sign_out()
#             st.experimental_rerun()
#     else:
#         # Renderizar UI de login
#         firebase_auth.render_login_ui()
#         
#         # Formulário de login com email/senha
#         with st.form("login_form"):
#             email = st.text_input("Email")
#             password = st.text_input("Senha", type="password")
#             
#             col1, col2 = st.columns(2)
#             with col1:
#                 login_button = st.form_submit_button("Login")
#             with col2:
#                 create_button = st.form_submit_button("Criar Conta")
#                 
#         if login_button:
#             firebase_auth.login_with_email(email, password)
#         
#         if create_button:
#             firebase_auth.create_account(email, password)
#         
#         # Botões de login social
#         col1, col2, col3 = st.columns(3)
#         with col1:
#             if st.button("Login com Google"):
#                 firebase_auth.login_with_google()
#         with col2:
#             if st.button("Login com Facebook"):
#                 firebase_auth.login_with_facebook()
#         with col3:
#             if st.button("Login com GitHub"):
#                 firebase_auth.login_with_github()
#                 
#         # Link para resetar senha
#         reset_email = st.text_input("Email para resetar senha")
#         if st.button("Resetar Senha") and reset_email:
#             firebase_auth.reset_password(reset_email)
#     
#     # Processar callbacks
#     if firebase_auth.handle_auth_callback():
#         st.experimental_rerun()
#     
#     # Exibir erros
#     if st.session_state.get('login_error'):
#         st.error(f"Erro de login: {st.session_state.login_error}")
# 
# if __name__ == "__main__":
#     main()