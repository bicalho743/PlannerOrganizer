"""
Google Auth via Google Identity Services (GIS) + Firebase REST API.
GIS não tem restrição de domínio como o Firebase JS SDK.
O id_token retornado pelo Google é trocado com o Firebase REST API.
"""
import streamlit as st
import streamlit.components.v1 as components
import requests
import os


def _get_google_client_id():
    api_key = os.getenv("FIREBASE_API_KEY", "")
    if not api_key:
        return ""
    try:
        resp = requests.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:createAuthUri?key={api_key}",
            json={"providerId": "google.com", "continueUri": "https://localhost/"},
            timeout=5
        )
        data = resp.json()
        auth_uri = data.get("authUri", "")
        if auth_uri:
            import urllib.parse
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(auth_uri).query)
            return qs.get("client_id", [""])[0]
    except Exception:
        pass
    return ""


def google_login_button():
    client_id = _get_google_client_id()
    if not client_id:
        return

    html = f"""
<!DOCTYPE html><html><head>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:transparent; display:flex; justify-content:center; align-items:center; min-height:40px; }}
#msg {{ font-size:11px; text-align:center; margin-top:5px; color:rgba(245,240,232,0.4); min-height:14px; }}
#msg.err {{ color:#f08080; }}
#msg.ok  {{ color:#38A169; }}
#wrapper {{ width:100%; text-align:center; }}
#custom-btn {{
  display:flex; align-items:center; justify-content:center; gap:10px;
  width:100%; padding:11px 16px;
  background:rgba(255,255,255,0.06);
  border:1px solid rgba(201,168,76,0.22);
  border-radius:10px; color:rgba(245,240,232,0.75);
  font-size:14px; cursor:pointer; transition:all 0.2s;
  font-family:'DM Sans',sans-serif;
}}
#custom-btn:hover {{ background:rgba(255,255,255,0.1); border-color:rgba(201,168,76,0.45); color:#F5F0E8; }}
#custom-btn:disabled {{ opacity:0.5; cursor:not-allowed; }}
#custom-btn img {{ width:18px; height:18px; }}
</style>
</head><body>
<div id="wrapper">
  <button id="custom-btn" onclick="startGoogleLogin()">
    <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg"/>
    Continuar com Google
  </button>
  <div id="msg"></div>
</div>

<script src="https://accounts.google.com/gsi/client"></script>
<script>
var clientReady = false;

function onGsiLoad() {{
  google.accounts.id.initialize({{
    client_id: "{client_id}",
    callback: handleCredentialResponse,
    auto_select: false,
    cancel_on_tap_outside: true
  }});
  clientReady = true;
}}

function handleCredentialResponse(response) {{
  var msg = document.getElementById("msg");
  msg.className = "ok";
  msg.textContent = "Autenticado! Entrando...";
  var token = encodeURIComponent(response.credential);
  window.parent.location.href =
    window.parent.location.pathname +
    "?google_id_token=" + token;
}}

function startGoogleLogin() {{
  var btn = document.getElementById("custom-btn");
  var msg = document.getElementById("msg");
  btn.disabled = true;
  msg.textContent = "Abrindo Google...";

  if (!clientReady) {{
    msg.className = "err";
    msg.textContent = "Carregando... tente novamente.";
    btn.disabled = false;
    return;
  }}

  google.accounts.id.prompt(function(notification) {{
    if (notification.isNotDisplayed()) {{
      msg.textContent = "";
      google.accounts.oauth2.initCodeClient({{
        client_id: "{client_id}",
        scope: "email profile",
        ux_mode: "popup",
        callback: function(resp) {{
          if (resp.code) {{
            msg.className = "ok";
            msg.textContent = "Autenticado! Entrando...";
            var code = encodeURIComponent(resp.code);
            window.parent.location.href =
              window.parent.location.pathname +
              "?google_auth_code=" + code;
          }} else {{
            btn.disabled = false;
            msg.className = "err";
            msg.textContent = "Login cancelado.";
          }}
        }}
      }}).requestCode();
    }}
    if (notification.isSkippedMoment()) {{
      btn.disabled = false;
      msg.textContent = "";
    }}
    if (notification.isDismissedMoment()) {{
      btn.disabled = false;
      msg.textContent = "";
    }}
  }});
}}

if (typeof google !== 'undefined' && google.accounts) {{
  onGsiLoad();
}} else {{
  var checkGsi = setInterval(function() {{
    if (typeof google !== 'undefined' && google.accounts) {{
      clearInterval(checkGsi);
      onGsiLoad();
    }}
  }}, 200);
  setTimeout(function() {{ clearInterval(checkGsi); }}, 5000);
}}
</script>
</body></html>
"""
    components.html(html, height=50, scrolling=False)


def handle_google_callback():
    params = st.query_params

    if "code" in params or "state" in params:
        st.query_params.clear()
        return False

    if "google_id_token" in params:
        return _handle_id_token(params.get("google_id_token", ""))

    if "google_auth_code" in params:
        return _handle_auth_code(params.get("google_auth_code", ""))

    if "google_uid" in params:
        uid   = params.get("google_uid", "")
        email = params.get("google_email", "")
        name  = params.get("google_name", "")
        if uid and email:
            st.query_params.clear()
            return _create_session(uid, email, name)
        return False

    return False


def _handle_id_token(id_token):
    if not id_token:
        return False
    api_key = os.getenv("FIREBASE_API_KEY", "")
    try:
        resp = requests.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={api_key}",
            json={
                "requestUri": "http://localhost",
                "postBody": f"id_token={id_token}&providerId=google.com",
                "returnSecureToken": True,
                "returnIdpCredential": True
            },
            timeout=10
        )
        data = resp.json()
        if "error" in data:
            st.error(f"Erro login Google: {data['error'].get('message', '')}")
            st.query_params.clear()
            return False

        uid   = data.get("localId", "")
        email = data.get("email", "")
        name  = data.get("displayName", "")
        if uid and email:
            st.query_params.clear()
            return _create_session(uid, email, name)
    except Exception as e:
        print(f"Erro id_token: {e}")
    st.query_params.clear()
    return False


def _handle_auth_code(code):
    if not code:
        return False
    api_key = os.getenv("FIREBASE_API_KEY", "")
    try:
        resp = requests.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={api_key}",
            json={
                "requestUri": "http://localhost",
                "postBody": f"code={code}&providerId=google.com",
                "returnSecureToken": True,
                "returnIdpCredential": True
            },
            timeout=10
        )
        data = resp.json()
        if "error" in data:
            st.error(f"Erro login Google: {data['error'].get('message', '')}")
            st.query_params.clear()
            return False

        uid   = data.get("localId", "")
        email = data.get("email", "")
        name  = data.get("displayName", "")
        if uid and email:
            st.query_params.clear()
            return _create_session(uid, email, name)
    except Exception as e:
        print(f"Erro auth_code: {e}")
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
