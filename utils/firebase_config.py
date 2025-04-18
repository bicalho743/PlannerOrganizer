"""
Configuração do Firebase para autenticação de usuários
"""
import os
import streamlit as st
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração do Firebase - SUBSTITUA com seus valores
# Estes valores seriam definidos como variáveis de ambiente em produção
FIREBASE_CONFIG = {
    "apiKey": st.secrets.get("FIREBASE_API_KEY", "AIzaSyA8xzYgZXCkZ-97RWQZXtMpvLVf1Jx8wjk"),
    "authDomain": st.secrets.get("FIREBASE_AUTH_DOMAIN", "planner-organizer.firebaseapp.com"),
    "projectId": st.secrets.get("FIREBASE_PROJECT_ID", "planner-organizer"),
    "storageBucket": st.secrets.get("FIREBASE_STORAGE_BUCKET", "planner-organizer.appspot.com"),
    "messagingSenderId": st.secrets.get("FIREBASE_MESSAGING_SENDER_ID", "695046724018"),
    "appId": st.secrets.get("FIREBASE_APP_ID", "1:695046724018:web:98d8feec0c6b6c937d57fd"),
    "databaseURL": st.secrets.get("FIREBASE_DATABASE_URL", "https://planner-organizer-default-rtdb.firebaseio.com")
}

def initialize_firebase():
    """
    Inicializa a conexão com o Firebase
    """
    try:
        import pyrebase
        firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
        auth = firebase.auth()
        db = firebase.database()
        logger.info("Firebase inicializado com sucesso!")
        return firebase, auth, db
    except ImportError:
        logger.warning("Biblioteca pyrebase não encontrada. Usando modo de demonstração.")
        return None, None, None
    except Exception as e:
        logger.error(f"Erro ao inicializar Firebase: {e}")
        return None, None, None

# Tenta inicializar o Firebase
try:
    firebase, auth, db = initialize_firebase()
    if auth is None:
        logger.warning("Firebase Auth não inicializado, usando modo de demonstração.")
except Exception as e:
    logger.error(f"Falha ao configurar Firebase: {e}")
    firebase, auth, db = None, None, None