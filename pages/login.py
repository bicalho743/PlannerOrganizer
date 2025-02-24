import streamlit as st
from utils.database import Database
import jwt
import datetime

def show():
    st.title("🔐 Login")

    # Verificar se já existe um token de autenticação
    if 'token' in st.session_state:
        try:
            # Decodificar o token
            token_data = jwt.decode(st.session_state.token, st.secrets["JWT_SECRET"], algorithms=["HS256"])

            # Se o token ainda é válido, autenticar automaticamente
            if datetime.datetime.fromtimestamp(token_data['exp']) > datetime.datetime.utcnow():
                st.session_state.autenticado = True
                st.session_state.usuario = {
                    'id': token_data['id'],
                    'nome': token_data['nome'],
                    'email': token_data['email'],
                    'tipo': token_data['tipo']
                }
                st.experimental_rerun()
                return
        except:
            # Se houver qualquer erro com o token, removê-lo
            del st.session_state.token

    # Centralizar o formulário de login
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # Formulário de login
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
                        # Guardar informações do usuário na sessão
                        st.session_state.usuario = {
                            'id': usuario.id,
                            'nome': usuario.nome,
                            'email': usuario.email,
                            'tipo': usuario.tipo
                        }

                        # Se o usuário marcou "lembrar", criar um token JWT
                        if lembrar:
                            token = jwt.encode({
                                'id': usuario.id,
                                'nome': usuario.nome,
                                'email': usuario.email,
                                'tipo': usuario.tipo,
                                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
                            }, st.secrets["JWT_SECRET"], algorithm="HS256")
                            st.session_state.token = token

                        st.session_state.autenticado = True
                        st.experimental_rerun()
                    else:
                        st.error("Email ou senha incorretos.")

        # Link para registro
        st.markdown("---")
        st.markdown("Não tem uma conta? Entre em contato com o administrador.")