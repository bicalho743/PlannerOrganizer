"""
Página de login simplificada com integração Firebase moderna
Este arquivo contém um login simplificado com Firebase usando o módulo v9 (importação ESM)
"""
import streamlit as st
import json
import os
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Planner Organizer - Login",
    page_icon="🗂️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Verificar se o usuário está autenticado
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Verificar parâmetros de URL para login Firebase
params = st.experimental_get_query_params()
if "login_success" in params and params["login_success"][0] == "true":
    if "uid" in params and "email" in params:
        # Login bem-sucedido via Firebase Auth UI
        uid = params["uid"][0]
        email = params["email"][0]
        
        st.session_state.authenticated = True
        st.session_state.user = {
            'user_id': uid,
            'email': email,
            'provider': 'firebase',
            'login_time': datetime.now().isoformat()
        }
        
        # Verificar status da assinatura (simplificado para demonstração)
        st.session_state.subscription = {"status": "active", "demo_mode": True}
        
        # Limpar parâmetros da URL
        st.experimental_set_query_params()
        st.rerun()

# Configuração do Firebase
firebase_config = {
    "apiKey": os.environ.get("FIREBASE_API_KEY", st.secrets.get("FIREBASE_API_KEY", "")),
    "authDomain": "planner-organizer-68a23.firebaseapp.com",
    "projectId": "planner-organizer-68a23",
    "storageBucket": "planner-organizer-68a23.appspot.com",
    "messagingSenderId": "763383033284",
    "appId": "1:763383033284:web:5a5dc3b4d3f5bc63631ce7",
    "measurementId": "G-XQP8M2ZKHZ"
}

