"""
Configuração do Firebase para autenticação
"""
import os

FIREBASE_CONFIG = {
    "apiKey":            os.environ.get("FIREBASE_API_KEY",            "AIzaSyAtuIO-4oyI99rQSl9dAMu756FI4q10kcY"),
    "authDomain":        os.environ.get("FIREBASE_AUTH_DOMAIN",        "planner-organizer-68a23.firebaseapp.com"),
    "projectId":         os.environ.get("FIREBASE_PROJECT_ID",         "planner-organizer-68a23"),
    "storageBucket":     os.environ.get("FIREBASE_STORAGE_BUCKET",     "planner-organizer-68a23.firebasestorage.app"),
    "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID","275264106992"),
    "appId":             os.environ.get("FIREBASE_APP_ID",             "1:275264106992:web:3040a39f4f3530693c6d35"),
    "databaseURL":       os.environ.get("FIREBASE_DATABASE_URL",       "https://planner-organizer-68a23-default-rtdb.firebaseio.com")
}

AUTH_COOKIE_NAME = "planner_organizer_auth"
TOKEN_EXPIRY = 60 * 60 * 24 * 7  # 7 dias