"""
Configuração do Firebase para autenticação de usuários
"""
import os
import pyrebase
import streamlit as st

# Configuração do Firebase usando variáveis de ambiente ou secrets
FIREBASE_CONFIG = {
    "apiKey": os.environ.get("FIREBASE_API_KEY", st.secrets.get("FIREBASE_API_KEY", "")),
    "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN", st.secrets.get("FIREBASE_AUTH_DOMAIN", "")),
    "projectId": os.environ.get("FIREBASE_PROJECT_ID", st.secrets.get("FIREBASE_PROJECT_ID", "")),
    "storageBucket": os.environ.get("FIREBASE_STORAGE_BUCKET", st.secrets.get("FIREBASE_STORAGE_BUCKET", "")),
    "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID", st.secrets.get("FIREBASE_MESSAGING_SENDER_ID", "")),
    "appId": os.environ.get("FIREBASE_APP_ID", st.secrets.get("FIREBASE_APP_ID", "")),
    "databaseURL": os.environ.get("FIREBASE_DATABASE_URL", st.secrets.get("FIREBASE_DATABASE_URL", ""))
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