# Conteúdo principal
if not st.session_state.authenticated:
    # Remover cabeçalho e rodapé do Streamlit
    st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)
    
    # Scripts do Firebase
    st.markdown("""
    <script src="https://www.gstatic.com/firebasejs/8.10.0/firebase-app.js"></script>
    <script src="https://www.gstatic.com/firebasejs/8.10.0/firebase-auth.js"></script>
    """, unsafe_allow_html=True)
    
    # Script para carregar o módulo de autenticação do Firebase
    st.markdown("""
    <script>
    // Função para carregar script externo
    function loadExternalScript(src) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.onload = resolve;
            script.onerror = reject;
            document.body.appendChild(script);
        });
    }
    
    // Carregar nosso módulo personalizado
    document.addEventListener('DOMContentLoaded', function() {
        loadExternalScript('/utils/firebase_module.js')
            .then(() => console.log('Módulo Firebase carregado'))
            .catch(error => console.error('Erro ao carregar módulo Firebase:', error));
    });
    </script>
    """, unsafe_allow_html=True)
    
    # Inicialização do Firebase
    st.markdown(f"""
    <script>
    // Configuração do Firebase
    const firebaseConfig = {json.dumps(firebase_config)};
    
    // Inicializar quando o DOM estiver carregado
    document.addEventListener('DOMContentLoaded', function() {{
        setTimeout(function() {{
            if (window.firebaseAuthModule) {{
                // Inicializar Firebase
                const {{ auth, googleProvider, facebookProvider }} = 
                    window.firebaseAuthModule.initializeFirebase(firebaseConfig);
                    
                // Verificar autenticação existente
                const userData = window.firebaseAuthModule.checkUserAuthentication();
                if (userData) {{
                    console.log('Usuário já autenticado:', userData.email);
                    window.firebaseAuthModule.redirectAfterAuth(userData);
                }}
                
                // Configurar botões
                setupLoginButtons(auth, googleProvider, facebookProvider);
            }}
        }}, 1000); // Pequeno delay para garantir que o módulo esteja carregado
    }});
    
    // Configurar botões de login
    function setupLoginButtons(auth, googleProvider, facebookProvider) {{
        // Google Sign In
        const googleBtn = document.getElementById('googleLoginBtn');
        if (googleBtn) {{
            googleBtn.addEventListener('click', function(e) {{
                e.preventDefault();
                window.firebaseAuthModule.signInWithGoogle(auth, googleProvider)
                    .then(result => {{
                        if (result.success) {{
                            window.firebaseAuthModule.saveUserToLocalStorage(result);
                            window.firebaseAuthModule.redirectAfterAuth(result);
                        }} else {{
                            alert('Erro ao fazer login com Google: ' + result.errorMessage);
                        }}
                    }});
            }});
        }}
        
        // Facebook Sign In
        const fbBtn = document.getElementById('facebookLoginBtn');
        if (fbBtn) {{
            fbBtn.addEventListener('click', function(e) {{
                e.preventDefault();
                window.firebaseAuthModule.signInWithFacebook(auth, facebookProvider)
                    .then(result => {{
                        if (result.success) {{
                            window.firebaseAuthModule.saveUserToLocalStorage(result);
                            window.firebaseAuthModule.redirectAfterAuth(result);
                        }} else {{
                            alert('Erro ao fazer login com Facebook: ' + result.errorMessage);
                        }}
                    }});
            }});
        }}
    }}
    </script>
    """, unsafe_allow_html=True)

    # Título da página
    st.title("🗂️ Planner Organizer")
    st.subheader("Organize seus projetos")
    
    # Login com redes sociais
    st.markdown("""
    <button id="googleLoginBtn" class="social-button" style="background-color: white; color: #444; border: 1px solid #ddd; 
                 border-radius: 5px; padding: 10px; display: flex; align-items: center; width: 100%; margin-bottom: 10px; cursor: pointer;">
        <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" 
             style="width: 18px; height: 18px; margin-right: 8px;">
        Continuar com Google
    </button>
    
    <button id="facebookLoginBtn" class="social-button" style="background-color: #3b5998; color: white; border: none; 
                 border-radius: 5px; padding: 10px; display: flex; align-items: center; width: 100%; margin-bottom: 10px; cursor: pointer;">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="white" 
             style="margin-right: 8px;">
            <path d="M12 0c-6.627 0-12 5.373-12 12s5.373 12 12 12 12-5.373 12-12-5.373-12-12-12zm3 8h-1.35c-.538 0-.65.221-.65.778v1.222h2l-.209 2h-1.791v7h-3v-7h-2v-2h2v-2.308c0-1.769.931-2.692 3.029-2.692h1.971v3z"/>
        </svg>
        Continuar com Facebook
    </button>
    
    <div style="text-align: center; margin: 20px 0; position: relative;">
        <hr style="margin: 0; position: absolute; top: 50%; width: 100%; border-top: 1px solid #ddd;">
        <span style="background-color: white; position: relative; padding: 0 10px; color: #777;">ou</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Login com email e senha
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("Email")
        password = st.text_input("Senha", type="password")
        login_button = st.form_submit_button("Entrar", use_container_width=True)
        
        if login_button:
            # Para demonstração, aceitamos admin/admin
            if email.lower() == "admin" and password == "admin":
                st.session_state.authenticated = True
                st.session_state.user = {
                    'user_id': 'demo-user',
                    'email': 'admin@example.com',
                    'demo_mode': True
                }
                st.rerun()
            else:
                st.error("Email ou senha inválidos")
    
    # Links para cadastro e recuperação de senha
    col1, col2 = st.columns(2)
    with col1:
        st.write("[Esqueceu a senha?](#)")
    with col2:
        st.write("[Criar uma conta](#)")

# Página após login
else:
    st.title(f"Bem-vindo, {st.session_state.user.get('email')}")
    st.success("Login realizado com sucesso!")
    
    if st.button("Sair"):
        # Limpar sessão
        st.session_state.clear()
        st.rerun()
    
    # Link para a aplicação principal
    st.markdown("[Ir para o Dashboard](/)")

if __name__ == "__main__":
    # O código já está executando
    pass