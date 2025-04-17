import streamlit as st
import os
import sys
import time

# Adicionar diretório raiz ao path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

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

def main():
    # Se o usuário já estiver autenticado, redirecionar para o app principal
    if st.session_state.authenticated:
        # Redirecionar para o app principal
        st.success("Login realizado com sucesso! Redirecionando...")
        st.session_state.authenticated = True
        st.switch_page("app.py")
        return
    
    st.title("Planner Organizer - Login")
    st.subheader("Sistema de Gestão para Personal Organizers")
    
    # Login tradicional com email/senha
    with st.form("login_form"):
        username = st.text_input("Usuário ou E-mail")
        password = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar", use_container_width=True)
        
        if submit:
            if username.lower() == "admin" and password == "admin":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos")
    
    # Informações de acesso para demonstração
    st.info("""
    **Acesso para demonstração:**
    - Usuário: admin
    - Senha: admin
    """)
    
    # Opção alternativa para pular o login durante testes
    if st.button("Pular login (apenas para testes)"):
        st.session_state.authenticated = True
        st.rerun()

if __name__ == "__main__":
    main()