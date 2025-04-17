import streamlit as st
import os
import sys
import time
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adicionar diretório raiz ao path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)
    logger.info(f"Adicionado {project_root} ao sys.path")

# Configuração da página
st.set_page_config(
    page_title="Planner Organizer - Login",
    page_icon="favicon.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Remover o menu hamburguer e rodapé
hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    </style>
"""
st.markdown(hide_menu_style, unsafe_allow_html=True)

# Verificar se o usuário já está autenticado
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Simulação da autenticação para demonstração
if "admin_login_attempt" not in st.session_state:
    st.session_state.admin_login_attempt = False

def main():
    # Se o usuário já estiver autenticado, redirecionar para o app principal
    if st.session_state.authenticated:
        # Redirecionar para o app principal
        st.success("Login realizado com sucesso! Redirecionando...")
        st.session_state.authenticated = True
        time.sleep(1)
        st.switch_page("app.py")
        return
    
    # Criar um layout com duas colunas
    col1, col2 = st.columns([6, 4])
    
    with col1:
        st.markdown("""
        <div style="padding: 2rem; background-color: #f8f9fa; border-radius: 10px;">
            <h1 style="color: #1E366F; font-size: 2rem;">Planner Organizer</h1>
            <h3 style="color: #5A6A85; margin-bottom: 2rem;">Sistema de Gestão para Personal Organizers</h3>
            
            <p style="margin-bottom: 1.5rem; color: #495057;">
                Acesse o sistema para gerenciar suas propostas, clientes, 
                produtos e finanças de maneira simples e eficiente.
            </p>
            
            <ul style="list-style-type: none; padding-left: 0; margin-bottom: 2rem;">
                <li style="margin-bottom: 0.5rem; color: #495057;">✅ Controle de propostas</li>
                <li style="margin-bottom: 0.5rem; color: #495057;">✅ Gestão de clientes</li>
                <li style="margin-bottom: 0.5rem; color: #495057;">✅ Finanças e receitas</li>
                <li style="margin-bottom: 0.5rem; color: #495057;">✅ Relatórios detalhados</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        tab1, tab2 = st.tabs(["Login", "Registrar"])
        
        with tab1:
            # Login tradicional com email/senha
            with st.form("login_form"):
                username = st.text_input("Usuário ou E-mail")
                password = st.text_input("Senha", type="password")
                submit = st.form_submit_button("Entrar", use_container_width=True)
                
                if submit:
                    if username.lower() == "admin" and password == "admin":
                        st.session_state.authenticated = True
                        st.session_state.admin_login_attempt = True
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos")
            
            # Divisor com "ou"
            st.markdown("""
            <div style="text-align: center; margin: 1.5rem 0; position: relative;">
                <hr style="margin: 0; border: none; height: 1px; background-color: #E0E0E0;">
                <span style="position: absolute; top: -10px; left: 50%; transform: translateX(-50%); 
                       background-color: white; padding: 0 10px; color: #5A6A85; font-size: 0.9rem;">
                    ou continuar com
                </span>
            </div>
            """, unsafe_allow_html=True)
            
            # Botões para login social
            col_google, col_facebook = st.columns(2)
            
            with col_google:
                st.markdown("""
                <button style="width: 100%; background-color: white; border: 1px solid #E0E0E0; 
                               border-radius: 4px; padding: 8px 0; display: flex; align-items: center; 
                               justify-content: center; cursor: pointer; transition: all 0.2s ease;">
                    <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" 
                         style="width: 18px; height: 18px; margin-right: 8px;">
                    Google
                </button>
                """, unsafe_allow_html=True)
            
            with col_facebook:
                st.markdown("""
                <button style="width: 100%; background-color: #3b5998; border: none; color: white;
                               border-radius: 4px; padding: 8px 0; display: flex; align-items: center; 
                               justify-content: center; cursor: pointer; transition: all 0.2s ease;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="white" 
                         style="margin-right: 8px;">
                        <path d="M12 0c-6.627 0-12 5.373-12 12s5.373 12 12 12 12-5.373 12-12-5.373-12-12-12zm3 8h-1.35c-.538 0-.65.221-.65.778v1.222h2l-.209 2h-1.791v7h-3v-7h-2v-2h2v-2.308c0-1.769.931-2.692 3.029-2.692h1.971v3z"/>
                    </svg>
                    Facebook
                </button>
                """, unsafe_allow_html=True)
            
            # Adicionar links para recuperação de senha
            st.markdown("""
            <div style="text-align: center; margin-top: 1rem;">
                <a href="#" style="color: #1E88E5; text-decoration: none; font-size: 0.9rem;">
                    Esqueceu sua senha?
                </a>
            </div>
            """, unsafe_allow_html=True)
            
            # Nota informativa sobre o login social
            st.info("Os botões de login social estão em implementação e serão ativados em breve.")
            
            # Informações de acesso para demonstração
            st.markdown("""
            <div style="margin-top: 1rem; padding: 0.75rem; background-color: #E3F2FD; border-radius: 4px; border-left: 4px solid #1976D2;">
                <p style="margin: 0; color: #1E366F; font-size: 0.9rem;">
                    <strong>Acesso para demonstração:</strong><br>
                    Usuário: admin<br>
                    Senha: admin
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with tab2:
            with st.form("registro_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    nome = st.text_input("Nome completo")
                    email = st.text_input("E-mail")
                
                with col2:
                    senha = st.text_input("Senha", type="password")
                    confirmar_senha = st.text_input("Confirmar senha", type="password")
                
                aceito_termos = st.checkbox("Eu aceito os termos de uso")
                
                submit_button = st.form_submit_button("Criar conta", use_container_width=True)
                
                if submit_button:
                    if not (nome and email and senha and confirmar_senha):
                        st.error("Por favor, preencha todos os campos")
                    elif senha != confirmar_senha:
                        st.error("As senhas não coincidem")
                    elif not aceito_termos:
                        st.error("Você precisa aceitar os termos de uso")
                    else:
                        st.success(f"Conta simulada criada com sucesso para {email}")
                        st.info("Você pode fazer login agora")

if __name__ == "__main__":
    main()