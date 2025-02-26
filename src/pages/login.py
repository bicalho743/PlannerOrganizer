import streamlit as st
import datetime
import jwt
import os

def show():
    # Criar três colunas para centralização
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # Título centralizado com estilo
        st.markdown("<h1>PLANNER ORGANIZER</h1>", unsafe_allow_html=True)

        # Tabs para login e registro
        tab1, tab2 = st.tabs(["Login", "Registrar"])

        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email")
                senha = st.text_input("Senha", type="password")
                lembrar = st.checkbox("Manter conectado")
                submitted = st.form_submit_button("Entrar")

                if submitted:
                    if not email or not senha:
                        st.error("Por favor, preencha todos os campos.")
                    else:
                        # Tentar autenticar
                        sucesso, usuario = st.session_state.db.autenticar_usuario(email, senha)

                        if sucesso:
                            st.session_state.usuario = usuario

                            # Se o usuário marcou "lembrar", criar um token JWT
                            if lembrar:
                                try:
                                    jwt_secret = st.secrets.get("JWT_SECRET") or os.getenv("JWT_SECRET")
                                    if jwt_secret:
                                        token = jwt.encode({
                                            'id': usuario['id'],
                                            'nome': usuario['nome'],
                                            'email': usuario['email'],
                                            'tipo': usuario['tipo'],
                                            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
                                        }, jwt_secret, algorithm="HS256")
                                        st.session_state.token = token
                                except Exception as e:
                                    st.warning("Não foi possível criar o token de 'lembrar-me'. O login ainda funcionará, mas você precisará fazer login novamente ao fechar o navegador.")

                            st.session_state.autenticado = True
                            st.success("Login realizado com sucesso!")
                            st.rerun()
                        else:
                            st.error("Email ou senha incorretos.")

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
                                st.rerun()
                            else:
                                st.error(msg)
                        else:
                            st.error("As senhas não coincidem")
                    else:
                        st.warning("Por favor, preencha todos os campos obrigatórios")

        # Link para contato centralizado e com estilo mais discreto
        st.markdown(
            "<div style='text-align: center; margin-top: 2rem; color: #666;'>"
            "Não tem uma conta? Entre em contato com o administrador."
            "</div>",
            unsafe_allow_html=True
        )