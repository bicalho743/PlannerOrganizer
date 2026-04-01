"""
Componente Google Auth — abre popup via Blob URL
para evitar problemas de MIME type do Streamlit static
"""
import streamlit as st
import streamlit.components.v1 as components
import os

def google_login_button():
    api_key     = os.getenv("FIREBASE_API_KEY", "")
    auth_domain = os.getenv("FIREBASE_AUTH_DOMAIN", "")
    project_id  = os.getenv("FIREBASE_PROJECT_ID", "")
    app_id      = os.getenv("FIREBASE_APP_ID", "")

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

// Conteúdo do popup como string — será criado via Blob com tipo text/html correto
function getPopupHTML() {{
  return `<!DOCTYPE html><html><head>
<meta charset="UTF-8"/>
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:#0D1B35;font-family:sans-serif;display:flex;
  align-items:center;justify-content:center;min-height:100vh;color:#F5F0E8;}}
.card{{background:rgba(255,255,255,0.06);border:1px solid rgba(201,168,76,0.22);
  border-radius:16px;padding:2rem;text-align:center;max-width:320px;width:90%;}}
h2{{font-size:1.1rem;margin-bottom:.5rem;}}
p{{font-size:.8rem;color:rgba(245,240,232,.5);margin-bottom:1rem;}}
#msg{{font-size:.8rem;margin-top:.75rem;min-height:18px;color:rgba(245,240,232,.5);}}
#msg.err{{color:#f08080;}}
.spin{{width:32px;height:32px;border:3px solid rgba(201,168,76,.2);
  border-top-color:#C9A84C;border-radius:50%;
  animation:sp .8s linear infinite;margin:0 auto 1rem;}}
@keyframes sp{{to{{transform:rotate(360deg)}}}}
</style></head><body>
<div class="card">
  <div class="spin"></div>
  <h2>Autenticando com Google</h2>
  <p>Aguarde um momento...</p>
  <div id="msg"></div>
</div>
<script type="module">
import {{initializeApp}} from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import {{getAuth,signInWithRedirect,getRedirectResult,GoogleAuthProvider}}
  from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";
const app  = initializeApp({{
  apiKey:    "{api_key}",
  authDomain:"{auth_domain}",
  projectId: "{project_id}",
  appId:     "{app_id}"
}});
const auth = getAuth(app);
const prov = new GoogleAuthProvider();
prov.setCustomParameters({{prompt:"select_account"}});
const msg  = document.getElementById("msg");
try {{
  // Verificar se voltou de redirect
const rr = await getRedirectResult(auth);
if (rr && rr.user) {{
  msg.textContent = "Sucesso! Fechando...";
  window.opener && window.opener.postMessage({{
    type:"google_auth_success",
    uid:rr.user.uid,
    email:rr.user.email,
    displayName:rr.user.displayName||""
  }},"*");
  setTimeout(()=>window.close(),600);
  return;
}}
// Iniciar redirect para Google
msg.textContent = "Redirecionando...";
await signInWithRedirect(auth, prov);
}} catch(e) {{
  document.querySelector(".spin").style.display="none";
  msg.className="err";
  msg.textContent = e.message;
  window.opener && window.opener.postMessage({{
    type:"google_auth_error", message:e.message
  }},"*");
  setTimeout(()=>window.close(),2500);
}}
<\/script></body></html>`;
}}

window.openGoogle = function() {{
  var msg = document.getElementById("msg");
  var btn = document.getElementById("btn");
  msg.className = "";
  msg.textContent = "Abrindo Google...";
  btn.disabled = true;

  // Criar Blob com tipo correto text/html
  var blob = new Blob([getPopupHTML()], {{type: "text/html"}});
  var url  = URL.createObjectURL(blob);

  popup = window.open(url, "google_auth",
    "width=480,height=560,left=200,top=100");

  if (!popup || popup.closed) {{
    btn.disabled = false;
    msg.className = "err";
    msg.textContent = "Permita popups para este site.";
    return;
  }}

  var timer = setInterval(function() {{
    if (popup.closed) {{
      clearInterval(timer);
      btn.disabled = false;
      msg.textContent = "";
    }}
  }}, 500);
}};

window.addEventListener("message", function(e) {{
  if (e.data && e.data.type === "google_auth_success") {{
    document.getElementById("msg").textContent = "Autenticado! Entrando...";
    if (popup && !popup.closed) popup.close();
    var uid   = encodeURIComponent(e.data.uid || "");
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
    document.getElementById("msg").textContent = e.data.message || "Erro.";
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