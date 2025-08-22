"""
Sistema de auto-login melhorado
Verifica e restaura sessões válidas automaticamente
"""
import streamlit as st
import json
from datetime import datetime, timedelta

def try_restore_session():
    """Tenta restaurar sessão armazenada no navegador"""
    # Se já está autenticado, não fazer nada
    if st.session_state.get('authenticated', False):
        return True
    
    # HTML/JS para verificar localStorage
    check_session_html = """
    <script>
    function checkStoredSession() {
        try {
            const sessionData = localStorage.getItem('planner_session');
            const timestamp = localStorage.getItem('planner_timestamp');
            
            if (sessionData && timestamp) {
                const saveTime = new Date(timestamp);
                const now = new Date();
                const hoursOld = (now - saveTime) / (1000 * 60 * 60);
                
                // Sessão válida por 24 horas
                if (hoursOld < 24) {
                    const data = JSON.parse(sessionData);
                    
                    // Criar formulário oculto para enviar dados ao Streamlit
                    const form = document.createElement('form');
                    form.method = 'POST';
                    form.style.display = 'none';
                    
                    // Adicionar dados como campos ocultos
                    Object.keys(data).forEach(key => {
                        const input = document.createElement('input');
                        input.type = 'hidden';
                        input.name = key;
                        input.value = typeof data[key] === 'object' ? JSON.stringify(data[key]) : data[key];
                        form.appendChild(input);
                    });
                    
                    document.body.appendChild(form);
                    
                    // Mostrar indicador de carregamento
                    const indicator = document.createElement('div');
                    indicator.innerHTML = '🔄 Restaurando sessão...';
                    indicator.style.cssText = 'position:fixed;top:10px;right:10px;background:#4CAF50;color:white;padding:10px;border-radius:5px;z-index:9999;';
                    document.body.appendChild(indicator);
                    
                    // Remover após 3 segundos
                    setTimeout(() => {
                        if (indicator.parentNode) {
                            indicator.parentNode.removeChild(indicator);
                        }
                    }, 3000);
                    
                    return true;
                } else {
                    // Sessão expirada
                    localStorage.removeItem('planner_session');
                    localStorage.removeItem('planner_timestamp');
                }
            }
        } catch (error) {
            console.error('Erro ao verificar sessão:', error);
        }
        return false;
    }
    
    // Executar verificação
    checkStoredSession();
    </script>
    """
    
    st.components.v1.html(check_session_html, height=0)
    return False

def restore_from_url_params():
    """Restaura sessão a partir de parâmetros na URL (método alternativo)"""
    try:
        query_params = st.query_params
        
        if 'restore_session' in query_params and query_params['restore_session'] == 'true':
            # Tentar restaurar sessão demo
            if not st.session_state.get('authenticated', False):
                # Verificar se há indicação de sessão demo
                if 'session_type' in query_params and query_params['session_type'] == 'demo':
                    restore_demo_session()
                    return True
                    
    except Exception as e:
        print(f"Erro ao verificar parâmetros de URL: {str(e)}")
    
    return False

def restore_demo_session():
    """Restaura sessão de demonstração"""
    st.session_state.authenticated = True
    st.session_state.user_id = "admin-demo-user-123"
    st.session_state.usuario_id = "admin-demo-user-123"
    
    user_data = {
        'localId': 'admin-demo-user-123',
        'email': 'admin@plannerorganizer.com',
        'role': 'admin'
    }
    
    usuario_data = {
        'email': 'admin@plannerorganizer.com',
        'nome': 'Administrador',
        'telefone': '',
        'empresa': 'Planner Organizer',
        'role': 'admin'
    }
    
    st.session_state.user = user_data
    st.session_state.usuario = usuario_data
    
    print("DEBUG AUTO-LOGIN: Sessão demo restaurada automaticamente")

def check_and_restore_auto_login():
    """Função principal para verificar e restaurar login automaticamente"""
    # Se já está autenticado, não fazer nada
    if st.session_state.get('authenticated', False):
        return
    
    # Tentar múltiplos métodos de restauração
    restored = False
    
    # 1. Tentar restaurar de localStorage
    try:
        restored = try_restore_session()
    except Exception as e:
        print(f"Erro no auto-login localStorage: {str(e)}")
    
    # 2. Tentar restaurar de parâmetros URL
    if not restored:
        try:
            restored = restore_from_url_params()
        except Exception as e:
            print(f"Erro no auto-login URL params: {str(e)}")
    
    return restored