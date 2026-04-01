"""
Componente de autenticação Google para Streamlit
Abre o google_auth.html como popup real (não iframe)
para que o Firebase reconheça o domínio correto.
"""
import streamlit as st
import streamlit.components.v1 as components
import os

def google_login_button():
    replit_url = os.getenv("REPLIT_DEV_DOMAIN", "")
    if not replit_url:
        replit_url = "e793124a-608d-4baa-9b36-f1c10d18b5f4-00-er4f29bufe88.worf.replit.dev"

    api_key     = os.getenv("FIREBASE_API_KEY", "")
    auth_domain = os.getenv("FIREBASE_AUTH_DOMAIN", "")
    project_id  = os.getenv("FIREBASE_PROJECT_ID", "")
    app_id      = os.getenv("FIREBASE_APP_ID", "")

    static_url = (
        f"https://{replit_url}/app/static/google_auth.html"
        f"?apiKey={api_key}"
        f"&authDomain={auth_domain}"
        f"&projectId={project_id}"
        f"&appId={app_id}"
    )

    html = f"""
<!DOCTYPE html><html><head>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:transparent; }}
#btn {{
  display:flex; align-items:center; justify-content:center; gap:10px;
  width:100%; padding:11px 16px;
  background:rgba(255,255,255,0.06);
  border:1px solid rgba(201,168,76,0.22);
  border-radius:10px; color:rgba(245,240,232,0.75);
  font-size:14px; cursor:pointer; transition:all 0.2s; font-family:sans-serif;
}}
#btn:hover {{ background:rgba(255,255,255,0.1); border-color:rgba(201,168,76,0.45); color:#F5F0E8; }}
#btn img {{ width:18px; height:18px; }}
#msg {{ font-size:11px; text-align:center; margin-top:5px; color:rgba(245,240,232,0.4); min-height:14px; }}
#msg.err {{ color:#f08080; }}
</style>
</head><body>
<button id="btn" onclick="openGoogle()">
  <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg"/>
  Continuar com Google
</button>
<div id="msg"></div>
<script>
var popup = null;

window.openGoogle = function() {{
  document.getElementById("msg").textContent = "Abrindo Google...";
  document.getElementById("btn").disabled = true;
  popup = window.open(
    "{static_url}",
    "google_auth",
    "width=500,height=600,left=200,top=100"
  );
  if (!popup) {{
    document.getElementById("msg").className = "err";
    document.getElementById("msg").textContent = "Permita popups para este site.";
    document.getElementById("btn").disabled = false;
  }}
}};

// Escutar mensagem do popup com os dados do Google
window.addEventListener("message", function(e) {{
  if (e.data && e.data.type === "google_auth_success") {{
    document.getElementById("msg").textContent = "Autenticado! Entrando...";
    if (popup) popup.close();
    var uid   = encodeURIComponent(e.data.uid   || "");
    var email = encodeURIComponent(e.data.email || "");
    var name  = encodeURIComponent(e.data.displayName || "");
    window.parent.location.href =
      window.parent.location.pathname +
      "?google_uid=" + uid +
      "&google_email=" + email +
      "&google_name=" + name;
  }}
  if (e.data && e.data.type === "google_auth_error") {{
    document.getElementById("btn").disabled = false;
    document.getElementById("msg").className = "err";
    document.getElementById("msg").textContent = e.data.message || "Erro no login.";
  }}
}});
</script>
</body></html>
"""
    components.html(html, height=80, scrolling=False)


def handle_google_callback():
    params = st.query_params
    if "google_uid" not in params:
        return False

    uid          = params.get("google_uid", "")
    email        = params.get("google_email", "")
    display_name = params.get("google_name", "")

    if not uid or not email:
        return False

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

    st.query_params.clear()
    return True