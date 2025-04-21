"""
Página de login simplificada usando Firebase Auth
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

# Título da página
st.title("Login - Planner Organizer")

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
            "provider": "firebase",
            "login_time": datetime.now().isoformat()
        }
        
        # Limpar parâmetros da URL
        st.query_params.clear()
        st.rerun()

# Tela de login
if not st.session_state.authenticated:
    # Carregar o módulo Firebase
    st.markdown("""
    <script src="https://www.gstatic.com/firebasejs/8.10.0/firebase-app.js"></script>
    <script src="https://www.gstatic.com/firebasejs/8.10.0/firebase-auth.js"></script>
    <script src="/public/js/firebase-simple-auth.js"></script>
    """, unsafe_allow_html=True)
    
    # Inicializar Firebase
    st.markdown(f"""
    <script>
    // Inicializar quando a página carregar
    document.addEventListener('DOMContentLoaded', function() {{
        console.log('Inicializando Firebase Auth...');
        
        // Configuração do Firebase
        const firebaseConfig = {json.dumps(firebase_config)};
        
        // Inicializar
        if (window.firebaseSimpleAuth) {{
            const success = window.firebaseSimpleAuth.init(firebaseConfig);
            if (success) {{
                console.log('Firebase Auth inicializado com sucesso');
                
                // Verificar autenticação existente
                const user = window.firebaseSimpleAuth.checkExistingAuth();
                if (user) {{
                    console.log('Usuário já autenticado:', user.email);
                    window.firebaseSimpleAuth.redirectAfterLogin(user);
                }} else {{
                    console.log('Nenhum usuário autenticado encontrado');
                    
                    // Configurar botões de login
                    window.firebaseSimpleAuth.setupLoginButtons();
                }}
            }} else {{
                console.error('Falha ao inicializar Firebase Auth');
            }}
        }} else {{
            console.error('Módulo Firebase Simple Auth não encontrado');
        }}
    }});
    </script>
    """, unsafe_allow_html=True)
    
    # Interface de login
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <h2 style="text-align: center; margin-bottom: 20px;">Entrar no Sistema</h2>
        
        <button id="googleLoginBtn" style="
            width: 100%;
            padding: 10px;
            margin-bottom: 10px;
            background-color: white;
            color: #444;
            border: 1px solid #ddd;
            border-radius: 5px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
        ">
            <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" 
                 style="width: 18px; height: 18px; margin-right: 8px;">
            Continuar com Google
        </button>
        
        <button id="facebookLoginBtn" style="
            width: 100%;
            padding: 10px;
            margin-bottom: 10px;
            background-color: #3b5998;
            color: white;
            border: none;
            border-radius: 5px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
        ">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="white" 
                 style="margin-right: 8px;">
                <path d="M12 0c-6.627 0-12 5.373-12 12s5.373 12 12 12 12-5.373 12-12-5.373-12-12-12zm3 8h-1.35c-.538 0-.65.221-.65.778v1.222h2l-.209 2h-1.791v7h-3v-7h-2v-2h2v-2.308c0-1.769.931-2.692 3.029-2.692h1.971v3z"/>
            </svg>
            Continuar com Facebook
        </button>
    </div>
    
    <div style="text-align: center; margin-top: 20px;">
        <p>OU</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Formulário de login tradicional
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")
        
        if submit:
            if email.lower() == "admin" and password == "admin":
                st.session_state.authenticated = True
                st.session_state.user = {
                    'user_id': 'admin-demo',
                    'email': 'admin@example.com',
                    'demo_mode': True
                }
                st.success("Login realizado com sucesso (modo de demonstração)!")
                st.rerun()
            else:
                st.error("Email ou senha inválidos")
    
    # Interface para recuperação de senha
    st.markdown("<h3 style='text-align: center; margin-top: 30px;'>Esqueceu sua senha?</h3>", unsafe_allow_html=True)
    
    # Campo para email e botão de recuperação
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-top: 10px;">
        <p style="margin-bottom: 15px;">Digite seu email abaixo para receber instruções de recuperação de senha:</p>
        <div style="display: flex; margin-bottom: 10px;">
            <input type="email" id="resetPasswordEmail" placeholder="Seu email" style="
                flex: 1;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-right: 10px;
            ">
            <button id="resetPasswordBtn" style="
                padding: 10px 15px;
                background-color: #1976D2;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            ">Recuperar</button>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Link para criar conta
    st.markdown("""
    <div style="text-align: center; margin-top: 20px;">
        <p>Não tem uma conta? <a href="/cadastro" style="color: #1976D2; text-decoration: none;">Criar conta</a></p>
    </div>
    """, unsafe_allow_html=True)
else:
    # Tela após login
    st.success(f"Login realizado com sucesso como {st.session_state.user.get('email')}!")
    
    # Exibir informações do usuário
    st.write("### Dados do usuário")
    st.json(st.session_state.user)
    
    # Botão para sair
    if st.button("Sair"):
        # Limpar sessão
        st.session_state.authenticated = False
        if 'user' in st.session_state:
            del st.session_state.user
        
        # Limpar localStorage via JavaScript
        st.markdown("""
        <script>
        localStorage.removeItem('firebase_user');
        </script>
        """, unsafe_allow_html=True)
        
        st.rerun()