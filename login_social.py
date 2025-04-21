import streamlit as st
import os
import json
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Login - Planner Organizer",
    page_icon="🔑",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Esconder elementos do Streamlit
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Inicializar sessão
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user" not in st.session_state:
    st.session_state.user = None

# Configuração do Firebase
firebase_config = {
    "apiKey": os.environ.get("FIREBASE_API_KEY", "AIzaSyDNvFRG_LcmnrQlvGzHx5_dR16vCUTp13I"),
    "authDomain": "planner-organizer-68a23.firebaseapp.com",
    "projectId": "planner-organizer-68a23",
    "storageBucket": "planner-organizer-68a23.appspot.com",
    "messagingSenderId": "763383033284",
    "appId": "1:763383033284:web:5a5dc3b4d3f5bc63631ce7"
}

# Verificar parâmetros de URL para autenticação
params = dict(st.query_params)
if "auth_success" in params and params["auth_success"] == "true":
    if "uid" in params and "email" in params:
        uid = params["uid"]
        email = params["email"]

        # Salvar na sessão
        st.session_state.authenticated = True
        st.session_state.user = {
            "uid": uid,
            "email": email,
            "login_time": datetime.now().isoformat()
        }

        # Limpar parâmetros
        st.query_params.clear()
        st.rerun()

# Título principal
st.title("Login - Planner Organizer")

