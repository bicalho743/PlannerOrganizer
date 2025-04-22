"""
Componente de autenticação com Google para Streamlit
Este módulo adiciona um componente HTML personalizado para autenticação com Google
"""
import streamlit as st
import os
import json
from pathlib import Path
try:
    import firebase_admin
    from firebase_admin import credentials, auth
    FIREBASE_ADMIN_AVAILABLE = True
except ImportError:
    FIREBASE_ADMIN_AVAILABLE = False

def load_firebase_auth_html():
    """
    Carrega o HTML do componente de autenticação com Google
    
    Returns:
        str: HTML do componente
    """
    html_path = Path(__file__).parent.parent / ".streamlit" / "firebase_auth.html"
    if not html_path.exists():
        return "<div>Componente de autenticação não encontrado</div>"
    
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    return html_content

def add_google_auth_component(firebase_config):
    """
    Adiciona o componente de autenticação com Google à página
    
    Args:
        firebase_config: Configuração do Firebase (dict)
    """
    if not firebase_config:
        st.warning("Configuração do Firebase não fornecida. Autenticação com Google não disponível.")
        return
    
    try:
        # Carregar o HTML do componente
        html_content = load_firebase_auth_html()
        
        # Adicionar configuração do Firebase ao HTML
        config_json = json.dumps(firebase_config)
        html_with_config = html_content.replace(
            '<div id="firebase-config" style="display: none;"></div>',
            f'<div id="firebase-config" style="display: none;">{config_json}</div>'
        )
        
        # Adicionar o componente à página
        st.components.v1.html(html_with_config, height=100)
        st.write(f"FIREBASE_CONFIG carregado com sucesso. Chaves disponíveis: {', '.join(firebase_config.keys())}")
    except Exception as e:
        st.error(f"Erro ao adicionar componente de autenticação Google: {str(e)}")

def create_google_login_button(label="Entrar com Google", key=None):
    """
    Cria um botão de login com Google
    
    Args:
        label: Texto do botão
        key: Chave única para o botão (opcional)
    """
    try:
        # Criar botão com classe especial para ser detectado pelo JS
        button_html = f"""
        <button 
            onclick="window.googleLogin && window.googleLogin()"
            class="google-login-button"
            style="
                background-color: #4285F4;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                font-size: 16px;
                font-weight: 500;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                width: 100%;
                margin: 10px 0;
            "
        >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" style="margin-right: 10px">
                <path fill="white" d="M12.545,10.239v3.821h5.445c-0.712,2.315-2.647,3.972-5.445,3.972c-3.332,0-6.033-2.701-6.033-6.032s2.701-6.032,6.033-6.032c1.498,0,2.866,0.549,3.921,1.453l2.814-2.814C17.503,2.988,15.139,2,12.545,2C7.021,2,2.543,6.477,2.543,12s4.478,10,10.002,10c8.396,0,10.249-7.85,9.426-11.748L12.545,10.239z"/>
            </svg>
            {label}
        </button>
        """
        
        # Adicionar o botão à página
        st.components.v1.html(button_html, height=60)
        
        # Adicionar um botão alternativo para casos onde o JS falha
        st.markdown('<div style="text-align: center; margin-top: 5px; font-size: 0.8rem;">'
                   '<a href="#" onclick="javascript:window.googleLogin(); return false;">'
                   'Problema com o botão? Clique aqui'
                   '</a></div>', unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Erro ao criar botão de login Google: {str(e)}")
        
        # Fallback em caso de erro
        st.button(f"🔄 {label} (fallback)", key=key or "google_login_fallback")