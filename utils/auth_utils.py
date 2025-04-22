"""
Utilitários para autenticação

Este módulo fornece funções auxiliares para serem usadas nas páginas 
de login, registro e recuperação de senha.
"""
import streamlit as st
import re
import time
import logging

# Tentar importar firebase_admin, mas falhar silenciosamente se não estiver disponível
try:
    from firebase_admin import auth as firebase_admin_auth
    firebase_admin_available = True
except ImportError:
    firebase_admin_available = False

from utils.auth_security import (
    check_brute_force,
    validate_password_strength,
    hash_password,
    verify_password,
    create_password_reset_token
)
from utils.auth_audit import log_auth_event
from utils.session_manager import set_auth_session, clear_session, is_authenticated
from utils.firebase_auth import firebase_auth

# Configuração de logging
logger = logging.getLogger(__name__)


def login_user(email, password):
    """
    Realiza o login do usuário
    
    Args:
        email: Email do usuário
        password: Senha do usuário
        
    Returns:
        dict: Resultado da operação com status e mensagem
    """
    # Validar entrada
    if not email or not password:
        return {"success": False, "message": "Email e senha são obrigatórios"}
    
    # Verificar proteção contra força bruta
    blocked, reason = check_brute_force(email)
    if blocked:
        return {"success": False, "message": reason}
    
    # Tentar autenticar com Firebase
    try:
        # Se Firebase Auth disponível, usar ele
        if firebase_auth is not None:
            result = firebase_auth.login(email, password)
            
            # Registrar evento de auditoria
            log_auth_event(
                "login", 
                user_email=email,
                user_id=result.get("user", {}).get("localId") if result.get("success") else None,
                success=result.get("success", False),
                details={"method": "firebase"}
            )
            
            if result.get("success"):
                # Definir sessão
                user_data = result.get("user", {})
                set_auth_session(user_data)
                
                return {"success": True, "message": "Login realizado com sucesso", "user": user_data}
            else:
                # Login falhou
                error_msg = result.get("error", "Erro desconhecido")
                return {"success": False, "message": f"Erro de autenticação: {error_msg}"}
        else:
            # Fallback para conta de demonstração
            if email.lower() == "admin" and password == "admin":
                user_data = {
                    "email": "admin@example.com",
                    "displayName": "Administrador",
                    "demo_account": True
                }
                
                # Definir sessão
                set_auth_session(user_data)
                
                # Registrar evento
                log_auth_event(
                    "login", 
                    user_email=email,
                    success=True,
                    details={"method": "demo_account"}
                )
                
                return {"success": True, "message": "Login (demonstração) realizado com sucesso", "user": user_data}
            
            # Login falhou
            log_auth_event(
                "login", 
                user_email=email,
                success=False,
                details={"method": "demo_account", "reason": "invalid_credentials"}
            )
            
            return {"success": False, "message": "Email ou senha incorretos"}
    except Exception as e:
        logger.error(f"Erro ao fazer login: {str(e)}")
        log_auth_event(
            "login", 
            user_email=email,
            success=False,
            details={"method": "firebase", "error": str(e)}
        )
        return {"success": False, "message": f"Erro ao fazer login: {str(e)}"}


def register_user(email, password, name=""):
    """
    Registra um novo usuário
    
    Args:
        email: Email do usuário
        password: Senha do usuário
        name: Nome do usuário (opcional)
        
    Returns:
        dict: Resultado da operação com status e mensagem
    """
    # Validar entrada
    if not email or not password:
        return {"success": False, "message": "Email e senha são obrigatórios"}
    
    # Validar formato de email
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return {"success": False, "message": "Formato de email inválido"}
    
    # Validar força da senha
    is_valid, reason = validate_password_strength(password)
    if not is_valid:
        return {"success": False, "message": reason}
    
    # Tentar registrar com Firebase
    try:
        if firebase_auth is not None:
            result = firebase_auth.register(email, password, name)
            
            # Registrar evento de auditoria
            log_auth_event(
                "register", 
                user_email=email,
                user_id=result.get("user", {}).get("localId") if result.get("success") else None,
                success=result.get("success", False),
                details={"method": "firebase"}
            )
            
            if result.get("success"):
                # Definir sessão de usuário
                user_data = result.get("user", {})
                set_auth_session(user_data)
                
                return {"success": True, "message": "Conta criada com sucesso", "user": user_data}
            else:
                # Registro falhou
                error_msg = result.get("error", "Erro desconhecido")
                return {"success": False, "message": f"Erro ao criar conta: {error_msg}"}
        else:
            # Sem Firebase, informar que o registro está desabilitado
            log_auth_event(
                "register", 
                user_email=email,
                success=False,
                details={"method": "demo", "reason": "firebase_disabled"}
            )
            return {"success": False, "message": "Criação de conta desabilitada nesta versão de demonstração"}
    except Exception as e:
        logger.error(f"Erro ao registrar usuário: {str(e)}")
        log_auth_event(
            "register", 
            user_email=email,
            success=False,
            details={"method": "firebase", "error": str(e)}
        )
        return {"success": False, "message": f"Erro ao criar conta: {str(e)}"}


