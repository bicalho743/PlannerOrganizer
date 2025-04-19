"""
Funções de autenticação usando Firebase
"""
import streamlit as st
import logging
from utils.firebase_config import auth

# Configuração do logging
logger = logging.getLogger(__name__)

def login_email_senha(email, senha):
    """
    Realiza login com email e senha usando Firebase Auth
    
    Args:
        email (str): Email do usuário
        senha (str): Senha do usuário
        
    Returns:
        dict: Informações do usuário se autenticado com sucesso, None se falhar
    """
    # Se auth for None (Firebase não inicializado), modo de demonstração
    if auth is None:
        logger.warning("Firebase Auth não disponível, usando modo de demonstração.")
        if email.lower() == "admin" and senha == "admin":
            return {
                'user_id': 'demo-123',
                'email': email,
                'token': 'demo-token',
                'refresh_token': 'demo-refresh',
                'is_verified': True,
                'demo_mode': True
            }
        return None
    
    # Procedimento normal com Firebase
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
        logger.error(f"Erro ao fazer login: {str(e)}")
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
    # Se auth for None (Firebase não inicializado), modo de demonstração
    if auth is None:
        logger.warning("Firebase Auth não disponível, usando modo de demonstração.")
        return {
            'user_id': f'demo-{email}-{hash(senha) % 10000}',
            'email': email,
            'token': 'demo-token',
            'refresh_token': 'demo-refresh',
            'demo_mode': True
        }
    
    # Procedimento normal com Firebase
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
        logger.error(f"Erro ao criar conta: {str(e)}")
        return None

def redefinir_senha(email):
    """
    Envia email para redefinição de senha
    
    Args:
        email (str): Email do usuário
        
    Returns:
        bool: True se enviado com sucesso, False se falhar
    """
    # Se auth for None (Firebase não inicializado), modo de demonstração
    if auth is None:
        logger.warning("Firebase Auth não disponível, usando modo de demonstração.")
        return True
    
    # Procedimento normal com Firebase
    try:
        auth.send_password_reset_email(email)
        return True
    except Exception as e:
        logger.error(f"Erro ao redefinir senha: {str(e)}")
        return False

def fazer_login(email, senha):
    """
    Função wrapper para compatibilidade com o sistema atual
    
    Args:
        email (str): Email do usuário
        senha (str): Senha do usuário
        
    Returns:
        dict: Informações do usuário ou None se falhar
    """
    return login_email_senha(email, senha)

def verificar_autenticacao():
    """
    Verifica se o usuário está autenticado
    
    Returns:
        bool: True se autenticado, False se não
    """
    return 'authenticated' in st.session_state and st.session_state.authenticated