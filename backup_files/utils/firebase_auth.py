"""
Funções de autenticação usando Firebase
"""
import streamlit as st
from utils.firebase_config import auth

def login_email_senha(email, senha):
    """
    Realiza login com email e senha usando Firebase Auth
    
    Args:
        email (str): Email do usuário
        senha (str): Senha do usuário
        
    Returns:
        dict: Informações do usuário se autenticado com sucesso, None se falhar
    """
    try:
        user = auth.sign_in_with_email_and_password(email, senha)
        # Obtém informações adicionais do usuário (opcional)
        user_info = auth.get_account_info(user['idToken'])
        return {
            'user_id': user['localId'],
            'email': user['email'],
            'token': user['idToken'],
            'refresh_token': user['refreshToken'],
            'is_verified': user_info['users'][0]['emailVerified']
        }
    except Exception as e:
        st.error(f"Erro ao fazer login: {e}")
        return None

def criar_conta(email, senha, nome=None):
    """
    Cria uma nova conta de usuário
    
    Args:
        email (str): Email do usuário
        senha (str): Senha do usuário
        nome (str, opcional): Nome do usuário
        
    Returns:
        dict: Informações do usuário se criado com sucesso, None se falhar
    """
    try:
        # Cria o usuário
        user = auth.create_user_with_email_and_password(email, senha)
        
        # Envia email de verificação (opcional)
        auth.send_email_verification(user['idToken'])
        
        # Armazena as informações do usuário na sessão
        return {
            'user_id': user['localId'],
            'email': user['email'],
            'token': user['idToken'],
            'refresh_token': user['refreshToken']
        }
    except Exception as e:
        st.error(f"Erro ao criar conta: {e}")
        return None

def redefinir_senha(email):
    """
    Envia email para redefinição de senha
    
    Args:
        email (str): Email do usuário
        
    Returns:
        bool: True se enviado com sucesso, False se falhar
    """
    try:
        auth.send_password_reset_email(email)
        return True
    except Exception as e:
        st.error(f"Erro ao redefinir senha: {e}")
        return False

def verificar_autenticacao():
    """
    Verifica se o usuário está autenticado
    
    Returns:
        bool: True se autenticado, False se não
    """
    return 'user_info' in st.session_state and st.session_state.user_info is not None