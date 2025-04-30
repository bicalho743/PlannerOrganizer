"""
Configuração do Firebase para autenticação
"""
import os

# Configuração do Firebase
FIREBASE_CONFIG = {
    "apiKey": os.environ.get("FIREBASE_API_KEY", "AIzaSyAtuIO-4oyI99rQSl9dAMu756FI4q10kcY"),
    "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN", "planner-organizer.firebaseapp.com"),
    "projectId": os.environ.get("FIREBASE_PROJECT_ID", "planner-organizer"),
    "storageBucket": os.environ.get("FIREBASE_STORAGE_BUCKET", "planner-organizer.appspot.com"),
    "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID", "108435556655"),
    "appId": os.environ.get("FIREBASE_APP_ID", "1:108435556655:web:f3355aec87a2142e8fa82f"),
    "databaseURL": os.environ.get("FIREBASE_DATABASE_URL", "https://planner-organizer-default-rtdb.firebaseio.com")
}

# Nome do cookie de autenticação
AUTH_COOKIE_NAME = "planner_organizer_auth"

# Tempo de expiração do token em segundos (padrão: 7 dias)
TOKEN_EXPIRY = 60 * 60 * 24 * 7  # 7 dias