"""
Google Auth via Firebase REST API
Sem iframe, sem popup — redireciona a página inteira para o Google
e processa o callback no Streamlit.
"""
import streamlit as st
import requests
import os

def google_login_button():
    """Exibe botão que redireciona a página inteira para o Google OAuth."""
    api_key     = os.getenv("FIREBASE_API_KEY", "")
    # URL base do app — pega dinamicamente dos headers do Streamlit
    base_url    = st.context.headers.get("origin", "")
    if not base_url:
        base_url = "https://e793124a-608d-4baa-9b36-f1c10d18b5f4-00-er4f29bufe88.worf.replit.dev"

    continue_uri = base_url + "/"

    # Chamar Firebase REST API para gerar a URL do Google OAuth
    try:
        resp = requests.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:createAuthUri?key={api_key}",
            json={
                "providerId":  "google.com",
                "continueUri": continue_uri
            },
            timeout=5
        )
        data     = resp.json()
        auth_uri = data.get("authUri", "")
        session_id = data.get("sessionId", "")

        if auth_uri:
            # Salvar sessionId para validar o callback depois
            st.session_state["google_session_id"] = session_id

            # Botão que redireciona a página inteira — sem iframe!
            st.markdown(f"""
            <a href="{auth_uri}" style="
              display:flex; align-items:center; justify-content:center; gap:10px;
              width:100%; padding:11px 16px; text-decoration:none;
              background:rgba(255,255,255,0.06);
              border:1px solid rgba(201,168,76,0.22);
              border-radius:10px; color:rgba(245,240,232,0.75);
              font-size:0.875rem; font-family:'DM Sans',sans-serif;
              transition:all 0.2s; box-sizing:border-box;">
              <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg"
                   style="width:18px;height:18px;"/>
              Continuar com Google
            </a>
            """, unsafe_allow_html=True)
        else:
            st.warning("Não foi possível gerar o link do Google.")

    except Exception as e:
        st.warning(f"Google login indisponível: {e}")


def handle_google_callback():
    """
    Processa o callback do Google OAuth.
    Chamado quando a URL contém ?code=... ou ?state=...
    """
    params = st.query_params

    # Callback do Google — tem 'code' e 'state' na URL
    if "code" not in params and "google_uid" not in params:
        return False

    api_key    = os.getenv("FIREBASE_API_KEY", "")
    session_id = st.session_state.get("google_session_id", "")

    # Processar callback direto com uid (fluxo anterior ainda compatível)
    if "google_uid" in params:
        uid          = params.get("google_uid", "")
        email        = params.get("google_email", "")
        display_name = params.get("google_name", "")
        if uid and email:
            return _create_session(uid, email, display_name)
        return False

    # Processar callback OAuth com code
    code = params.get("code", "")
    if not code:
        return False

    try:
        # Trocar o code pelo token Firebase via REST
        resp = requests.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={api_key}",
            json={
                "requestUri":   st.context.headers.get("origin", "") + "/",
                "sessionId":    session_id,
                "postBody":     f"code={code}&providerId=google.com",
                "returnSecureToken": True,
                "returnIdpCredential": True
            },
            timeout=10
        )
        data = resp.json()

        if "error" in data:
            st.error(f"Erro Google login: {data['error'].get('message', '')}")
            st.query_params.clear()
            return False

        uid          = data.get("localId", "")
        email        = data.get("email", "")
        display_name = data.get("displayName", "")

        if uid and email:
            st.query_params.clear()
            return _create_session(uid, email, display_name)

    except Exception as e:
        print(f"Erro callback Google: {e}")
        st.query_params.clear()

    return False


def _create_session(uid, email, display_name):
    """Cria a sessão do usuário após autenticação Google."""
    from datetime import datetime, timedelta
    try:
        from utils.firebase_config import TOKEN_EXPIRY
    except:
        TOKEN_EXPIRY = 3600

    session_user = {
        "localId":      uid,
        "email":        email,
        "idToken":      "",
        "refreshToken": "",
        "expiresIn":    TOKEN_EXPIRY,
        "registered":   True,
        "last_login":   datetime.now().isoformat(),
        "expiry":       (datetime.now() + timedelta(seconds=TOKEN_EXPIRY)).isoformat()
    }

    usuario_data = {
        "email":   email,
        "nome":    display_name or email.split("@")[0].title(),
        "empresa": "Planner Organizer",
        "role":    "user"
    }

    st.session_state.user          = session_user
    st.session_state.usuario       = usuario_data
    st.session_state.usuario_id    = uid
    st.session_state.authenticated = True
    st.session_state.current_page  = "Dashboard"

    try:
        from utils.database import Database
        st.session_state.db = Database(usuario_id=uid)
    except Exception as e:
        print(f"Erro DB Google login: {e}")

    try:
        from utils.session_persistence import save_session_to_storage
        save_session_to_storage(session_user, usuario_data, uid)
    except Exception as e:
        print(f"Erro sessão persistente: {e}")

    return True