def reset_password(email):
    """
    Inicia o processo de redefinição de senha
    
    Args:
        email: Email do usuário
        
    Returns:
        dict: Resultado da operação com status e mensagem
    """
    # Validar entrada
    if not email:
        return {"success": False, "message": "Email é obrigatório"}
    
    # Validar formato de email
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return {"success": False, "message": "Formato de email inválido"}
    
    # Tentar redefinir senha
    try:
        if firebase_auth is not None:
            result = firebase_auth.reset_password(email)
            
            # Registrar evento de auditoria
            log_auth_event(
                "password_reset", 
                user_email=email,
                success=result.get("success", False),
                details={"method": "firebase"}
            )
            
            if result.get("success"):
                return {"success": True, "message": "Email de redefinição enviado. Verifique sua caixa de entrada."}
            else:
                # Redefinição falhou
                error_msg = result.get("error", "Erro desconhecido")
                return {"success": False, "message": f"Erro ao redefinir senha: {error_msg}"}
        else:
            # Sem Firebase, informar que a redefinição está desabilitada
            log_auth_event(
                "password_reset", 
                user_email=email,
                success=False,
                details={"method": "demo", "reason": "firebase_disabled"}
            )
            return {"success": False, "message": "Redefinição de senha desabilitada nesta versão de demonstração"}
    except Exception as e:
        logger.error(f"Erro ao redefinir senha: {str(e)}")
        log_auth_event(
            "password_reset", 
            user_email=email,
            success=False,
            details={"method": "firebase", "error": str(e)}
        )
        return {"success": False, "message": f"Erro ao redefinir senha: {str(e)}"}


def logout():
    """
    Realiza o logout do usuário
    
    Returns:
        dict: Resultado da operação com status e mensagem
    """
    try:
        # Obter informações do usuário antes de limpar
        user = st.session_state.get("user", {})
        
        # Limpar dados de sessão
        clear_session()
        
        # Se Firebase disponível, fazer logout nele também
        if firebase_auth is not None:
            firebase_auth.logout()
        
        # Registrar evento de auditoria
        log_auth_event(
            "logout", 
            user_email=user.get("email"),
            user_id=user.get("uid"),
            success=True
        )
        
        return {"success": True, "message": "Logout realizado com sucesso"}
    except Exception as e:
        logger.error(f"Erro ao fazer logout: {str(e)}")
        return {"success": False, "message": f"Erro ao fazer logout: {str(e)}"}


def verify_google_auth(id_token):
    """
    Verifica token de autenticação Google
    
    Args:
        id_token: Token de ID do Google
        
    Returns:
        dict: Resultado da verificação com status e mensagem
    """
    if not id_token:
        return {"success": False, "message": "Token não fornecido"}
    
    # Verificar se firebase_admin está disponível
    if not firebase_admin_available:
        logger.error("Firebase Admin SDK não disponível para verificar token Google")
        log_auth_event(
            "login", 
            success=False,
            details={"method": "google", "error": "Firebase Admin SDK não disponível"}
        )
        return {"success": False, "message": "Autenticação com Google não está disponível neste ambiente"}
    
    try:
        # Verificar token com Firebase Admin SDK
        decoded_token = firebase_admin_auth.verify_id_token(id_token)
        
        # Extrair informações do usuário
        user_info = {
            'uid': decoded_token['uid'],
            'email': decoded_token.get('email', ''),
            'displayName': decoded_token.get('name', ''),
            'photoURL': decoded_token.get('picture', ''),
            'email_verified': decoded_token.get('email_verified', False),
            'auth_provider': 'google'
        }
        
        # Definir sessão
        set_auth_session(user_info)
        
        # Registrar evento
        log_auth_event(
            "login", 
            user_email=user_info['email'],
            user_id=user_info['uid'],
            success=True,
            details={"method": "google"}
        )
        
        return {"success": True, "message": "Autenticação com Google bem-sucedida", "user": user_info}
    except Exception as e:
        logger.error(f"Erro ao verificar token Google: {str(e)}")
        log_auth_event(
            "login", 
            success=False,
            details={"method": "google", "error": str(e)}
        )
        return {"success": False, "message": f"Erro na autenticação com Google: {str(e)}"}


def require_auth(func):
    """
    Decorador para proteger páginas que requerem autenticação
    
    Args:
        func: Função a ser decorada
        
    Returns:
        wrapper: Função decorada
    """
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            st.warning("Você precisa estar autenticado para acessar esta página.")
            st.stop()
        return func(*args, **kwargs)
    return wrapper