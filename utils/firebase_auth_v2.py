"""
Módulo de autenticação Firebase atualizado para Streamlit
Este módulo fornece funções para gerenciar autenticação com Firebase a partir do Streamlit
"""
import os
import json
import requests
import streamlit as st

# Chaves de API e configurações
FIREBASE_API_KEY = os.environ.get("FIREBASE_API_KEY", st.secrets.get("FIREBASE_API_KEY", ""))
FIREBASE_PROJECT_ID = "planner-organizer-68a23"
FIREBASE_AUTH_DOMAIN = f"{FIREBASE_PROJECT_ID}.firebaseapp.com"

# URLs da API REST do Firebase Auth
BASE_URL = f"https://identitytoolkit.googleapis.com/v1/accounts"
SIGNIN_URL = f"{BASE_URL}:signInWithPassword?key={FIREBASE_API_KEY}"
SIGNUP_URL = f"{BASE_URL}:signUp?key={FIREBASE_API_KEY}"
RESET_PASSWORD_URL = f"{BASE_URL}:sendOobCode?key={FIREBASE_API_KEY}"
GET_USER_DATA_URL = f"{BASE_URL}:lookup?key={FIREBASE_API_KEY}"

def register_user(email, password, display_name=None):
    """
    Registra um novo usuário no Firebase Authentication
    
    Args:
        email (str): Email do usuário
        password (str): Senha do usuário
        display_name (str, optional): Nome de exibição do usuário
        
    Returns:
        dict: Dados do usuário ou erro
    """
    try:
        # Criar usuário no Firebase
        auth_data = {
            "email": email,
            "password": password, 
            "returnSecureToken": True
        }
        
        response = requests.post(SIGNUP_URL, json=auth_data)
        result = response.json()
        
        if 'error' in result:
            return {
                'success': False,
                'error': result['error']['message']
            }
        
        # Adicionar nome de exibição se fornecido
        if display_name and 'idToken' in result:
            update_profile_url = f"{BASE_URL}:update?key={FIREBASE_API_KEY}"
            profile_data = {
                "idToken": result['idToken'],
                "displayName": display_name,
                "returnSecureToken": True
            }
            
            profile_response = requests.post(update_profile_url, json=profile_data)
            if profile_response.status_code != 200:
                # O usuário foi criado, mas não conseguimos atualizar o perfil
                return {
                    'success': True,
                    'user': result,
                    'warning': 'Usuário criado, mas o nome de exibição não pôde ser atualizado'
                }
        
        # Retornar dados do usuário
        return {
            'success': True,
            'user': {
                'user_id': result['localId'],
                'email': result['email'],
                'id_token': result['idToken'],
                'refresh_token': result['refreshToken'],
                'display_name': display_name
            }
        }
        
    except Exception as e:
        import traceback
        return {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }

def login_with_email_password(email, password):
    """
    Faz login no Firebase com email e senha
    
    Args:
        email (str): Email do usuário
        password (str): Senha do usuário
        
    Returns:
        dict: Dados do usuário autenticado ou None se falhar
    """
    try:
        auth_data = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        
        response = requests.post(SIGNIN_URL, json=auth_data)
        
        if response.status_code == 200:
            result = response.json()
            
            # Obter dados adicionais do usuário
            user_info = get_user_info(result['idToken'])
            
            # Dados do usuário autenticado
            user_data = {
                'user_id': result['localId'],
                'email': result['email'],
                'id_token': result['idToken'],
                'refresh_token': result['refreshToken'],
                'display_name': user_info.get('displayName', ''),
                'photo_url': user_info.get('photoUrl', '')
            }
            
            return user_data
        else:
            error_data = response.json()
            st.error(f"Erro no login: {error_data.get('error', {}).get('message', 'Erro desconhecido')}")
            return None
            
    except Exception as e:
        st.error(f"Erro ao fazer login: {str(e)}")
        return None

