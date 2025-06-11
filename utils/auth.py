"""
Simple authentication utilities for standalone apps
"""
import streamlit as st

def check_authentication():
    """
    Check if user is authenticated
    For standalone apps without Firebase, this can be simplified
    """
    # If using Firebase auth
    if hasattr(st.session_state, 'authenticated') and st.session_state.authenticated:
        return True
    
    # If using firebase_auth module
    try:
        from utils.firebase_auth import firebase_auth
        if firebase_auth and hasattr(st.session_state, 'usuario') and st.session_state.usuario:
            return True
    except ImportError:
        pass
    
    # For standalone apps, always return True (no auth required)
    # This can be changed based on specific requirements
    return True

def get_current_user():
    """
    Get current authenticated user
    """
    if hasattr(st.session_state, 'usuario') and st.session_state.usuario:
        return st.session_state.usuario
    
    # Return a default user for standalone apps
    return {"id": "default_user", "email": "user@example.com"}

def require_authentication():
    """
    Decorator or function to require authentication
    """
    if not check_authentication():
        st.error("Você precisa estar logado para acessar esta página.")
        st.stop()
        return False
    return True