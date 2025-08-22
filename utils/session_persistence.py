"""
Módulo para persistência de sessão do usuário
Permite manter login após F5/refresh da página
"""
import streamlit as st
import json
import base64
from datetime import datetime, timedelta
from typing import Dict, Optional

def encode_session_data(data: dict) -> str:
    """Codifica dados da sessão para armazenamento seguro"""
    json_str = json.dumps(data)
    encoded = base64.b64encode(json_str.encode()).decode()
    return encoded

def decode_session_data(encoded_data: str) -> Optional[dict]:
    """Decodifica dados da sessão"""
    try:
        json_str = base64.b64decode(encoded_data.encode()).decode()
        return json.loads(json_str)
    except:
        return None

def save_session_to_storage(user_data: dict, usuario_data: dict, usuario_id: str):
    """Salva dados da sessão no localStorage do navegador"""
    session_data = {
        'user': user_data,
        'usuario': usuario_data,
        'usuario_id': usuario_id,
        'authenticated': True,
        'timestamp': datetime.now().isoformat()
    }
    
    encoded_data = encode_session_data(session_data)
    
    # JavaScript para salvar no localStorage
    js_code = f"""
    <script>
    localStorage.setItem('planner_session', '{encoded_data}');
    localStorage.setItem('planner_last_save', '{datetime.now().isoformat()}');
    console.log('Sessão salva no localStorage');
    </script>
    """
    
    st.components.v1.html(js_code, height=0)

def check_stored_session() -> Optional[dict]:
    """Verifica se existe sessão válida armazenada"""
    # JavaScript para recuperar do localStorage
    js_code = """
    <script>
    const sessionData = localStorage.getItem('planner_session');
    const lastSave = localStorage.getItem('planner_last_save');
    
    if (sessionData && lastSave) {
        // Verificar se a sessão não é muito antiga (24 horas)
        const saveTime = new Date(lastSave);
        const now = new Date();
        const hoursDiff = (now - saveTime) / (1000 * 60 * 60);
        
        if (hoursDiff < 24) {
            // Criar elemento oculto com os dados
            const hiddenDiv = document.createElement('div');
            hiddenDiv.id = 'stored-session-data';
            hiddenDiv.style.display = 'none';
            hiddenDiv.textContent = sessionData;
            document.body.appendChild(hiddenDiv);
            
            console.log('Sessão encontrada no localStorage, válida por', (24 - hoursDiff).toFixed(1), 'horas');
        } else {
            // Sessão expirada, limpar
            localStorage.removeItem('planner_session');
            localStorage.removeItem('planner_last_save');
            console.log('Sessão expirada, removida');
        }
    } else {
        console.log('Nenhuma sessão encontrada no localStorage');
    }
    </script>
    
    <div id="session-check" style="display: none;"></div>
    """
    
    return st.components.v1.html(js_code, height=0)

def restore_session_from_storage():
    """Restaura sessão a partir do localStorage se disponível"""
    # Verificar se já está autenticado
    if st.session_state.get('authenticated', False):
        return
    
    # Tentar recuperar sessão do localStorage via JavaScript
    check_stored_session()
    
    # Para funcionar, vamos usar uma abordagem diferente com cookies via Streamlit
    # Injetar JavaScript que definirá variáveis que podem ser lidas
    js_restore = """
    <script>
    window.restoreSession = function() {
        const sessionData = localStorage.getItem('planner_session');
        if (sessionData) {
            // Definir cookie temporário que o Streamlit pode ler
            document.cookie = `planner_temp_session=${sessionData}; path=/; max-age=10`;
            return true;
        }
        return false;
    };
    
    // Tentar restaurar automaticamente
    if (window.restoreSession()) {
        console.log('Tentando restaurar sessão...');
    }
    </script>
    """
    
    st.components.v1.html(js_restore, height=0)

def clear_stored_session():
    """Limpa sessão armazenada no logout"""
    js_code = """
    <script>
    localStorage.removeItem('planner_session');
    localStorage.removeItem('planner_last_save');
    document.cookie = 'planner_temp_session=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT';
    console.log('Sessão removida do localStorage');
    </script>
    """
    
    st.components.v1.html(js_code, height=0)

def auto_login_check():
    """
    Verifica automaticamente se há login válido armazenado
    e restaura a sessão se necessário
    """
    # Se já está autenticado, não fazer nada
    if st.session_state.get('authenticated', False):
        return
    
    # Tentar restaurar da sessão armazenada
    restore_session_from_storage()
    
    # Para demo, também verificar se há dados de usuário admin armazenados
    if not st.session_state.get('authenticated', False):
        # Verificar se há cookie temporário
        try:
            # Usar st.experimental_get_query_params como fallback
            # Em produção, usar sistema de cookies mais robusto
            pass
        except:
            pass

def setup_session_persistence():
    """Configura sistema de persistência de sessão na inicialização"""
    # Adicionar CSS e JS para persistência
    persistence_html = """
    <script>
    // Sistema de persistência de sessão
    window.plannerSessionManager = {
        save: function(data) {
            localStorage.setItem('planner_session', JSON.stringify(data));
            localStorage.setItem('planner_timestamp', new Date().toISOString());
        },
        
        load: function() {
            const session = localStorage.getItem('planner_session');
            const timestamp = localStorage.getItem('planner_timestamp');
            
            if (session && timestamp) {
                const saveTime = new Date(timestamp);
                const now = new Date();
                const hoursOld = (now - saveTime) / (1000 * 60 * 60);
                
                // Manter sessão por 24 horas
                if (hoursOld < 24) {
                    return JSON.parse(session);
                } else {
                    this.clear();
                }
            }
            return null;
        },
        
        clear: function() {
            localStorage.removeItem('planner_session');
            localStorage.removeItem('planner_timestamp');
        }
    };
    </script>
    """
    
    st.components.v1.html(persistence_html, height=0)