def reset_password(email):
    """
    Envia email de redefinição de senha para o usuário
    
    Args:
        email (str): Email do usuário
        
    Returns:
        bool: True se o email foi enviado com sucesso
    """
    try:
        reset_data = {
            "requestType": "PASSWORD_RESET",
            "email": email
        }
        
        response = requests.post(RESET_PASSWORD_URL, json=reset_data)
        
        if response.status_code == 200:
            return True
        else:
            error_data = response.json()
            st.error(f"Erro ao solicitar redefinição de senha: {error_data.get('error', {}).get('message', 'Erro desconhecido')}")
            return False
            
    except Exception as e:
        st.error(f"Erro ao solicitar redefinição de senha: {str(e)}")
        return False

def get_user_info(id_token):
    """
    Obtém informações adicionais do usuário a partir do token de ID
    
    Args:
        id_token (str): Token de ID do usuário
        
    Returns:
        dict: Dados do usuário ou dicionário vazio se falhar
    """
    try:
        user_data = {
            "idToken": id_token
        }
        
        response = requests.post(GET_USER_DATA_URL, json=user_data)
        
        if response.status_code == 200:
            result = response.json()
            if 'users' in result and len(result['users']) > 0:
                return result['users'][0]
                
        return {}
            
    except Exception:
        return {}

def verify_session():
    """
    Verifica se existe uma sessão de usuário ativa
    
    Returns:
        bool: True se o usuário está autenticado
    """
    return st.session_state.get('authenticated', False)

def login_container():
    """
    Cria um container de login para ser embutido em qualquer página Streamlit
    
    Returns:
        bool: True se o login foi bem-sucedido
    """
    with st.container():
        st.markdown("### Login")
        
        login_tab, cadastro_tab = st.tabs(["Entrar", "Cadastrar"])
        
        with login_tab:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Senha", type="password")
                submitted = st.form_submit_button("Entrar")
                
                if submitted:
                    if email and password:
                        with st.spinner("Verificando credenciais..."):
                            user_data = login_with_email_password(email, password)
                            
                            if user_data:
                                st.session_state.authenticated = True
                                st.session_state.user = user_data
                                st.success("Login realizado com sucesso!")
                                return True
                    else:
                        st.error("Por favor, preencha todos os campos.")
        
        with cadastro_tab:
            with st.form("signup_form"):
                nome = st.text_input("Nome completo")
                email_cadastro = st.text_input("Email", key="signup_email")
                senha_cadastro = st.text_input("Senha", type="password", key="signup_password")
                confirmar_senha = st.text_input("Confirmar senha", type="password")
                cadastro_submitted = st.form_submit_button("Criar conta")
                
                if cadastro_submitted:
                    if not nome or not email_cadastro or not senha_cadastro or not confirmar_senha:
                        st.error("Por favor, preencha todos os campos.")
                    elif senha_cadastro != confirmar_senha:
                        st.error("As senhas não coincidem.")
                    elif len(senha_cadastro) < 6:
                        st.error("A senha deve ter pelo menos 6 caracteres.")
                    else:
                        with st.spinner("Criando sua conta..."):
                            result = register_user(email_cadastro, senha_cadastro, nome)
                            
                            if result['success']:
                                st.session_state.authenticated = True
                                st.session_state.user = result['user']
                                st.success("Conta criada com sucesso!")
                                return True
                            else:
                                st.error(f"Erro ao criar conta: {result.get('error', 'Erro desconhecido')}")
        
        # Link para redefinição de senha
        if st.button("Esqueceu sua senha?"):
            email_reset = st.text_input("Digite seu email para redefinir a senha")
            if st.button("Enviar link de redefinição"):
                if email_reset:
                    with st.spinner("Enviando link de redefinição..."):
                        if reset_password(email_reset):
                            st.success(f"Email de redefinição enviado para {email_reset}")
                else:
                    st.error("Por favor, informe seu email.")
                    
        return False

def logout():
    """
    Faz logout do usuário atual
    """
    if 'authenticated' in st.session_state:
        st.session_state.authenticated = False
    if 'user' in st.session_state:
        del st.session_state.user
        
def get_current_user():
    """
    Obtém dados do usuário atual
    
    Returns:
        dict: Dados do usuário ou None se não estiver autenticado
    """
    if verify_session():
        return st.session_state.user
    return None