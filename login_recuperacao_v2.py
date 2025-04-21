"""
Página de login moderna com funcionalidade de recuperação de senha
Esta versão usa diretamente o Firebase Authentication Web SDK (v9)
"""
import streamlit as st
import os
import json
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Login - Planner Organizer",
    page_icon="🔒",
    layout="centered"
)

# Inicializar variáveis de sessão
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "view" not in st.session_state:
    st.session_state.view = "login"  # login, signup, reset, success

# Estilos CSS
st.markdown("""
<style>
    .main-title {
        text-align: center;
        color: #2557D6;
        margin-bottom: 1rem;
    }
    
    .auth-container {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    
    .auth-tabs {
        margin-bottom: 1.5rem;
    }
    
    .auth-tabs button {
        background: none;
        border: none;
        padding: 0.5rem 1rem;
        cursor: pointer;
        border-bottom: 2px solid transparent;
        transition: all 0.3s;
        color: #5A6A85;
    }
    
    .auth-tabs button.active {
        color: #2557D6;
        border-bottom: 2px solid #2557D6;
    }
    
    .form-container {
        margin-top: 1rem;
    }
    
    .footer {
        text-align: center;
        margin-top: 2rem;
        color: #666;
        font-size: 0.8rem;
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

# Injetar scripts do Firebase
st.markdown("""
<!-- Firebase App (the core Firebase SDK) -->
<script src="https://www.gstatic.com/firebasejs/9.22.0/firebase-app.js" type="module"></script>
<script src="https://www.gstatic.com/firebasejs/9.22.0/firebase-auth.js" type="module"></script>

<script type="module">
  // Importar funções necessárias
  import { initializeApp } from "https://www.gstatic.com/firebasejs/9.22.0/firebase-app.js";
  import { 
    getAuth, 
    signInWithEmailAndPassword,
    createUserWithEmailAndPassword,
    sendPasswordResetEmail,
    sendEmailVerification,
    signOut
  } from "https://www.gstatic.com/firebasejs/9.22.0/firebase-auth.js";

  // Firebase configuration
  const firebaseConfig = {json.dumps(firebase_config)};

  // Initialize Firebase
  const app = initializeApp(firebaseConfig);
  const auth = getAuth(app);
  
  // Expor funções para uso global
  window.firebaseAuth = {
    login: async function(email, password) {
      try {
        const userCredential = await signInWithEmailAndPassword(auth, email, password);
        const user = userCredential.user;
        
        // Verificar se o email foi verificado
        if (user.emailVerified) {
          window.postMessage({
            type: "AUTH_SUCCESS",
            user: {
              uid: user.uid,
              email: user.email,
              emailVerified: user.emailVerified
            }
          }, "*");
          return true;
        } else {
          alert("Por favor, verifique seu email antes de fazer login.");
          return false;
        }
      } catch (error) {
        let message = "Erro ao fazer login.";
        if (error.code === 'auth/user-not-found') {
          message = "Email não encontrado. Crie uma conta primeiro.";
        } else if (error.code === 'auth/wrong-password') {
          message = "Senha incorreta. Tente novamente.";
        }
        alert(message);
        return false;
      }
    },
    
    signup: async function(email, password) {
      try {
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        const user = userCredential.user;
        
        // Enviar email de verificação
        await sendEmailVerification(user);
        alert("Conta criada com sucesso! Um email de verificação foi enviado para " + email);
        return true;
      } catch (error) {
        let message = "Erro ao criar conta.";
        if (error.code === 'auth/email-already-in-use') {
          message = "Este email já está em uso.";
        } else if (error.code === 'auth/invalid-email') {
          message = "Email inválido.";
        } else if (error.code === 'auth/weak-password') {
          message = "Senha muito fraca (mínimo 6 caracteres).";
        }
        alert(message);
        return false;
      }
    },
    
    resetPassword: async function(email) {
      try {
        await sendPasswordResetEmail(auth, email);
        alert("Email de recuperação de senha enviado para " + email);
        return true;
      } catch (error) {
        let message = "Erro ao enviar email de recuperação.";
        if (error.code === 'auth/user-not-found') {
          message = "Email não encontrado.";
        }
        alert(message);
        return false;
      }
    }
  };
  
  // Adicionar listener para mensagens do iframe
  window.addEventListener("message", function(event) {
    if (event.data && event.data.type === "AUTH_ACTION") {
      const { action, email, password } = event.data;
      
      if (action === "login") {
        window.firebaseAuth.login(email, password);
      } else if (action === "signup") {
        window.firebaseAuth.signup(email, password);
      } else if (action === "resetPassword") {
        window.firebaseAuth.resetPassword(email);
      }
    }
  });
  
  console.log("Firebase Auth inicializado");
</script>
""", unsafe_allow_html=True)

# Verificar parâmetros de autenticação na URL
query_params = st.query_params.to_dict()
if "auth_success" in query_params and query_params["auth_success"] == "true":
    if "uid" in query_params and "email" in query_params:
        uid = query_params["uid"]
        email = query_params["email"]
        
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

# JavaScript para interagir com o Firebase
st.markdown("""
<script>
  // Obter elementos após carregar o DOM
  document.addEventListener("DOMContentLoaded", function() {
    // Setup do formulário de login
    const loginForm = document.getElementById("login-form");
    if (loginForm) {
      loginForm.addEventListener("submit", function(e) {
        e.preventDefault();
        const email = document.getElementById("login-email").value;
        const password = document.getElementById("login-password").value;
        
        if (email && password) {
          window.firebaseAuth.login(email, password);
        } else {
          alert("Por favor, preencha todos os campos");
        }
      });
    }
    
    // Setup do formulário de cadastro
    const signupForm = document.getElementById("signup-form");
    if (signupForm) {
      signupForm.addEventListener("submit", function(e) {
        e.preventDefault();
        const email = document.getElementById("signup-email").value;
        const password = document.getElementById("signup-password").value;
        const confirmPassword = document.getElementById("signup-confirm-password").value;
        
        if (!email || !password) {
          alert("Email e senha são obrigatórios");
          return;
        }
        
        if (password !== confirmPassword) {
          alert("As senhas não coincidem");
          return;
        }
        
        if (password.length < 6) {
          alert("A senha deve ter pelo menos 6 caracteres");
          return;
        }
        
        window.firebaseAuth.signup(email, password);
      });
    }
    
    // Setup do formulário de recuperação de senha
    const resetForm = document.getElementById("reset-form");
    if (resetForm) {
      resetForm.addEventListener("submit", function(e) {
        e.preventDefault();
        const email = document.getElementById("reset-email").value;
        
        if (email) {
          window.firebaseAuth.resetPassword(email);
        } else {
          alert("Por favor, informe seu email");
        }
      });
    }
    
    // Listener para receber mensagem de autenticação bem-sucedida
    window.addEventListener("message", function(event) {
      if (event.data && event.data.type === "AUTH_SUCCESS") {
        const user = event.data.user;
        
        // Redirecionar com parâmetros
        let url = new URL(window.location.href);
        url.searchParams.set('auth_success', 'true');
        url.searchParams.set('uid', user.uid);
        url.searchParams.set('email', user.email);
        
        window.location.href = url.toString();
      }
    });
  });
</script>
""", unsafe_allow_html=True)

# Título principal
st.markdown("<h1 class='main-title'>Planner Organizer</h1>", unsafe_allow_html=True)

# Mostrar a visualização adequada
if st.session_state.authenticated:
    # Área autenticada
    st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
    st.success(f"Login realizado com sucesso como {st.session_state.user.get('email')}")
    
    # Informações do usuário
    st.write("### Dados do usuário")
    st.json(st.session_state.user)
    
    # Botões de ação
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Acessar o Sistema", key="access_button", use_container_width=True):
            st.switch_page("app.py")
    
    with col2:
        if st.button("Sair", key="logout_button", use_container_width=True):
            # Limpar dados da sessão
            st.session_state.authenticated = False
            st.session_state.user = None
            
            # Script para limpar localStorage
            st.markdown("""
            <script>
            localStorage.removeItem('firebase_user');
            </script>
            """, unsafe_allow_html=True)
            
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
else:
    # Interface de abas de autenticação
    st.markdown("""
    <div class="auth-container">
      <div class="auth-tabs">
        <button id="tab-login" class="active" onclick="switchTab('login')">Login</button>
        <button id="tab-signup" onclick="switchTab('signup')">Criar Conta</button>
        <button id="tab-reset" onclick="switchTab('reset')">Recuperar Senha</button>
      </div>
      
      <div id="form-login" class="form-container">
        <form id="login-form">
          <div style="margin-bottom: 1rem;">
            <label for="login-email">Email</label>
            <input type="email" id="login-email" name="email" placeholder="Seu email" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;" required>
          </div>
          
          <div style="margin-bottom: 1.5rem;">
            <label for="login-password">Senha</label>
            <input type="password" id="login-password" name="password" placeholder="Sua senha" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;" required>
          </div>
          
          <button type="submit" style="width: 100%; background-color: #2557D6; color: white; border: none; padding: 10px; border-radius: 4px; cursor: pointer;">
            Entrar
          </button>
          
          <div style="margin-top: 1rem; text-align: center;">
            <a href="#" onclick="switchTab('reset')" style="color: #2557D6; text-decoration: none; font-size: 0.9rem;">
              Esqueceu sua senha?
            </a>
          </div>
        </form>
      </div>
      
      <div id="form-signup" class="form-container" style="display: none;">
        <form id="signup-form">
          <div style="margin-bottom: 1rem;">
            <label for="signup-email">Email</label>
            <input type="email" id="signup-email" name="email" placeholder="Seu email" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;" required>
          </div>
          
          <div style="margin-bottom: 1rem;">
            <label for="signup-password">Senha</label>
            <input type="password" id="signup-password" name="password" placeholder="Mínimo 6 caracteres" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;" required>
          </div>
          
          <div style="margin-bottom: 1.5rem;">
            <label for="signup-confirm-password">Confirmar Senha</label>
            <input type="password" id="signup-confirm-password" name="confirm_password" placeholder="Digite a senha novamente" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;" required>
          </div>
          
          <button type="submit" style="width: 100%; background-color: #2557D6; color: white; border: none; padding: 10px; border-radius: 4px; cursor: pointer;">
            Criar Conta
          </button>
          
          <div style="margin-top: 1rem; text-align: center;">
            <a href="#" onclick="switchTab('login')" style="color: #2557D6; text-decoration: none; font-size: 0.9rem;">
              Já tem uma conta? Faça login
            </a>
          </div>
        </form>
      </div>
      
      <div id="form-reset" class="form-container" style="display: none;">
        <form id="reset-form">
          <div style="margin-bottom: 1rem;">
            <p style="margin-bottom: 1rem;">Informe seu email para receber um link de recuperação de senha.</p>
            <label for="reset-email">Email</label>
            <input type="email" id="reset-email" name="email" placeholder="Seu email cadastrado" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;" required>
          </div>
          
          <button type="submit" style="width: 100%; background-color: #2557D6; color: white; border: none; padding: 10px; border-radius: 4px; cursor: pointer;">
            Enviar Link de Recuperação
          </button>
          
          <div style="margin-top: 1rem; text-align: center;">
            <a href="#" onclick="switchTab('login')" style="color: #2557D6; text-decoration: none; font-size: 0.9rem;">
              Voltar para o login
            </a>
          </div>
        </form>
      </div>
    </div>
    
    <script>
      function switchTab(tab) {
        // Ocultar todos os formulários
        document.getElementById('form-login').style.display = 'none';
        document.getElementById('form-signup').style.display = 'none';
        document.getElementById('form-reset').style.display = 'none';
        
        // Desativar todas as abas
        document.getElementById('tab-login').classList.remove('active');
        document.getElementById('tab-signup').classList.remove('active');
        document.getElementById('tab-reset').classList.remove('active');
        
        // Mostrar o formulário selecionado
        document.getElementById('form-' + tab).style.display = 'block';
        
        // Ativar a aba selecionada
        document.getElementById('tab-' + tab).classList.add('active');
      }
    </script>
    """, unsafe_allow_html=True)

    # Informações para o modo de demonstração
    st.info("""
    **Modo de Demonstração**
    
    Para acessar o sistema sem criar uma conta, você pode usar:
    - Email: `demo@example.com`
    - Senha: `senha123`
    """)

    # Botão para modo de demonstração
    if st.button("Entrar como Demonstração", use_container_width=True):
        st.session_state.authenticated = True
        st.session_state.user = {
            "user_id": "demo-123",
            "email": "demo@example.com",
            "provider": "demo",
            "demo_mode": True,
            "login_time": datetime.now().isoformat()
        }
        st.rerun()

# Informações no rodapé
st.markdown("""
<div class="footer">
    <p>© 2025 Planner Organizer. Todos os direitos reservados.</p>
</div>
""", unsafe_allow_html=True)