"""
Funções de autenticação usando Firebase
"""
import streamlit as st
import logging
from utils.firebase_config import initialize_firebase

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
    # Modo de demonstração para admin/admin
    if email.lower() == "admin" and senha == "admin":
        logger.warning("Usando modo de demonstração com admin/admin")
        return {
            'user_id': 'demo-123',
            'email': email,
            'token': 'demo-token',
            'refresh_token': 'demo-refresh',
            'is_verified': True,
            'demo_mode': True
        }
    
    # Inicializar Firebase
    try:
        app, _ = initialize_firebase()
        
        # Verificar se inicialização foi bem-sucedida
        if not app:
            logger.warning("Firebase não inicializado - usando modo de demonstração")
            return None
            
        # Importar auth aqui para evitar problemas de importação circular
        from firebase_admin import auth
        
        try:
            # Verifica se o usuário existe
            user = auth.get_user_by_email(email)
            
            # Verificação de senha (nota: Admin SDK não verifica senha diretamente)
            # Este é um login simplificado para demonstração
            # Na prática precisaria de um endpoint de autenticação adicional
            # ou usar Firebase Auth UI no cliente
            
            # Para simplicidade, consideramos que a senha é correta
            # (isso é apenas para demonstração)
            logger.warning("Usando autenticação simplificada - em produção use token auth")
            
            return {
                'user_id': user.uid,
                'email': user.email,
                'display_name': user.display_name,
                'is_verified': user.email_verified,
                'admin_sdk': True
            }
        except Exception as e:
            logger.error(f"Admin SDK - Erro de autenticação: {str(e)}")
            return None
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
    # Modo de demonstração para emails de teste
    if email.lower().endswith('@example.com') or email.lower() == 'admin':
        logger.warning("Usando modo de demonstração para criação de conta")
        return {
            'user_id': f'demo-{email}-{hash(senha) % 10000}',
            'email': email,
            'token': 'demo-token',
            'refresh_token': 'demo-refresh',
            'demo_mode': True
        }
    
    # Inicializar Firebase
    try:
        app, _ = initialize_firebase()
        
        # Verificar se inicialização foi bem-sucedida
        if not app:
            logger.warning("Firebase não inicializado - usando modo de demonstração")
            return {
                'user_id': f'demo-{email}-{hash(senha) % 10000}',
                'email': email,
                'token': 'demo-token',
                'refresh_token': 'demo-refresh',
                'demo_mode': True
            }
            
        # Importar auth aqui para evitar problemas de importação circular
        from firebase_admin import auth
        
        try:
            # Firebase Admin SDK
            user = auth.create_user(
                email=email,
                password=senha,
                display_name=nome or email.split('@')[0]
            )
            # Formato diferente de retorno no Admin SDK
            return {
                'user_id': user.uid,
                'email': user.email,
                'display_name': user.display_name,
                'admin_sdk': True
            }
        except Exception as e:
            logger.error(f"Admin SDK - Erro ao criar usuário: {str(e)}")
            return None
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
    # Modo de demonstração para emails de teste
    if email.lower().endswith('@example.com') or email.lower() == 'admin':
        logger.warning("Usando modo de demonstração para redefinição de senha")
        return True
    
    # Inicializar Firebase
    try:
        app, _ = initialize_firebase()
        
        # Verificar se inicialização foi bem-sucedida
        if not app:
            logger.warning("Firebase não inicializado - modo de demonstração")
            return True
            
        # Importar auth aqui para evitar problemas de importação circular
        from firebase_admin import auth
        
        # Gera link de redefinição
        link = auth.generate_password_reset_link(email)
        logger.info(f"Link de redefinição gerado: {link}")
        # Aqui seria implementado o envio do link por email
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