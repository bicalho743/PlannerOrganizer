"""
Configuração do Firebase para autenticação

Este módulo configura o acesso ao Firebase (Authentication) para o projeto.
As variáveis de ambiente são usadas para armazenar configurações sensíveis.
"""
import os
import json
import logging

# Configuração de logging
logger = logging.getLogger(__name__)

# Diretório para armazenar configurações
CONFIG_DIR = "config"
FIREBASE_CONFIG_FILE = os.path.join(CONFIG_DIR, "firebase_config.json")

# Constantes para autenticação
AUTH_COOKIE_NAME = "firebase_auth_token"
TOKEN_EXPIRY = 60 * 60 * 24 * 7  # 7 dias em segundos

# Criar diretório config se não existir
os.makedirs(CONFIG_DIR, exist_ok=True)


def get_firebase_config():
    """
    Obtém a configuração do Firebase a partir de variáveis de ambiente ou arquivo.
    
    Returns:
        dict: Configuração do Firebase ou None se não disponível
    """
    # Verificar se as variáveis de ambiente estão disponíveis
    api_key = os.environ.get("FIREBASE_API_KEY")
    auth_domain = os.environ.get("FIREBASE_AUTH_DOMAIN")
    project_id = os.environ.get("FIREBASE_PROJECT_ID")
    
    # Se todas as variáveis essenciais estiverem disponíveis, usar elas
    if api_key and auth_domain and project_id:
        config = {
            "apiKey": api_key,
            "authDomain": auth_domain,
            "projectId": project_id,
            "storageBucket": os.environ.get("FIREBASE_STORAGE_BUCKET", ""),
            "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID", ""),
            "appId": os.environ.get("FIREBASE_APP_ID", "")
        }
        return config
    else:
        # Tentar ler do arquivo de configuração
        try:
            if os.path.exists(FIREBASE_CONFIG_FILE):
                with open(FIREBASE_CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                return config
        except Exception as e:
            logger.warning(f"Erro ao ler arquivo de configuração do Firebase: {str(e)}")
    
    # Se não encontrou configuração, retornar None
    logger.warning("Configuração do Firebase não encontrada. Algumas funcionalidades de autenticação não estarão disponíveis.")
    return None


def save_firebase_config(config):
    """
    Salva a configuração do Firebase em um arquivo local.
    
    Args:
        config: Dicionário com a configuração do Firebase
        
    Returns:
        bool: True se salvou com sucesso, False caso contrário
    """
    try:
        with open(FIREBASE_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar configuração do Firebase: {str(e)}")
        return False


def firebase_enabled():
    """
    Verifica se a integração com Firebase está habilitada.
    
    Returns:
        bool: True se habilitada, False caso contrário
    """
    config = get_firebase_config()
    return config is not None


# Exportar a configuração
firebase_config = get_firebase_config()
FIREBASE_CONFIG = firebase_config  # Para compatibilidade com o código existente