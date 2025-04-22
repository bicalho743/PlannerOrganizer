"""
Gerenciador de sessão do usuário para autenticação

Este módulo centraliza a lógica de gerenciamento de estado de autenticação,
oferecendo funções para verificar, atualizar e limpar o estado do usuário.
"""
import streamlit as st
import time
from datetime import datetime, timedelta
import json
import os
import logging

# Configurar logging
logger = logging.getLogger(__name__)

# Constantes
TOKEN_EXPIRY_SECONDS = 60 * 60 * 24 * 7  # 7 dias
SESSION_USER_KEY = "user"
SESSION_AUTH_KEY = "authenticated"
SESSION_EXPIRY_KEY = "auth_expiry"


def is_authenticated():
    """
    Verifica se o usuário está autenticado e se o token ainda é válido
    
    Returns:
        bool: True se autenticado e válido, False caso contrário
    """
    # Verificar se há estado de autenticação
    if not st.session_state.get(SESSION_AUTH_KEY, False):
        return False
    
    # Verificar se há usuário na sessão
    if SESSION_USER_KEY not in st.session_state:
        return False
    
    # Verificar expiração do token
    expiry_time = st.session_state.get(SESSION_EXPIRY_KEY)
    if expiry_time and time.time() > expiry_time:
        # Token expirado, limpar sessão
        clear_session()
        return False
    
    return True


def set_auth_session(user_data, token=None, token_expiry=None):
    """
    Define o estado de autenticação e armazena os dados do usuário
    
    Args:
        user_data: Dicionário com informações do usuário
        token: Token de autenticação (opcional)
        token_expiry: Tempo de expiração do token em segundos (opcional)
    """
    if not user_data:
        raise ValueError("Dados do usuário não podem ser vazios")
    
    # Definir expiração do token
    expiry_seconds = token_expiry or TOKEN_EXPIRY_SECONDS
    expiry_time = time.time() + expiry_seconds
    
    # Armazenar na sessão
    st.session_state[SESSION_USER_KEY] = user_data
    st.session_state[SESSION_AUTH_KEY] = True
    st.session_state[SESSION_EXPIRY_KEY] = expiry_time
    
    # Registrar o evento (para auditoria)
    logger.info(f"Usuário autenticado: {user_data.get('email')} (expiração em {expiry_seconds/3600:.1f} horas)")


def clear_session():
    """
    Limpa os dados de autenticação da sessão
    """
    # Registrar o evento antes de limpar (para auditoria)
    if SESSION_USER_KEY in st.session_state:
        user_email = st.session_state[SESSION_USER_KEY].get('email', 'unknown')
        logger.info(f"Logout realizado: {user_email}")
    
    # Remover dados da sessão
    if SESSION_USER_KEY in st.session_state:
        del st.session_state[SESSION_USER_KEY]
    
    if SESSION_AUTH_KEY in st.session_state:
        st.session_state[SESSION_AUTH_KEY] = False
    
    if SESSION_EXPIRY_KEY in st.session_state:
        del st.session_state[SESSION_EXPIRY_KEY]


def get_current_user():
    """
    Retorna os dados do usuário atual
    
    Returns:
        dict: Dados do usuário ou None se não autenticado
    """
    if not is_authenticated():
        return None
    
    return st.session_state.get(SESSION_USER_KEY)


def update_session_expiry(seconds=None):
    """
    Atualiza o tempo de expiração da sessão
    
    Args:
        seconds: Tempo em segundos a partir de agora (padrão: TOKEN_EXPIRY_SECONDS)
    """
    if not is_authenticated():
        return
    
    expiry_seconds = seconds or TOKEN_EXPIRY_SECONDS
    st.session_state[SESSION_EXPIRY_KEY] = time.time() + expiry_seconds


def require_auth(redirect_path="/"):
    """
    Decorador para proteger páginas que requerem autenticação
    
    Args:
        redirect_path: Caminho para redirecionar se não autenticado
    
    Returns:
        função decorada
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not is_authenticated():
                st.warning("Você precisa estar autenticado para acessar esta página.")
                # Implementar redirecionamento aqui
                st.stop()
            return func(*args, **kwargs)
        return wrapper
    return decorator


def initialize_session_state():
    """
    Inicializa o estado da sessão se necessário
    """
    if SESSION_AUTH_KEY not in st.session_state:
        st.session_state[SESSION_AUTH_KEY] = False