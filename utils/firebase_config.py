"""
Configuração do Firebase para autenticação de usuários
"""
import os
import pyrebase
import streamlit as st

# Configuração do Firebase - SUBSTITUA com seus valores
# Estes valores seriam definidos como variáveis de ambiente em produção
FIREBASE_CONFIG = {
    "apiKey": st.secrets.get("FIREBASE_API_KEY", "sua_api_key"),
    "authDomain": st.secrets.get("FIREBASE_AUTH_DOMAIN", "seu_dominio.firebaseapp.com"),
    "projectId": st.secrets.get("FIREBASE_PROJECT_ID", "seu_project_id"),
    "storageBucket": st.secrets.get("FIREBASE_STORAGE_BUCKET", "seu_bucket"),
    "messagingSenderId": st.secrets.get("FIREBASE_MESSAGING_SENDER_ID", "seu_sender_id"),
    "appId": st.secrets.get("FIREBASE_APP_ID", "sua_app_id"),
    "databaseURL": st.secrets.get("FIREBASE_DATABASE_URL", "https://seu_database.firebaseio.com")
}

def initialize_firebase():
    """
    Inicializa a conexão com o Firebase
    """
    try:
        firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
        auth = firebase.auth()
        db = firebase.database()
        return firebase, auth, db
    except Exception as e:
        st.error(f"Erro ao inicializar Firebase: {e}")
        return None, None, None

# Inicializa o Firebase
firebase, auth, db = initialize_firebase()