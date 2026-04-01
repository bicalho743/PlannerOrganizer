"""
Persistência de sessão via localStorage do navegador.
Salva o token do usuário para não perder o login ao recarregar.
"""
import streamlit as st
import streamlit.components.v1 as components
import json

def setup_session_persistence():
    """
    Injeta JS que lê o token salvo no localStorage
    e restaura na URL para o Streamlit capturar.
    """
    components.html("""
    <script>
    (function() {
        var saved = localStorage.getItem('planner_session');
        if (!saved) return;
        try {
            var data = JSON.parse(saved);
            if (!data.uid || !data.email) return;
            // Verificar se expirou (7 dias)
            if (data.expiry && new Date(data.expiry) < new Date()) {
                localStorage.removeItem('planner_session');
                return;
            }
            // Só redirecionar se não há parâmetros de sessão já na URL
            var params = new URLSearchParams(window.location.search);
            if (!params.has('restored_uid') && !params.has('google_uid')) {
                window.parent.location.href =
                    window.parent.location.pathname +
                    '?restored_uid=' + encodeURIComponent(data.uid) +
                    '&restored_email=' + encodeURIComponent(data.email) +
                    '&restored_name=' + encodeURIComponent(data.name || '');
            }
        } catch(e) {
            localStorage.removeItem('planner_session');
        }
    })();
    </script>
    """, height=0)


def save_session_to_storage(session_user, usuario_data, uid):
    """Salva dados da sessão no localStorage via JS."""
    import json
    data = {
        'uid':    uid,
        'email':  session_user.get('email', ''),
        'name':   usuario_data.get('nome', ''),
        'expiry': session_user.get('expiry', '')
    }
    data_json = json.dumps(data).replace("'", "\\'")
    components.html(f"""
    <script>
    localStorage.setItem('planner_session', '{data_json}');
    </script>
    """, height=0)


def clear_stored_session():
    """Remove a sessão do localStorage."""
    components.html("""
    <script>
    localStorage.removeItem('planner_session');
    </script>
    """, height=0)


def check_and_restore_auto_login():
    """
    Verifica se há dados de sessão restaurados nos query params
    e faz o login automático sem pedir senha.
    """
    params = st.query_params

    if 'restored_uid' not in params:
        return False

    uid   = params.get('restored_uid', '')
    email = params.get('restored_email', '')
    name  = params.get('restored_name', '')

    if not uid or not email:
        st.query_params.clear()
        return False

    if st.session_state.get('authenticated'):
        st.query_params.clear()
        return True

    from datetime import datetime, timedelta
    try:
        from utils.firebase_config import TOKEN_EXPIRY
    except:
        TOKEN_EXPIRY = 3600

    session_user = {
        'localId':      uid,
        'email':        email,
        'idToken':      '',
        'refreshToken': '',
        'expiresIn':    TOKEN_EXPIRY,
        'registered':   True,
        'last_login':   datetime.now().isoformat(),
        'expiry':       (datetime.now() + timedelta(seconds=TOKEN_EXPIRY)).isoformat()
    }
    usuario_data = {
        'email':   email,
        'nome':    name or email.split('@')[0].title(),
        'empresa': 'Planner Organiza',
        'role':    'user'
    }

    st.session_state.user          = session_user
    st.session_state.usuario       = usuario_data
    st.session_state.usuario_id    = uid
    st.session_state.authenticated = True
    st.session_state.current_page  = 'Dashboard'

    try:
        from utils.database import Database
        st.session_state.db = Database(usuario_id=uid)
    except Exception as e:
        print(f"Erro DB restore: {e}")

    st.query_params.clear()
    st.rerun()
    return True