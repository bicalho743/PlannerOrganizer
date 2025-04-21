"""
Página de login simplificada com integração Firebase moderna
Este arquivo contém um login simplificado com Firebase usando o módulo v9 (importação ESM)
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

# Esconder o menu e rodapé do Streamlit
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Inicializar estado da sessão
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    
if "user" not in st.session_state:
    st.session_state.user = None

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
query_params = st.experimental_get_query_params()
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
        st.experimental_set_query_params()
        st.rerun()

# Título da página
st.markdown("<h1 style='text-align: center; margin-bottom: 30px; font-size: 2.5rem; color: #2d8cff;'>Planner Organizer</h1>", unsafe_allow_html=True)

# Subtítulo
st.markdown("<h3 style='text-align: center; margin-bottom: 30px; color: #5A6A85;'>Entre para acessar sua conta</h3>", unsafe_allow_html=True)

# Layout de duas colunas
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### Recursos Principais")
    st.markdown("""
    <ul style='list-style-type: none; padding-left: 0;'>
        <li style='margin-bottom: 10px;'>✓ Gestão completa de propostas</li>
        <li style='margin-bottom: 10px;'>✓ Controle de clientes</li>
        <li style='margin-bottom: 10px;'>✓ Monitoramento financeiro</li>
        <li style='margin-bottom: 10px;'>✓ Relatórios personalizados</li>
        <li style='margin-bottom: 10px;'>✓ Acesso em qualquer lugar</li>
    </ul>
    """, unsafe_allow_html=True)

with col2:
    # Tela de login
    if not st.session_state.authenticated:
        # Carregar SDK do Firebase e nosso módulo personalizado
        st.markdown("""
        <script src="https://www.gstatic.com/firebasejs/8.10.0/firebase-app.js"></script>
        <script src="https://www.gstatic.com/firebasejs/8.10.0/firebase-auth.js"></script>
        """, unsafe_allow_html=True)
        
        # Script para inicializar Firebase e configurar botões
        st.markdown(f"""
        <script>
        // Módulo de autenticação Firebase simplificado
        const firebaseAuth = {{
            // Firebase referencias
            app: null,
            auth: null,
            
            // Providers
            googleProvider: null,
            facebookProvider: null,
            
            // Inicializar Firebase
            init: function(config) {{
                try {{
                    console.log("Inicializando Firebase Auth...");
                    
                    // Inicializar Firebase
                    if (!firebase.apps.length) {{
                        this.app = firebase.initializeApp(config);
                    }} else {{
                        this.app = firebase.app();
                    }}
                    
                    // Obter auth
                    this.auth = firebase.auth();
                    
                    // Configurar providers
                    this.googleProvider = new firebase.auth.GoogleAuthProvider();
                    this.facebookProvider = new firebase.auth.FacebookAuthProvider();
                    
                    // Configurar opções
                    this.googleProvider.setCustomParameters({{
                        prompt: 'select_account'
                    }});
                    
                    console.log("Firebase inicializado com sucesso");
                    return true;
                }} catch (error) {{
                    console.error("Erro ao inicializar Firebase:", error);
                    return false;
                }}
            }},
            
            // Login com Google
            loginWithGoogle: function() {{
                console.log("Iniciando login com Google...");
                this.auth.signInWithPopup(this.googleProvider)
                    .then(result => {{
                        console.log("Login com Google bem-sucedido:", result.user.email);
                        this.handleAuthSuccess(result.user);
                    }})
                    .catch(error => {{
                        console.error("Erro no login com Google:", error);
                        alert("Erro ao fazer login com Google: " + error.message);
                    }});
            }},
            
            // Login com Facebook
            loginWithFacebook: function() {{
                console.log("Iniciando login com Facebook...");
                this.auth.signInWithPopup(this.facebookProvider)
                    .then(result => {{
                        console.log("Login com Facebook bem-sucedido:", result.user.email);
                        this.handleAuthSuccess(result.user);
                    }})
                    .catch(error => {{
                        console.error("Erro no login com Facebook:", error);
                        alert("Erro ao fazer login com Facebook: " + error.message);
                    }});
            }},
            
            // Processar autenticação bem-sucedida
            handleAuthSuccess: function(user) {{
                // Salvar dados no localStorage
                user.getIdToken().then(idToken => {{
                    const userData = {{
                        uid: user.uid,
                        email: user.email,
                        displayName: user.displayName || user.email,
                        photoURL: user.photoURL,
                        idToken: idToken,
                        lastLogin: new Date().toISOString()
                    }};
                    
                    localStorage.setItem('firebase_user', JSON.stringify(userData));
                    
                    // Redirecionar com parâmetros
                    const url = new URL(window.location.href);
                    url.searchParams.set('auth_success', 'true');
                    url.searchParams.set('uid', user.uid);
                    url.searchParams.set('email', encodeURIComponent(user.email));
                    
                    // Redirecionar
                    window.location.href = url.toString();
                }});
            }},
            
            // Configurar event listeners
            setupButtons: function() {{
                console.log("Configurando botões de login...");
                
                // Google login
                const googleBtn = document.getElementById('googleLoginBtn');
                if (googleBtn) {{
                    googleBtn.addEventListener('click', e => {{
                        e.preventDefault();
                        this.loginWithGoogle();
                    }});
                    console.log("Botão do Google configurado");
                }}
                
                // Facebook login
                const fbBtn = document.getElementById('facebookLoginBtn');
                if (fbBtn) {{
                    fbBtn.addEventListener('click', e => {{
                        e.preventDefault();
                        this.loginWithFacebook();
                    }});
                    console.log("Botão do Facebook configurado");
                }}
            }}
        }};

        // Inicializar quando a página carregar
        document.addEventListener('DOMContentLoaded', function() {{
            console.log("DOM carregado, inicializando Firebase...");
            const firebaseConfig = {json.dumps(firebase_config)};
            
            // Inicializar Firebase
            setTimeout(() => {{
                const success = firebaseAuth.init(firebaseConfig);
                if (success) {{
                    firebaseAuth.setupButtons();
                }}
            }}, 1000);
        }});
        </script>
        """, unsafe_allow_html=True)
        
        # Container de login estilizado
        st.markdown("""
        <div style="background-color: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <h3 style="text-align: center; margin-bottom: 20px; color: #333;">Acesse sua conta</h3>
            
            <button id="googleLoginBtn" style="
                width: 100%;
                padding: 10px 15px;
                margin-bottom: 12px;
                background-color: white;
                color: #444;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 15px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s ease;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            ">
                <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" 
                     style="width: 18px; height: 18px; margin-right: 10px;">
                Continuar com Google
            </button>
            
            <button id="facebookLoginBtn" style="
                width: 100%;
                padding: 10px 15px;
                margin-bottom: 12px;
                background-color: #3b5998;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 15px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s ease;
                box-shadow: 0 2px 4px rgba(59,89,152,0.3);
            ">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="white" 
                     style="margin-right: 10px;">
                    <path d="M12 0c-6.627 0-12 5.373-12 12s5.373 12 12 12 12-5.373 12-12-5.373-12-12-12zm3 8h-1.35c-.538 0-.65.221-.65.778v1.222h2l-.209 2h-1.791v7h-3v-7h-2v-2h2v-2.308c0-1.769.931-2.692 3.029-2.692h1.971v3z"/>
                </svg>
                Continuar com Facebook
            </button>
            
            <div style="text-align: center; margin: 15px 0; color: #777; position: relative;">
                <span style="background-color: white; padding: 0 10px; position: relative; z-index: 1;">ou</span>
                <div style="border-top: 1px solid #ddd; position: absolute; top: 50%; left: 0; right: 0; z-index: 0;"></div>
            </div>
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
        
        # Link para criar conta
        st.markdown("""
        <div style="text-align: center; margin-top: 20px;">
            <p>Não tem uma conta? <a href="/cadastro" style="color: #1976D2; text-decoration: none; font-weight: 500;">Criar conta</a></p>
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

# Rodapé
st.markdown("""
<div style="text-align: center; margin-top: 50px; padding-top: 20px; border-top: 1px solid #eee; color: #777; font-size: 14px;">
    © 2025 Planner Organizer. Todos os direitos reservados.
</div>
""", unsafe_allow_html=True)