import streamlit as st
import time

def show():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False
        st.session_state.usuario = None

    if not st.session_state.autenticado:
        st.title("🔐 Login")
        
        # Tabs para login e registro
        tab1, tab2 = st.tabs(["Login", "Registrar"])
        
        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email")
                senha = st.text_input("Senha", type="password")
                submitted = st.form_submit_button("Entrar")
                
                if submitted:
                    if email and senha:
                        sucesso, usuario = st.session_state.db.autenticar_usuario(email, senha)
                        if sucesso:
                            st.session_state.autenticado = True
                            st.session_state.usuario = usuario
                            st.success("Login realizado com sucesso!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Email ou senha inválidos")
                    else:
                        st.warning("Por favor, preencha todos os campos")
        
        with tab2:
            with st.form("registro_form"):
                nome = st.text_input("Nome")
                email = st.text_input("Email")
                empresa = st.text_input("Empresa (opcional)")
                senha = st.text_input("Senha", type="password")
                confirmar_senha = st.text_input("Confirmar Senha", type="password")
                
                submitted = st.form_submit_button("Registrar")
                
                if submitted:
                    if nome and email and senha and confirmar_senha:
                        if senha == confirmar_senha:
                            sucesso, msg = st.session_state.db.registrar_usuario(
                                email=email,
                                senha=senha,
                                nome=nome,
                                empresa=empresa
                            )
                            if sucesso:
                                st.success(msg)
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(msg)
                        else:
                            st.error("As senhas não coincidem")
                    else:
                        st.warning("Por favor, preencha todos os campos obrigatórios")
    else:
        st.success(f"Bem-vindo, {st.session_state.usuario.nome}!")
