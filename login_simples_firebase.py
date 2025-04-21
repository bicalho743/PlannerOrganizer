import streamlit as st
import os
import json
from datetime import datetime

st.set_page_config(
    page_title="Login Firebase Simples",
    page_icon="🔑",
    layout="centered"
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

# Tela de login
if not st.session_state.authenticated:
    st.title("Login com Firebase")
    
    # Adicionar Firebase SDK
    st.markdown("""
    <script src="https://www.gstatic.com/firebasejs/8.10.0/firebase-app.js"></script>
    <script src="https://www.gstatic.com/firebasejs/8.10.0/firebase-auth.js"></script>
    """, unsafe_allow_html=True)
    
    # Código de inicialização do Firebase
    st.markdown(f"""
    <script>
    // Configuração do Firebase
    const firebaseConfig = {json.dumps(firebase_config)};
    
    // Inicializar Firebase
    if (!firebase.apps.length) {{
        firebase.initializeApp(firebaseConfig);
        console.log("Firebase inicializado");
    }}
    
    // Função para login com Google
    function loginWithGoogle() {{
        console.log("Iniciando login com Google...");
        const provider = new firebase.auth.GoogleAuthProvider();
        
        firebase.auth()
            .signInWithPopup(provider)
            .then((result) => {{
                const user = result.user;
                console.log("Login com Google bem-sucedido:", user.email);
                
                // Salvar no localStorage para persistência
                localStorage.setItem('firebase_user', JSON.stringify({{
                    uid: user.uid,
                    email: user.email,
                    displayName: user.displayName
                }}));
                
                // Redirecionar com parâmetros
                const url = new URL(window.location.href);
                url.searchParams.set('login_success', 'true');
                url.searchParams.set('uid', user.uid);
                url.searchParams.set('email', user.email);
                window.location.href = url.toString();
            }})
            .catch((error) => {{
                console.error("Erro no login com Google:", error);
                alert("Erro ao fazer login: " + error.message);
            }});
    }}
    
    // Função para login com Facebook
    function loginWithFacebook() {{
        console.log("Iniciando login com Facebook...");
        const provider = new firebase.auth.FacebookAuthProvider();
        
        firebase.auth()
            .signInWithPopup(provider)
            .then((result) => {{
                const user = result.user;
                console.log("Login com Facebook bem-sucedido:", user.email);
                
                // Salvar no localStorage para persistência
                localStorage.setItem('firebase_user', JSON.stringify({{
                    uid: user.uid,
                    email: user.email,
                    displayName: user.displayName
                }}));
                
                // Redirecionar com parâmetros
                const url = new URL(window.location.href);
                url.searchParams.set('login_success', 'true');
                url.searchParams.set('uid', user.uid);
                url.searchParams.set('email', user.email);
                window.location.href = url.toString();
            }})
            .catch((error) => {{
                console.error("Erro no login com Facebook:", error);
                alert("Erro ao fazer login: " + error.message);
            }});
    }}
    
    // Verificar se o usuário já está autenticado
    function checkExistingAuth() {{
        const userData = localStorage.getItem('firebase_user');
        if (userData) {{
            try {{
                const user = JSON.parse(userData);
                console.log("Usuário já autenticado:", user.email);
                
                // Redirecionar se necessário
                const url = new URL(window.location.href);
                if (!url.searchParams.has('login_success')) {{
                    url.searchParams.set('login_success', 'true');
                    url.searchParams.set('uid', user.uid);
                    url.searchParams.set('email', user.email);
                    window.location.href = url.toString();
                }}
            }} catch (e) {{
                console.error("Erro ao processar dados do localStorage:", e);
                localStorage.removeItem('firebase_user');
            }}
        }}
    }}
    
    // Executar quando a página carregar
    document.addEventListener('DOMContentLoaded', function() {{
        checkExistingAuth();
        
        // Configurar botões de login
        setTimeout(function() {{
            const googleBtn = document.getElementById('googleLoginBtn');
            if (googleBtn) {{
                googleBtn.addEventListener('click', function(e) {{
                    e.preventDefault();
                    loginWithGoogle();
                }});
                console.log("Event listener adicionado ao botão Google");
            }}
            
            const fbBtn = document.getElementById('facebookLoginBtn');
            if (fbBtn) {{
                fbBtn.addEventListener('click', function(e) {{
                    e.preventDefault();
                    loginWithFacebook();
                }});
                console.log("Event listener adicionado ao botão Facebook");
            }}
        }}, 500);
    }});
    </script>
    """, unsafe_allow_html=True)
    
    # Botões de login
    st.markdown("""
    <button id="googleLoginBtn" style="background-color: white; color: #444; border: 1px solid #ddd; 
                border-radius: 5px; padding: 10px; display: flex; align-items: center; 
                width: 100%; margin-bottom: 10px; cursor: pointer;">
        <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" 
             style="width: 18px; height: 18px; margin-right: 8px;">
        Continuar com Google
    </button>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <button id="facebookLoginBtn" style="background-color: #3b5998; color: white; border: none; 
                border-radius: 5px; padding: 10px; display: flex; align-items: center; 
                width: 100%; margin-bottom: 10px; cursor: pointer;">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="white" 
             style="margin-right: 8px;">
            <path d="M12 0c-6.627 0-12 5.373-12 12s5.373 12 12 12 12-5.373 12-12-5.373-12-12-12zm3 8h-1.35c-.538 0-.65.221-.65.778v1.222h2l-.209 2h-1.791v7h-3v-7h-2v-2h2v-2.308c0-1.769.931-2.692 3.029-2.692h1.971v3z"/>
        </svg>
        Continuar com Facebook
    </button>
    """, unsafe_allow_html=True)
    
    # Verificar parâmetros de login
    params = st.experimental_get_query_params()
    if "login_success" in params and params["login_success"][0] == "true":
        if "uid" in params and "email" in params:
            uid = params["uid"][0]
            email = params["email"][0]
            
            st.session_state.authenticated = True
            st.session_state.user = {
                'user_id': uid,
                'email': email,
                'provider': 'firebase',
                'login_time': datetime.now().isoformat()
            }
            
            # Limpar parâmetros da URL
            st.experimental_set_query_params()
            st.rerun()
    
    # Login tradicional
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Senha", type="password")
        login_button = st.form_submit_button("Entrar")
        
        if login_button:
            if email.lower() == "admin" and password == "admin":
                st.session_state.authenticated = True
                st.session_state.user = {
                    'user_id': 'demo-user',
                    'email': email,
                    'demo_mode': True
                }
                st.rerun()
            else:
                st.error("Email ou senha inválidos")

# Tela pós-login
else:
    st.title(f"Bem-vindo, {st.session_state.user.get('email')}")
    st.write("Login realizado com sucesso!")
    
    if st.button("Sair"):
        # Limpar dados de sessão
        st.session_state.clear()
        
        # Limpar localStorage via JavaScript
        st.markdown("""
        <script>
        localStorage.removeItem('firebase_user');
        </script>
        """, unsafe_allow_html=True)
        
        st.rerun()