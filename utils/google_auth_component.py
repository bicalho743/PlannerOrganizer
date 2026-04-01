"""
Google Auth via Firebase REST API — sem JavaScript SDK.
Gera link OAuth direto para o Google, processa callback com code.
"""
import streamlit as st
import requests
import os
import urllib.parse


def google_login_button():
    api_key = os.getenv("FIREBASE_API_KEY", "")
    if not api_key:
        return

    replit_domain = os.getenv("REPLIT_DEV_DOMAIN", "")
    if replit_domain:
        base_url = f"https://{replit_domain}"
    else:
        base_url = st.context.headers.get("origin", "https://localhost")

    continue_uri = base_url

    try:
        resp = requests.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:createAuthUri?key={api_key}",
            json={"providerId": "google.com", "continueUri": continue_uri},
            timeout=5
        )
        data       = resp.json()
        auth_uri   = data.get("authUri", "")
        session_id = data.get("sessionId", "")

        if not auth_uri:
            return

        parsed = urllib.parse.urlparse(auth_uri)
        qs     = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        original_state = qs.get("state", [""])[0]
        new_state = f"{original_state}__SID__{session_id}"
        qs["state"] = [new_state]
        new_query = urllib.parse.urlencode({k: v[0] for k, v in qs.items()})
        auth_uri  = urllib.parse.urlunparse(parsed._replace(query=new_query))

        st.markdown(f"""
        <a href="{auth_uri}" target="_top" style="
          display:flex; align-items:center; justify-content:center; gap:10px;
          width:100%; padding:11px 16px; text-decoration:none;
          background:rgba(255,255,255,0.06);
          border:1px solid rgba(201,168,76,0.22);
          border-radius:10px; color:rgba(245,240,232,0.75);
          font-size:0.875rem; font-family:'DM Sans',sans-serif;
          box-sizing:border-box; transition:all 0.2s;">
          <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg"
               style="width:18px;height:18px;flex-shrink:0;"/>
          Continuar com Google
        </a>
        """, unsafe_allow_html=True)

    except Exception as e:
        print(f"Erro Google button: {e}")


def handle_google_callback():
    params = st.query_params

    if "google_uid" in params:
        uid   = params.get("google_uid", "")
        email = params.get("google_email", "")
        name  = params.get("google_name", "")
        if uid and email:
            st.query_params.clear()
            return _create_session(uid, email, name)
        return False

    if "code" not in params:
        return False

    code  = params.get("code", "")
    state = params.get("state", "")

    if not code:
        st.query_params.clear()
        return False

    session_id = ""
    if "__SID__" in state:
        session_id = state.split("__SID__")[-1]

    api_key  = os.getenv("FIREBASE_API_KEY", "")
    replit_domain = os.getenv("REPLIT_DEV_DOMAIN", "")
    if replit_domain:
        base_url = f"https://{replit_domain}"
    else:
        base_url = st.context.headers.get("origin", "https://localhost")

    request_uri = base_url

    try:
        resp = requests.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={api_key}",
            json={
                "requestUri":          request_uri,
                "sessionId":           session_id,
                "returnSecureToken":   True,
                "returnIdpCredential": True,
                "postBody":            f"code={code}&providerId=google.com"
            },
            timeout=10
        )
        data = resp.json()
        print(f"Google signInWithIdp response keys: {list(data.keys())}")

        if "error" in data:
            msg = data["error"].get("message", "Erro")
            print(f"Google signInWithIdp error: {msg}")
            st.error(f"Erro no login Google: {msg}")
            st.query_params.clear()
            return False

        uid   = data.get("localId", "")
        email = data.get("email", "")
        name  = data.get("displayName", "")

        if uid and email:
            st.query_params.clear()
            return _create_session(uid, email, name)
        else:
            print(f"Google login: uid ou email vazio. Data: {data}")
            st.query_params.clear()

    except Exception as e:
        print(f"Erro callback Google: {e}")
        st.query_params.clear()

    return False


def _create_session(uid, email, display_name):
    from datetime import datetime, timedelta
    try:
        from utils.firebase_config import TOKEN_EXPIRY
    except Exception:
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
        "empresa": "Planner Organiza",
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
        print(f"Erro DB: {e}")

    try:
        from utils.session_persistence import save_session_to_storage
        save_session_to_storage(session_user, usuario_data, uid)
    except Exception as e:
        print(f"Erro sessao: {e}")

    return True
