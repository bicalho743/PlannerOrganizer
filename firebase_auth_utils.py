"""
Módulo de utilitários para autenticação com Firebase
Este módulo fornece funções que podem ser importadas em diferentes arquivos
"""
import os
import json
import streamlit as st

def get_firebase_config():
    """
    Obter configuração do Firebase das variáveis de ambiente ou secrets
    """
    firebase_api_key = os.environ.get("FIREBASE_API_KEY")
    if not firebase_api_key and hasattr(st, 'secrets'):
        firebase_api_key = st.secrets.get("FIREBASE_API_KEY", "")
    
    config = {
        "apiKey": firebase_api_key,
        "authDomain": "planner-organizer-68a23.firebaseapp.com",
        "projectId": "planner-organizer-68a23",
        "storageBucket": "planner-organizer-68a23.appspot.com",
        "messagingSenderId": "763383033284",
        "appId": "1:763383033284:web:5a5dc3b4d3f5bc63631ce7"
    }
    
    return config

def load_firebase_scripts():
    """
    Carrega os scripts do Firebase para a página
    """
    return """
    <!-- Firebase App (the core Firebase SDK) -->
    <script src="https://www.gstatic.com/firebasejs/9.22.0/firebase-app.js" type="module"></script>
    
    <!-- Firebase Authentication -->
    <script src="https://www.gstatic.com/firebasejs/9.22.0/firebase-auth.js" type="module"></script>
    """

def init_firebase_auth_js(config):
    """
    Código JavaScript para inicializar o Firebase Auth
    """
    return f"""
    <script type="module">
      // Import Firebase modules
      import {{ initializeApp }} from "https://www.gstatic.com/firebasejs/9.22.0/firebase-app.js";
      import {{ 
        getAuth, 
        signInWithEmailAndPassword,
        createUserWithEmailAndPassword,
        sendPasswordResetEmail,
        sendEmailVerification
      }} from "https://www.gstatic.com/firebasejs/9.22.0/firebase-auth.js";
      
      // Firebase configuration
      const firebaseConfig = {json.dumps(config)};
      
      // Initialize Firebase
      const app = initializeApp(firebaseConfig);
      const auth = getAuth(app);
      
      // Make auth available globally
      window.firebaseAuth = auth;
      
      // Login function
      window.loginWithEmail = async function(email, password) {{
        try {{
          const userCredential = await signInWithEmailAndPassword(auth, email, password);
          const user = userCredential.user;
          console.log("Login bem-sucedido:", user.email);
          
          // Set session data and redirect if email is verified
          if (user.emailVerified) {{
            window.setUserData(user);
            return true;
          }} else {{
            alert("Por favor verifique seu email antes de fazer login.");
            return false;
          }}
        }} catch (error) {{
          console.error("Erro de login:", error.code, error.message);
          let errorMessage = "Falha no login. Verifique suas credenciais.";
          
          if (error.code === 'auth/user-not-found') {{
            errorMessage = "Usuário não encontrado. Verifique seu email ou crie uma conta.";
          }} else if (error.code === 'auth/wrong-password') {{
            errorMessage = "Senha incorreta. Tente novamente ou use 'Esqueci minha senha'.";
          }}
          
          alert(errorMessage);
          return false;
        }}
      }};
      
      // Create account function
      window.createAccount = async function(email, password) {{
        try {{
          const userCredential = await createUserWithEmailAndPassword(auth, email, password);
          const user = userCredential.user;
          console.log("Conta criada:", user.email);
          
          // Send verification email
          try {{
            await sendEmailVerification(user);
            alert("Conta criada com sucesso! Um email de verificação foi enviado para " + email);
            return true;
          }} catch (verifyError) {{
            console.error("Erro ao enviar email de verificação:", verifyError);
            alert("Conta criada, mas houve um erro ao enviar o email de verificação.");
            return true;
          }}
        }} catch (error) {{
          console.error("Erro ao criar conta:", error.code, error.message);
          let errorMessage = "Falha ao criar conta.";
          
          if (error.code === 'auth/email-already-in-use') {{
            errorMessage = "Este email já está em uso. Tente fazer login ou recupere sua senha.";
          }}
          
          alert(errorMessage);
          return false;
        }}
      }};
      
      // Password reset function
      window.resetPassword = async function(email) {{
        try {{
          await sendPasswordResetEmail(auth, email);
          alert("Email de recuperação de senha enviado para " + email);
          return true;
        }} catch (error) {{
          console.error("Erro ao enviar email de recuperação:", error.code, error.message);
          
          let errorMessage = "Erro ao enviar email de recuperação.";
          if (error.code === 'auth/user-not-found') {{
            errorMessage = "Email não encontrado. Verifique o email ou crie uma conta.";
          }}
          
          alert(errorMessage);
          return false;
        }}
      }};
      
      // Set user data in session and localStorage
      window.setUserData = function(user) {{
        if (user) {{
          const userData = {{
            uid: user.uid,
            email: user.email,
            emailVerified: user.emailVerified,
            lastLogin: new Date().toISOString()
          }};
          
          // Save to localStorage
          localStorage.setItem('firebase_user', JSON.stringify(userData));
          
          // Redirect with auth params
          let url = new URL(window.location.href);
          url.searchParams.set('auth_success', 'true');
          url.searchParams.set('uid', user.uid);
          url.searchParams.set('email', user.email);
          
          console.log("Redirecionando após login para:", url.toString());
          window.location.href = url.toString();
        }}
      }};
      
      // Initialize listeners after document is ready
      document.addEventListener('DOMContentLoaded', function() {{
        console.log("Firebase Auth inicializado");
      }});
    </script>
    """

def get_login_js():
    """
    JavaScript para operações de login
    """
    return """
    <script>
      document.addEventListener('DOMContentLoaded', function() {
        // Login form
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
          loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const email = document.getElementById('login-email').value;
            const password = document.getElementById('login-password').value;
            
            if (email && password) {
              window.loginWithEmail(email, password);
            } else {
              alert("Por favor, preencha todos os campos.");
            }
          });
        }
        
        // Signup form
        const signupForm = document.getElementById('signup-form');
        if (signupForm) {
          signupForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const email = document.getElementById('signup-email').value;
            const password = document.getElementById('signup-password').value;
            const confirmPassword = document.getElementById('signup-confirm-password').value;
            
            if (!email || !password) {
              alert("Email e senha são obrigatórios.");
              return;
            }
            
            if (password !== confirmPassword) {
              alert("As senhas não coincidem.");
              return;
            }
            
            if (password.length < 6) {
              alert("A senha deve ter pelo menos 6 caracteres.");
              return;
            }
            
            window.createAccount(email, password);
          });
        }
        
        // Reset password form
        const resetForm = document.getElementById('reset-form');
        if (resetForm) {
          resetForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const email = document.getElementById('reset-email').value;
            
            if (email) {
              window.resetPassword(email);
            } else {
              alert("Por favor, informe seu email.");
            }
          });
        }
      });
    </script>
    """

def inject_firebase_auth(config=None):
    """
    Injeta todos os scripts do Firebase Auth na página
    """
    if config is None:
        config = get_firebase_config()
    
    scripts = load_firebase_scripts()
    scripts += init_firebase_auth_js(config)
    scripts += get_login_js()
    
    st.markdown(scripts, unsafe_allow_html=True)

def check_auth_from_url():
    """
    Verifica se há parâmetros de autenticação na URL
    """
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
            return True
    
    return False