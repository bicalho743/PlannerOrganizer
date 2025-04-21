import streamlit as st
import os
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Login", page_icon="🔒", layout="centered")

# Inicializar sessão
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user" not in st.session_state:
    st.session_state.user = None

# Verificar parâmetros de URL
params = st.experimental_get_query_params()
if "auth_success" in params and params["auth_success"][0] == "true":
    if "uid" in params and "email" in params:
        uid = params["uid"][0]
        email = params["email"][0]
        
        # Salvar na sessão
        st.session_state.authenticated = True
        st.session_state.user = {
            "uid": uid,
            "email": email,
            "login_time": datetime.now().isoformat()
        }
        
        # Limpar parâmetros
        st.experimental_set_query_params()
        st.rerun()

# Título da página
st.title("Login - Planner Organizer")

# Se não estiver autenticado, mostrar tela de login
if not st.session_state.authenticated:
    # Formulário de login simples
    email = st.text_input("Email")
    password = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
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
            st.error("Credenciais inválidas")
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
        st.rerun()