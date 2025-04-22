"""
Recursos de segurança para autenticação

Este módulo fornece funções para proteger o sistema de autenticação contra 
vários ataques como força bruta, fixação de sessão, e outras vulnerabilidades.
"""
import time
import re
import streamlit as st
import logging
import hashlib
import secrets
import os
from datetime import datetime, timedelta
from utils.auth_audit import (
    log_auth_event, 
    get_failed_login_count
)

# Configuração de logging
logger = logging.getLogger(__name__)

# Constantes
MAX_LOGIN_ATTEMPTS = 5  # Número máximo de tentativas de login
LOGIN_THROTTLE_MINUTES = 30  # Período de throttle após muitas tentativas
MIN_PASSWORD_LENGTH = 8  # Tamanho mínimo da senha
HASH_ITERATIONS = 10000  # Iterações para PBKDF2
PASSWORD_RESET_EXPIRY_HOURS = 24  # Expiração do token de reset de senha


def check_brute_force(user_email):
    """
    Verifica se há indícios de ataque de força bruta para o usuário
    
    Args:
        user_email: Email do usuário
        
    Returns:
        tuple: (bloqueado, motivo) onde bloqueado é bool e motivo é str
    """
    # Verificar número de falhas recentes
    failed_count = get_failed_login_count(user_email, minutes=LOGIN_THROTTLE_MINUTES)
    
    if failed_count >= MAX_LOGIN_ATTEMPTS:
        # Usuário bloqueado temporariamente
        logger.warning(f"Possível ataque de força bruta para {user_email}: {failed_count} tentativas falhas")
        log_auth_event(
            "brute_force_detection", 
            user_email=user_email, 
            success=False, 
            details={"failed_count": failed_count}
        )
        return True, f"Muitas tentativas de login falhas. Tente novamente após {LOGIN_THROTTLE_MINUTES} minutos."
    
    return False, ""


def validate_password_strength(password):
    """
    Valida a força da senha do usuário
    
    Args:
        password: Senha a ser validada
        
    Returns:
        tuple: (válida, motivo) onde válida é bool e motivo é str
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"A senha deve ter pelo menos {MIN_PASSWORD_LENGTH} caracteres."
    
    # Verificar complexidade (letras, números e caracteres especiais)
    has_number = bool(re.search(r'\d', password))
    has_lowercase = bool(re.search(r'[a-z]', password))
    has_uppercase = bool(re.search(r'[A-Z]', password))
    has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
    
    requirements = []
    if not has_number:
        requirements.append("número")
    if not has_lowercase:
        requirements.append("letra minúscula")
    if not has_uppercase:
        requirements.append("letra maiúscula")
    if not has_special:
        requirements.append("caractere especial")
    
    if requirements:
        return False, f"A senha deve conter pelo menos um: {', '.join(requirements)}."
    
    return True, ""


def generate_secure_token():
    """
    Gera um token seguro para uso em resets de senha ou sessões
    
    Returns:
        str: Token seguro
    """
    # Gerar token seguro de 32 bytes (64 caracteres em hex)
    token = secrets.token_hex(32)
    return token


def hash_password(password, salt=None):
    """
    Gera um hash de senha seguro usando PBKDF2
    
    Args:
        password: Senha a ser hash
        salt: Salt opcional (gerado se não fornecido)
        
    Returns:
        tuple: (hash, salt) onde ambos são strings
    """
    if salt is None:
        salt = os.urandom(16)  # 16 bytes (128 bits) de salt
    
    # Usar PBKDF2 para criar hash
    hash_bytes = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        HASH_ITERATIONS
    )
    
    # Converter para string para armazenamento
    hash_hex = hash_bytes.hex()
    salt_hex = salt.hex()
    
    return hash_hex, salt_hex


def verify_password(password, stored_hash, stored_salt):
    """
    Verifica se a senha corresponde ao hash armazenado
    
    Args:
        password: Senha a verificar
        stored_hash: Hash armazenado
        stored_salt: Salt armazenado
        
    Returns:
        bool: True se a senha corresponder, False caso contrário
    """
    # Converter salt de hex para bytes
    salt = bytes.fromhex(stored_salt)
    
    # Calcular hash com a mesma salt e iterações
    calculated_hash, _ = hash_password(password, salt)
    
    # Verificar se os hashes são iguais
    return calculated_hash == stored_hash


def protect_session():
    """
    Aplicar proteções de segurança à sessão atual
    - Regeneração de ID de sessão após login
    - Proteção contra fixação de sessão
    """
    # Verificar se há mudança de estado de autenticação
    if st.session_state.get("_session_regenerated") != st.session_state.get("authenticated"):
        # Regenerar ID de sessão (conceitual - Streamlit não tem API direta para isso)
        session_id = generate_secure_token()
        st.session_state["_session_id"] = session_id
        st.session_state["_session_regenerated"] = st.session_state.get("authenticated")
        
        # Registrar para auditoria
        user = st.session_state.get("user", {})
        log_auth_event(
            "session_regenerated", 
            user_email=user.get("email"),
            user_id=user.get("uid"),
            details={"new_session_id": session_id}
        )


def create_password_reset_token(user_email):
    """
    Cria um token de redefinição de senha
    
    Args:
        user_email: Email do usuário
        
    Returns:
        tuple: (token, expiry) onde token é string e expiry é timestamp
    """
    token = generate_secure_token()
    expiry = datetime.now() + timedelta(hours=PASSWORD_RESET_EXPIRY_HOURS)
    
    # Registrar evento
    log_auth_event(
        "password_reset_requested", 
        user_email=user_email,
        details={"expiry": expiry.isoformat()}
    )
    
    return token, expiry.timestamp()


def verify_password_reset_token(token, stored_data):
    """
    Verifica se um token de redefinição de senha é válido
    
    Args:
        token: Token a verificar
        stored_data: Dicionário com token e expiry
        
    Returns:
        bool: True se válido, False caso contrário
    """
    if not token or not stored_data:
        return False
    
    stored_token = stored_data.get("token")
    expiry = stored_data.get("expiry")
    
    # Verificar token e expiração
    if token != stored_token:
        return False
    
    if expiry and time.time() > expiry:
        # Token expirado
        return False
    
    return True