import streamlit as st
from utils.database import Database
import jwt
import datetime

def show():
    # Criar três colunas para centralização
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # Título centralizado com estilo
        st.markdown("<h1>PLANNER ORGANIZER</h1>", unsafe_allow_html=True)

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

        # Formulário de login centralizado
        st.markdown("<br>", unsafe_allow_html=True)  # Espaço entre título e formulário
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
                        # O usuario já é um dicionário agora
                        st.session_state.usuario = usuario

                        # Se o usuário marcou "lembrar", criar um token JWT
                        if lembrar:
                            token = jwt.encode({
                                'id': usuario['id'],
                                'nome': usuario['nome'],
                                'email': usuario['email'],
                                'tipo': usuario['tipo'],
                                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
                            }, st.secrets["JWT_SECRET"], algorithm="HS256")
                            st.session_state.token = token

                        st.session_state.autenticado = True
                        st.experimental_rerun()
                    else:
                        st.error("Email ou senha incorretos.")

        # Link para contato centralizado e com estilo mais discreto
        st.markdown("<div style='text-align: center; margin-top: 2rem; color: #666;'>Não tem uma conta? Entre em contato com o administrador.</div>", unsafe_allow_html=True)