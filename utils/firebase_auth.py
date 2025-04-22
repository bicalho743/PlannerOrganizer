"""
Integração com Firebase Authentication

Este módulo fornece funções para autenticação usando Firebase.
Ele permite login, registro, recuperação de senha e login com Google.
"""
import os
import streamlit as st
import requests
import json
import logging
from utils.firebase_config import firebase_config

# Configuração de logging
logger = logging.getLogger(__name__)

# URLs base do Firebase Auth REST API
FIREBASE_AUTH_BASE_URL = "https://identitytoolkit.googleapis.com/v1"
FIREBASE_AUTH_RESET_URL = "https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode"


class FirebaseAuth:
    """Classe para gerenciar autenticação com Firebase"""
    
    def __init__(self, config=None):
        """
        Inicializa o serviço de autenticação Firebase
        
        Args:
            config: Configuração do Firebase (dict)
        """
        self.config = config or firebase_config
        self.api_key = self.config.get("apiKey") if self.config else None
        
        if not self.config or not self.api_key:
            logger.warning("Configuração do Firebase não fornecida. Autenticação desabilitada.")
    
    def login(self, email, password):
        """
        Realiza o login usando email e senha
        
        Args:
            email: Email do usuário
            password: Senha do usuário
            
        Returns:
            dict: Resultado da operação com detalhes do usuário
        """
        if not self.api_key:
            return {"success": False, "error": "Firebase não configurado"}
        
        # Payload da requisição
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        
        # URL completa
        url = f"{FIREBASE_AUTH_BASE_URL}/accounts:signInWithPassword?key={self.api_key}"
        
        try:
            # Fazer requisição para o Firebase
            response = requests.post(url, json=payload)
            data = response.json()
            
            # Verificar erro
            if "error" in data:
                error_message = self._translate_error(data["error"]["message"])
                return {"success": False, "error": error_message}
            
            # Extrair informações do usuário
            user_data = {
                "uid": data.get("localId"),
                "email": data.get("email"),
                "displayName": data.get("displayName", ""),
                "photoURL": data.get("photoUrl", ""),
                "idToken": data.get("idToken"),
                "refreshToken": data.get("refreshToken"),
                "expiresIn": data.get("expiresIn")
            }
            
            # Armazenar token na sessão
            st.session_state["firebase_token"] = data.get("idToken")
            
            return {"success": True, "user": user_data}
        
        except Exception as e:
            logger.error(f"Erro ao fazer login no Firebase: {str(e)}")
            return {"success": False, "error": f"Erro de comunicação: {str(e)}"}
    
    def register(self, email, password, display_name=""):
        """
        Registra um novo usuário
        
        Args:
            email: Email do usuário
            password: Senha do usuário
            display_name: Nome de exibição (opcional)
            
        Returns:
            dict: Resultado da operação com detalhes do usuário
        """
        if not self.api_key:
            return {"success": False, "error": "Firebase não configurado"}
        
        # Payload da requisição
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        
        # URL completa
        url = f"{FIREBASE_AUTH_BASE_URL}/accounts:signUp?key={self.api_key}"
        
        try:
            # Fazer requisição para o Firebase
            response = requests.post(url, json=payload)
            data = response.json()
            
            # Verificar erro
            if "error" in data:
                error_message = self._translate_error(data["error"]["message"])
                return {"success": False, "error": error_message}
            
            # Se tiver nome, atualizar perfil
            if display_name:
                self._update_profile(data.get("idToken"), display_name)
            
            # Extrair informações do usuário
            user_data = {
                "uid": data.get("localId"),
                "email": data.get("email"),
                "displayName": display_name,
                "idToken": data.get("idToken"),
                "refreshToken": data.get("refreshToken"),
                "expiresIn": data.get("expiresIn")
            }
            
            return {"success": True, "user": user_data}
        
        except Exception as e:
            logger.error(f"Erro ao registrar usuário no Firebase: {str(e)}")
            return {"success": False, "error": f"Erro de comunicação: {str(e)}"}
    
    def reset_password(self, email):
        """
        Envia email de recuperação de senha
        
        Args:
            email: Email do usuário
            
        Returns:
            dict: Resultado da operação
        """
        if not self.api_key:
            return {"success": False, "error": "Firebase não configurado"}
        
        # Payload da requisição
        payload = {
            "requestType": "PASSWORD_RESET",
            "email": email
        }
        
        # URL completa
        url = f"{FIREBASE_AUTH_RESET_URL}?key={self.api_key}"
        
        try:
            # Fazer requisição para o Firebase
            response = requests.post(url, json=payload)
            data = response.json()
            
            # Verificar erro
            if "error" in data:
                error_message = self._translate_error(data["error"]["message"])
                return {"success": False, "error": error_message}
            
            return {"success": True}
        
        except Exception as e:
            logger.error(f"Erro ao solicitar recuperação de senha: {str(e)}")
            return {"success": False, "error": f"Erro de comunicação: {str(e)}"}
    
    def logout(self):
        """
        Realiza o logout
        
        Returns:
            dict: Resultado da operação
        """
        # Limpar token da sessão
        if "firebase_token" in st.session_state:
            del st.session_state["firebase_token"]
        
        return {"success": True}
    
    def _update_profile(self, id_token, display_name, photo_url=""):
        """
        Atualiza o perfil do usuário
        
        Args:
            id_token: Token de ID do usuário
            display_name: Nome de exibição
            photo_url: URL da foto de perfil (opcional)
            
        Returns:
            dict: Resultado da operação
        """
        if not id_token:
            return {"success": False, "error": "Token não fornecido"}
        
        # Payload da requisição
        payload = {
            "idToken": id_token,
            "displayName": display_name,
            "photoUrl": photo_url,
            "returnSecureToken": False
        }
        
        # URL completa
        url = f"{FIREBASE_AUTH_BASE_URL}/accounts:update?key={self.api_key}"
        
        try:
            # Fazer requisição para o Firebase
            response = requests.post(url, json=payload)
            data = response.json()
            
            # Verificar erro
            if "error" in data:
                error_message = self._translate_error(data["error"]["message"])
                logger.error(f"Erro ao atualizar perfil: {error_message}")
                return {"success": False, "error": error_message}
            
            return {"success": True}
        
        except Exception as e:
            logger.error(f"Erro ao atualizar perfil: {str(e)}")
            return {"success": False, "error": f"Erro de comunicação: {str(e)}"}
    
    def generate_google_login_url(self, redirect_url):
        """
        Gera URL para autenticação com Google
        
        Args:
            redirect_url: URL para redirecionamento após autenticação
            
        Returns:
            tuple: (URL de autenticação, parâmetros)
        """
        if not self.api_key or not self.config:
            logger.warning("Configuração do Firebase insuficiente para login com Google.")
            return "#", {}
        
        # Obter os dados necessários do config
        project_id = self.config.get("projectId")
        auth_domain = self.config.get("authDomain")
        
        if not project_id or not auth_domain:
            logger.warning("projectId ou authDomain não encontrados na configuração.")
            return "#", {}
        
        # Gerar state para segurança (anti-CSRF)
        import uuid
        state = str(uuid.uuid4())
        
        # Parâmetros para o OAuth
        params = {
            "client_id": f"{project_id}.apps.googleusercontent.com",
            "redirect_uri": redirect_url,
            "response_type": "token id_token",
            "scope": "email profile",
            "state": state,
        }
        
        # Construir URL
        base_url = f"https://accounts.google.com/o/oauth2/auth"
        param_string = "&".join([f"{k}={v}" for k, v in params.items()])
        auth_url = f"{base_url}?{param_string}"
        
        return auth_url, params
    
    def process_google_auth(self, id_token):
        """
        Processa autenticação com Google após redirecionamento
        
        Args:
            id_token: Token de ID fornecido pelo Google
            
        Returns:
            dict: Resultado da operação com detalhes do usuário
        """
        if not self.api_key:
            return {"success": False, "error": "Firebase não configurado"}
        
        # URL para verificar o token
        url = f"{FIREBASE_AUTH_BASE_URL}/accounts:signInWithIdp?key={self.api_key}"
        
        # Payload da requisição
        payload = {
            "postBody": f"id_token={id_token}&providerId=google.com",
            "requestUri": "http://localhost",  # Não é usado pelo Firebase, mas é necessário
            "returnIdpCredential": True,
            "returnSecureToken": True
        }
        
        try:
            # Fazer requisição para o Firebase
            response = requests.post(url, json=payload)
            data = response.json()
            
            # Verificar erro
            if "error" in data:
                error_message = self._translate_error(data["error"]["message"])
                return {"success": False, "error": error_message}
            
            # Extrair informações do usuário
            user_data = {
                "uid": data.get("localId"),
                "email": data.get("email"),
                "displayName": data.get("displayName", ""),
                "photoURL": data.get("photoUrl", ""),
                "idToken": data.get("idToken"),
                "refreshToken": data.get("refreshToken"),
                "expiresIn": data.get("expiresIn"),
                "provider": "google.com"
            }
            
            # Armazenar token na sessão
            st.session_state["firebase_token"] = data.get("idToken")
            
            return {"success": True, "user": user_data}
        
        except Exception as e:
            logger.error(f"Erro ao processar autenticação com Google: {str(e)}")
            return {"success": False, "error": f"Erro de comunicação: {str(e)}"}
    
    def _translate_error(self, error_code):
        """
        Traduz códigos de erro do Firebase para mensagens amigáveis
        
        Args:
            error_code: Código de erro do Firebase
            
        Returns:
            str: Mensagem de erro traduzida
        """
        error_messages = {
            "EMAIL_EXISTS": "Este email já está sendo usado por outra conta.",
            "OPERATION_NOT_ALLOWED": "O login com email/senha está desativado para este projeto.",
            "TOO_MANY_ATTEMPTS_TRY_LATER": "Muitas tentativas. Tente novamente mais tarde.",
            "EMAIL_NOT_FOUND": "Email não encontrado. Verifique seu email ou crie uma nova conta.",
            "INVALID_PASSWORD": "Senha inválida. Verifique sua senha ou use a opção de recuperação.",
            "USER_DISABLED": "Esta conta foi desativada por um administrador.",
            "WEAK_PASSWORD": "A senha deve ter pelo menos 6 caracteres.",
            "INVALID_EMAIL": "O formato do email é inválido.",
            "MISSING_EMAIL": "O email é obrigatório.",
            "MISSING_PASSWORD": "A senha é obrigatória."
        }
        
        return error_messages.get(error_code, f"Erro: {error_code}")


# Instância global do Firebase Auth
firebase_auth = FirebaseAuth() if firebase_config else None