# Se não estiver autenticado, mostrar tela de login
if not st.session_state.authenticated:
    # Carregar bibliotecas do Firebase (versão 9)
    st.markdown("""
    <script type="module">
    // Importar Firebase V9 (modular)
    import { initializeApp } from "https://www.gstatic.com/firebasejs/9.22.0/firebase-app.js";
    import { 
        getAuth, 
        signInWithPopup, 
        GoogleAuthProvider, 
        FacebookAuthProvider,
        signInWithEmailAndPassword 
    } from "https://www.gstatic.com/firebasejs/9.22.0/firebase-auth.js";

    // Configuração do Firebase
    const firebaseConfig = {
        apiKey: "AIzaSyDNvFRG_LcmnrQlvGzHx5_dR16vCUTp13I",
        authDomain: "planner-organizer-68a23.firebaseapp.com",
        projectId: "planner-organizer-68a23",
        storageBucket: "planner-organizer-68a23.appspot.com",
        messagingSenderId: "763383033284",
        appId: "1:763383033284:web:5a5dc3b4d3f5bc63631ce7"
    };

    // Inicializar Firebase
    const app = initializeApp(firebaseConfig);
    const auth = getAuth(app);
    const googleProvider = new GoogleAuthProvider();
    const facebookProvider = new FacebookAuthProvider();

    // Função para login com Google
    window.loginWithGoogle = async function() {
        console.log("Iniciando login com Google...");
        try {
            // Adicionar escopo para perfil e email
            googleProvider.addScope('profile');
            googleProvider.addScope('email');
            
            // Parâmetros adicionais para o pop-up
            googleProvider.setCustomParameters({
                'prompt': 'select_account',
                'login_hint': 'user@example.com'
            });
            
            // Iniciar pop-up
            const result = await signInWithPopup(auth, googleProvider);
            const user = result.user;
            console.log("Login com Google bem-sucedido:", user.email);
            
            // Obter token
            const token = await user.getIdToken();
            
            // Redirecionar com parâmetros
            const url = new URL(window.location.href);
            url.searchParams.set('auth_success', 'true');
            url.searchParams.set('uid', user.uid);
            url.searchParams.set('email', user.email);
            
            // Salvar no localStorage
            localStorage.setItem('firebase_user', JSON.stringify({
                uid: user.uid,
                email: user.email,
                token: token,
                provider: 'google'
            }));
            
            // Redirecionar
            window.location.href = url.toString();
        } catch (error) {
            console.error("Erro no login com Google:", error);
            
            if (error.code === 'auth/popup-blocked') {
                alert("O pop-up foi bloqueado pelo navegador. Por favor, permita pop-ups para este site e tente novamente.");
            } else if (error.code === 'auth/popup-closed-by-user') {
                console.log("Pop-up fechado pelo usuário");
            } else {
                alert("Erro no login com Google: " + error.message);
            }
        }
    };

    // Função para login com Facebook
    window.loginWithFacebook = async function() {
        console.log("Iniciando login com Facebook...");
        try {
            const result = await signInWithPopup(auth, facebookProvider);
            const user = result.user;
            console.log("Login com Facebook bem-sucedido:", user.email);
            
            // Obter token
            const token = await user.getIdToken();
            
            // Redirecionar com parâmetros
            const url = new URL(window.location.href);
            url.searchParams.set('auth_success', 'true');
            url.searchParams.set('uid', user.uid);
            url.searchParams.set('email', user.email);
            
            // Salvar no localStorage
            localStorage.setItem('firebase_user', JSON.stringify({
                uid: user.uid,
                email: user.email,
                token: token,
                provider: 'facebook'
            }));
            
            // Redirecionar
            window.location.href = url.toString();
        } catch (error) {
            console.error("Erro no login com Facebook:", error);
            
            if (error.code === 'auth/popup-blocked') {
                alert("O pop-up foi bloqueado pelo navegador. Por favor, permita pop-ups para este site e tente novamente.");
            } else if (error.code === 'auth/popup-closed-by-user') {
                console.log("Pop-up fechado pelo usuário");
            } else {
                alert("Erro no login com Facebook: " + error.message);
            }
        }
    };

    // Função para login com email e senha
    window.loginWithEmail = async function(email, password) {
        console.log("Iniciando login com email e senha...");
        try {
            const result = await signInWithEmailAndPassword(auth, email, password);
            const user = result.user;
            console.log("Login com email bem-sucedido:", user.email);
            
            // Obter token
            const token = await user.getIdToken();
            
            // Redirecionar com parâmetros
            const url = new URL(window.location.href);
            url.searchParams.set('auth_success', 'true');
            url.searchParams.set('uid', user.uid);
            url.searchParams.set('email', user.email);
            
            // Salvar no localStorage
            localStorage.setItem('firebase_user', JSON.stringify({
                uid: user.uid,
                email: user.email,
                token: token,
                provider: 'email'
            }));
            
            // Redirecionar
            window.location.href = url.toString();
        } catch (error) {
            console.error("Erro no login com email:", error);
            alert("Erro no login com email: " + error.message);
        }
    };

    // Configurar botões após carregamento do DOM
    document.addEventListener('DOMContentLoaded', function() {
        console.log("Configurando botões de login...");
        
        // Google Login
        const googleBtn = document.getElementById('googleLogin');
        if (googleBtn) {
            googleBtn.addEventListener('click', function(e) {
                e.preventDefault();
                console.log("Clicou no botão Google");
                window.loginWithGoogle();
            });
            console.log("Botão Google configurado");
        }
        
        // Facebook Login
        const facebookBtn = document.getElementById('facebookLogin');
        if (facebookBtn) {
            facebookBtn.addEventListener('click', function(e) {
                e.preventDefault();
                console.log("Clicou no botão Facebook");
                window.loginWithFacebook();
            });
            console.log("Botão Facebook configurado");
        }
    });
    </script>
    """, unsafe_allow_html=True)

    # Botões de login com estilo direto no HTML
    st.markdown("""
    <div style="margin-bottom: 20px; padding: 20px; background-color: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <h2 style="text-align: center; margin-bottom: 20px;">Entrar com</h2>

        <button id="googleLogin" style="
            width: 100%;
            padding: 10px;
            margin-bottom: 10px;
            background-color: white;
            color: #444;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        ">
            <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" 
                 style="width: 18px; height: 18px; margin-right: 10px;">
            Continuar com Google
        </button>

        <button id="facebookLogin" style="
            width: 100%;
            padding: 10px;
            margin-bottom: 10px;
            background-color: #3b5998;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        ">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="white" 
                 style="margin-right: 10px;">
                <path d="M12 0c-6.627 0-12 5.373-12 12s5.373 12 12 12 12-5.373 12-12-5.373-12-12-12zm3 8h-1.35c-.538 0-.65.221-.65.778v1.222h2l-.209 2h-1.791v7h-3v-7h-2v-2h2v-2.308c0-1.769.931-2.692 3.029-2.692h1.971v3z"/>
            </svg>
            Continuar com Facebook
        </button>
    </div>
    """, unsafe_allow_html=True)

    # Separador
    st.markdown("<p style='text-align: center; margin: 20px 0;'>OU</p>", unsafe_allow_html=True)

    # Formulário de login
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")

        if submit:
            if email and password:
                # Adicionando código para chamar a função de login com email
                st.markdown(f"""
                <script>
                document.addEventListener('DOMContentLoaded', function() {{
                    // Chamar a função de login por email
                    window.loginWithEmail("{email}", "{password}");
                }});
                </script>
                """, unsafe_allow_html=True)
                
                # Modo de demonstração (somente para testes)
                if email.lower() == "admin" and password == "admin":
                    st.session_state.authenticated = True
                    st.session_state.user = {
                        "uid": "admin-user",
                        "email": "admin@example.com",
                        "demo": True
                    }
                    st.success("Login realizado com sucesso (modo demonstração)")
                    st.rerun()
            else:
                st.error("Email e senha são obrigatórios")
else:
    # Mostrar informações do usuário
    st.success(f"Login realizado com sucesso: {st.session_state.user.get('email')}")

    # Exibir dados
    st.write("### Dados do usuário")
    st.json(st.session_state.user)

    # Botão de logout
    if st.button("Sair"):
        # Limpar sessão
        st.session_state.authenticated = False
        st.session_state.user = None

        # Limpar localStorage
        st.markdown("""
        <script>
        localStorage.removeItem('firebase_user');
        </script>
        """, unsafe_allow_html=True)

        st.rerun()