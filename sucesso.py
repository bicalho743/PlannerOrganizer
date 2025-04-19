"""
Página de sucesso após o checkout do Stripe
"""
import streamlit as st
import os

def main():
    """
    Página exibida após o retorno do checkout com sucesso
    """
    # Configuração da página
    st.set_page_config(
        page_title="Pagamento Confirmado | Planner Organizer",
        page_icon="✅",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    # Ocultar o menu hamburger e o rodapé do Streamlit
    hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """
    st.markdown(hide_menu_style, unsafe_allow_html=True)
    
    # CSS para a página
    st.markdown("""
    <style>
    .success-container {
        padding: 2rem;
        border-radius: 10px;
        background-color: #f0f9ff;
        border: 1px solid #90cdf4;
        text-align: center;
        margin: 2rem auto;
        max-width: 600px;
    }
    .success-icon {
        font-size: 5rem;
        color: #38a169;
        margin-bottom: 1rem;
    }
    .success-title {
        font-size: 1.8rem;
        color: #2c5282;
        margin-bottom: 1rem;
    }
    .success-message {
        font-size: 1.1rem;
        color: #4a5568;
        margin-bottom: 2rem;
    }
    .action-button {
        background-color: #3182ce;
        color: white;
        padding: 10px 20px;
        border-radius: 5px;
        text-decoration: none;
        font-weight: bold;
        transition: background-color 0.3s;
    }
    .action-button:hover {
        background-color: #2b6cb0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Carregar o Firebase SDK e o script personalizado
    st.markdown("""
    <script src="https://www.gstatic.com/firebasejs/8.10.0/firebase-app.js"></script>
    <script src="https://www.gstatic.com/firebasejs/8.10.0/firebase-auth.js"></script>
    <script src="/public/js/firebase-auth.js"></script>
    """, unsafe_allow_html=True)
    
    # Container para mensagens de pagamento que será atualizado pelo JavaScript
    st.markdown('<div id="payment-message-container"></div>', unsafe_allow_html=True)
    
    # Interface padrão (será substituída pelo JavaScript se o usuário tiver feito pagamento)
    st.markdown("""
    <div class="success-container">
        <div class="success-icon">✅</div>
        <h1 class="success-title">Pagamento Processado!</h1>
        <p class="success-message">
            Estamos verificando os detalhes do seu pagamento. Isso pode levar alguns instantes.
            Assim que confirmado, sua conta será ativada automaticamente.
        </p>
        <a href="/" class="action-button">Voltar para o início</a>
    </div>
    """, unsafe_allow_html=True)
    
    # Inicializar o Firebase com as configurações
    firebase_config = {
        "apiKey": st.secrets.get("FIREBASE_API_KEY", "AIzaSyA8xzYgZXCkZ-97RWQZXtMpvLVf1Jx8wjk"),
        "authDomain": st.secrets.get("FIREBASE_AUTH_DOMAIN", "planner-organizer.firebaseapp.com"),
        "projectId": st.secrets.get("FIREBASE_PROJECT_ID", "planner-organizer"),
        "storageBucket": st.secrets.get("FIREBASE_STORAGE_BUCKET", "planner-organizer.appspot.com"),
        "messagingSenderId": st.secrets.get("FIREBASE_MESSAGING_SENDER_ID", "695046724018"),
        "appId": st.secrets.get("FIREBASE_APP_ID", "1:695046724018:web:98d8feec0c6b6c937d57fd"),
        "databaseURL": st.secrets.get("FIREBASE_DATABASE_URL", "https://planner-organizer-default-rtdb.firebaseio.com")
    }
    
    # JavaScript para inicializar o Firebase e processar o pagamento
    st.markdown(f"""
    <script>
        // Configuração do Firebase
        const firebaseConfig = {JSON.stringify(firebase_config)};
        
        // Inicializar Firebase quando a página carregar
        document.addEventListener('DOMContentLoaded', function() {{
            // Inicializar Firebase
            window.firebaseAuth.init(firebaseConfig);
            
            // Verificar parâmetros da URL
            const urlParams = new URLSearchParams(window.location.search);
            const sessionId = urlParams.get('session_id');
            
            if (sessionId) {{
                // Exibir mensagem de processamento
                const messageContainer = document.getElementById('payment-message-container');
                if (messageContainer) {{
                    messageContainer.innerHTML = `
                        <div class="success-container">
                            <div class="success-icon">⌛</div>
                            <h1 class="success-title">Processando Pagamento</h1>
                            <p class="success-message">
                                Estamos verificando seu pagamento com o ID: ${sessionId}.
                                Por favor, aguarde alguns instantes...
                            </p>
                        </div>
                    `;
                }}
            }}
        }});
    </script>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()