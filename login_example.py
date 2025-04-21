"""
Exemplo de página de login usando o módulo Firebase Auth V2
"""
import streamlit as st
from utils.firebase_auth_v2 import login_container, verify_session, logout, get_current_user

# Configuração da página
st.set_page_config(
    page_title="Demo Login Firebase",
    page_icon="🔑",
    layout="centered"
)

# Título da aplicação
st.title("Demo de Login com Firebase")

# Verificar se o usuário já está autenticado
if verify_session():
    # Obter dados do usuário
    user = get_current_user()
    
    # Mostrar boas-vindas
    st.success(f"Bem-vindo, {user.get('display_name') or user.get('email')}!")
    
    # Exibir dados do usuário
    st.write("### Seus dados:")
    st.json(user)
    
    # Botão de logout
    if st.button("Sair"):
        logout()
        st.experimental_rerun()
else:
    # Exibir o container de login
    st.write("Por favor, faça login para continuar:")
    
    if login_container():
        # Recarregar a página após login bem-sucedido
        st.experimental_rerun()