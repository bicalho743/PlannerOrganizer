"""
Google Auth via Firebase REST API — sem JavaScript SDK.
Gera link OAuth com response_type=code (query param, legível pelo Streamlit).
"""
import streamlit as st
import requests
import os
import urllib.parse


def _get_base_url():
    origin = st.context.headers.get("origin", "")
    if origin:
        return origin.rstrip("/")
    replit_domain = os.getenv("REPLIT_DEV_DOMAIN", "localhost")
    return f"https://{replit_domain}"


def _get_firebase_api_key():
    key = os.getenv("FIREBASE_API_KEY", "")
    if not key:
        try:
            from utils.firebase_config import FIREBASE_CONFIG
            key = FIREBASE_CONFIG.get("apiKey", "")
        except Exception:
            pass
    return key


def google_login_button():
    api_key = _get_firebase_api_key()
    if not api_key:
        return

    base_url = _get_base_url()
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

        qs["response_type"] = ["code"]

        for drop in ("response_mode", "nonce", "include_profile"):
            qs.pop(drop, None)

        qs["access_type"] = ["offline"]
        qs["prompt"] = ["select_account"]

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

    api_key  = _get_firebase_api_key()
    base_url = _get_base_url()

    google_client_id     = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")

    if google_client_secret:
        try:
            token_resp = requests.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code":          code,
                    "client_id":     google_client_id or "275264106992-d59h4ub40gs6kqk5k3drm8kghdv5rpt4.apps.googleusercontent.com",
                    "client_secret": google_client_secret,
                    "redirect_uri":  base_url,
                    "grant_type":    "authorization_code",
                },
                timeout=10
            )
            token_data = token_resp.json()
            print(f"Google token exchange keys: {list(token_data.keys())}")

            if "error" in token_data:
                print(f"Google token exchange error: {token_data}")
                st.error(f"Erro na troca do código Google: {token_data.get('error_description', token_data.get('error'))}")
                st.query_params.clear()
                return False

            google_id_token = token_data.get("id_token", "")
            if google_id_token:
                resp = requests.post(
                    f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={api_key}",
                    json={
                        "requestUri":          base_url,
                        "postBody":            f"id_token={google_id_token}&providerId=google.com",
                        "returnSecureToken":   True,
                        "returnIdpCredential": True,
                    },
                    timeout=10
                )
                data = resp.json()
                print(f"Google signInWithIdp response keys: {list(data.keys())}")
            else:
                print("No id_token in Google token response")
                st.query_params.clear()
                return False

        except Exception as e:
            print(f"Erro token exchange: {e}")
            st.query_params.clear()
            return False
    else:
        try:
            callback_url = f"{base_url}?code={urllib.parse.quote(code, safe='')}"
            resp = requests.post(
                f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={api_key}",
                json={
                    "requestUri":          callback_url,
                    "sessionId":           session_id,
                    "returnSecureToken":   True,
                    "returnIdpCredential": True,
                },
                timeout=10
            )
            data = resp.json()
            print(f"Google signInWithIdp response keys: {list(data.keys())}")
        except Exception as e:
            print(f"Erro callback Google: {e}")
            st.query_params.clear()
            return False

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

    print(f"Google login: uid ou email vazio. Data: {data}")
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
