import streamlit as st
from utils.database import Database

def show():
    st.title("🔐 Login")
    
    # Centralizar o formulário de login
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Formulário de login
        with st.form("login_form"):
            email = st.text_input("Email")
            senha = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar")
            
            if submitted:
                if not email or not senha:
                    st.error("Por favor, preencha todos os campos.")
                else:
                    # Tentar autenticar
                    sucesso, usuario = st.session_state.db.autenticar_usuario(email, senha)
                    
                    if sucesso:
                        # Guardar informações do usuário na sessão
                        st.session_state.usuario = {
                            'id': usuario.id,
                            'nome': usuario.nome,
                            'email': usuario.email,
                            'tipo': usuario.tipo
                        }
                        st.session_state.autenticado = True
                        st.experimental_rerun()
                    else:
                        st.error("Email ou senha incorretos.")
        
        # Link para registro
        st.markdown("---")
        st.markdown("Não tem uma conta? Entre em contato com o administrador.")
