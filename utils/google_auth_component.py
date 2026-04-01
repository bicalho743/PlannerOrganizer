"""
Componente de autenticação Google para Streamlit
Abre google_auth.html como popup real servido pelo Streamlit static
(enableStaticServing = true no config.toml)
"""
import streamlit as st
import streamlit.components.v1 as components
import os

def google_login_button():
    api_key     = os.getenv("FIREBASE_API_KEY", "")
    auth_domain = os.getenv("FIREBASE_AUTH_DOMAIN", "")
    project_id  = os.getenv("FIREBASE_PROJECT_ID", "")
    app_id      = os.getenv("FIREBASE_APP_ID", "")

    # Com enableStaticServing=true, Streamlit serve /app/static/
    # A URL do popup usa window.parent.location.origin para pegar o domínio correto
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
  var msg = document.getElementById("msg");
  var btn = document.getElementById("btn");
  msg.className = "";
  msg.textContent = "Abrindo Google...";
  btn.disabled = true;

  // Pegar o domínio real da janela pai (o Replit)
  var base = window.parent.location.origin;
  var url  = base + "/app/static/google_auth.html"
           + "?apiKey={api_key}"
           + "&authDomain={auth_domain}"
           + "&projectId={project_id}"
           + "&appId={app_id}";

  popup = window.open(url, "google_auth",
    "width=480,height=580,left=200,top=100,resizable=yes");

  if (!popup || popup.closed) {{
    btn.disabled = false;
    msg.className = "err";
    msg.textContent = "Permita popups para este site e tente novamente.";
    return;
  }}

  // Verificar se popup foi fechado manualmente
  var timer = setInterval(function() {{
    if (popup.closed) {{
      clearInterval(timer);
      btn.disabled = false;
      msg.textContent = "";
    }}
  }}, 500);
}};

// Receber dados do popup após autenticação Google
window.addEventListener("message", function(e) {{
  if (e.data && e.data.type === "google_auth_success") {{
    document.getElementById("msg").textContent = "Autenticado! Entrando...";
    if (popup && !popup.closed) popup.close();
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