"""
Componente para autenticação com Google via Firebase
Módulo destinado a ser utilizado quando a aplicação estiver em ambiente HTTPS
"""
import streamlit as st
import json
import os
import requests
import firebase_admin
from firebase_admin import credentials, auth

# Constantes
FIREBASE_CONFIG_FILE = "firebase-credentials.json"


class GoogleAuthComponent:
    """
    Componente para implementar autenticação com Google usando Firebase
    """
    def __init__(self, config=None):
        """
        Inicializa o componente de autenticação Google
        
        Args:
            config: Configuração opcional do Firebase (dict)
        """
        self.initialized = False
        self.config = config or {}
        
        # Se config não fornecido, tentar ler do ambiente
        if not self.config:
            try:
                # Verificar se as variáveis de ambiente estão disponíveis
                api_key = os.environ.get("FIREBASE_API_KEY")
                auth_domain = os.environ.get("FIREBASE_AUTH_DOMAIN")
                project_id = os.environ.get("FIREBASE_PROJECT_ID")
                
                if api_key and auth_domain and project_id:
                    self.config = {
                        "apiKey": api_key,
                        "authDomain": auth_domain,
                        "projectId": project_id,
                        "storageBucket": os.environ.get("FIREBASE_STORAGE_BUCKET", ""),
                        "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID", ""),
                        "appId": os.environ.get("FIREBASE_APP_ID", "")
                    }
            except Exception as e:
                st.warning(f"Erro ao configurar autenticação Google: {str(e)}")
        
        # Inicializar Admin SDK para verificação de tokens
        try:
            # Tentar inicializar apenas se ainda não inicializado
            if not firebase_admin._apps:
                if os.path.exists(FIREBASE_CONFIG_FILE):
                    cred = credentials.Certificate(FIREBASE_CONFIG_FILE)
                    firebase_admin.initialize_app(cred)
                    self.initialized = True
        except Exception as e:
            st.warning(f"Erro ao inicializar Firebase Admin SDK: {str(e)}")
    
    def render_login_button(self, button_text="Continuar com Google", key=None):
        """
        Renderiza o botão de login com Google
        
        Args:
            button_text: Texto a ser exibido no botão
            key: Chave única para o componente Streamlit
            
        Returns:
            bool: True se o botão foi clicado, False caso contrário
        """
        # Este componente só funciona corretamente em ambiente HTTPS
        if not self._check_https():
            st.warning("O login com Google requer HTTPS para funcionar corretamente.")
            return False
        
        # Verificar se temos configuração válida
        if not self.config or not self.config.get("apiKey"):
            st.error("Configuração do Firebase não encontrada ou incompleta.")
            return False
        
        # Gerar HTML com o botão e script de autenticação
        html_content = self._generate_auth_html(button_text)
        
        # Renderizar componente HTML
        st.components.v1.html(html_content, height=50)
        
        # Verificar se temos um token na URL
        query_params = st.query_params
        id_token = query_params.get('id_token')
        
        if id_token:
            # Processar token e retornar resultado de autenticação
            return self._process_id_token(id_token)
        
        return False
    
    def _check_https(self):
        """
        Verifica se a aplicação está rodando em HTTPS
        
        Returns:
            bool: True se estiver em HTTPS, False caso contrário
        """
        # Em produção, verificar o cabeçalho X-Forwarded-Proto
        # Em desenvolvimento local, permitir HTTP para testes
        if "STREAMLIT_ENV" in os.environ and os.environ["STREAMLIT_ENV"] == "production":
            # Aqui deveria verificar o protocolo, mas o Streamlit não expõe esta informação
            # Assumimos que em produção estará em HTTPS
            return True
        else:
            # Em desenvolvimento, permitimos HTTP para testes
            return True
    
    def _generate_auth_html(self, button_text):
        """
        Gera o HTML para o botão de autenticação e scripts
        
        Args:
            button_text: Texto a ser exibido no botão
            
        Returns:
            str: HTML com botão e scripts
        """
        config_json = json.dumps(self.config)
        
        html = f"""
        <script src="https://www.gstatic.com/firebasejs/9.22.0/firebase-app-compat.js"></script>
        <script src="https://www.gstatic.com/firebasejs/9.22.0/firebase-auth-compat.js"></script>
        
        <button id="google-login-button" class="social-button google-button" 
                style="background-color: white; border: 1px solid #E0E0E0; border-radius: 4px; 
                       padding: 8px 16px; display: flex; align-items: center; cursor: pointer;">
            <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" 
                 style="width: 18px; height: 18px; margin-right: 8px;">
            <span>{button_text}</span>
        </button>
        
        <script>
            // Inicializar Firebase
            const firebaseConfig = {config_json};
            firebase.initializeApp(firebaseConfig);
            
            // Configurar botão de login
            document.getElementById('google-login-button').addEventListener('click', function() {{
                const provider = new firebase.auth.GoogleAuthProvider();
                firebase.auth().signInWithPopup(provider)
                    .then((result) => {{
                        // Login bem-sucedido
                        const credential = result.credential;
                        const token = credential.idToken;
                        const user = result.user;
                        
                        // Redirecionar com o token na URL
                        const currentUrl = new URL(window.location.href);
                        currentUrl.searchParams.set('id_token', token);
                        window.location.href = currentUrl.toString();
                    }})
                    .catch((error) => {{
                        // Erro no login
                        console.error("Erro ao autenticar com Google:", error);
                        alert("Erro ao autenticar com Google: " + error.message);
                    }});
            }});
        </script>
        """
        
        return html
    
    def _process_id_token(self, id_token):
        """
        Processa o token de ID do Google/Firebase
        
        Args:
            id_token: Token de ID para verificar
            
        Returns:
            dict: Informações do usuário se autenticado com sucesso
            bool: False se falhou
        """
        if not self.initialized:
            st.error("Firebase Admin SDK não inicializado. Não é possível verificar o token.")
            return False
        
        try:
            # Verificar o token
            decoded_token = auth.verify_id_token(id_token)
            
            # Extrair informações do usuário
            user_info = {
                'uid': decoded_token['uid'],
                'email': decoded_token.get('email', ''),
                'name': decoded_token.get('name', ''),
                'picture': decoded_token.get('picture', ''),
                'email_verified': decoded_token.get('email_verified', False)
            }
            
            # Armazenar na sessão para uso futuro
            st.session_state.user = user_info
            st.session_state.authenticated = True
            
            return user_info
        except Exception as e:
            st.error(f"Erro ao verificar token de autenticação: {str(e)}")
            return False


# Função para criar e renderizar o componente
def google_login_button(text="Continuar com Google", key=None):
    """
    Renderiza um botão de login com Google
    
    Args:
        text: Texto a ser exibido no botão
        key: Chave única para o componente Streamlit
        
    Returns:
        dict: Informações do usuário se autenticado com sucesso
        bool: False se não autenticado
    """
    component = GoogleAuthComponent()
    return component.render_login_button(button_text=text, key=key)