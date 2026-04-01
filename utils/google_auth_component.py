"""
Componente de autenticação Google para Streamlit
Usa Firebase JS SDK via componente HTML para fazer o popup do Google
"""
import streamlit as st
import streamlit.components.v1 as components
import os

def google_login_button():
    """
    Renderiza o botão de login com Google e retorna os dados do usuário
    quando autenticado, ou None se ainda não autenticado.
    """
    api_key      = os.getenv("FIREBASE_API_KEY", "")
    auth_domain  = os.getenv("FIREBASE_AUTH_DOMAIN", "")
    project_id   = os.getenv("FIREBASE_PROJECT_ID", "")
    app_id       = os.getenv("FIREBASE_APP_ID", "")

    html_code = f"""
<!DOCTYPE html>
<html>
<head>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:transparent; font-family:'DM Sans',sans-serif; }}

  #btn-google {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    width: 100%;
    padding: 11px 16px;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(201,168,76,0.22);
    border-radius: 10px;
    color: rgba(245,240,232,0.75);
    font-family: 'DM Sans', sans-serif;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s;
  }}
  #btn-google:hover {{
    background: rgba(255,255,255,0.1);
    border-color: rgba(201,168,76,0.45);
    color: #F5F0E8;
  }}
  #btn-google img {{
    width: 18px; height: 18px;
  }}
  #msg {{
    font-size: 0.75rem;
    text-align: center;
    margin-top: 8px;
    color: rgba(245,240,232,0.4);
    min-height: 18px;
  }}
  #msg.error {{ color: #f08080; }}
</style>
</head>
<body>

<button id="btn-google" onclick="loginGoogle()">
  <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg"/>
  Continuar com Google
</button>
<div id="msg"></div>

<script type="module">
  import {{ initializeApp }} from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
  import {{ getAuth, signInWithPopup, GoogleAuthProvider }}
    from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";

  const firebaseConfig = {{
    apiKey:      "{api_key}",
    authDomain:  "{auth_domain}",
    projectId:   "{project_id}",
    appId:       "{app_id}"
  }};

  const app      = initializeApp(firebaseConfig);
  const auth     = getAuth(app);
  const provider = new GoogleAuthProvider();
  provider.setCustomParameters({{ prompt: "select_account" }});

  window.loginGoogle = async function() {{
    const btn = document.getElementById("btn-google");
    const msg = document.getElementById("msg");
    btn.disabled = true;
    msg.className = "";
    msg.textContent = "Abrindo popup do Google...";

    try {{
      const result  = await signInWithPopup(auth, provider);
      const user    = result.user;
      const token   = await user.getIdToken();

      msg.textContent = "Autenticado! Entrando...";

      // Enviar dados para o Streamlit via postMessage
      window.parent.postMessage({{
        type:         "google_auth_success",
        uid:          user.uid,
        email:        user.email,
        displayName:  user.displayName || "",
        photoURL:     user.photoURL    || "",
        idToken:      token
      }}, "*");

    }} catch (err) {{
      btn.disabled  = false;
      msg.className = "error";
      if (err.code === "auth/popup-closed-by-user") {{
        msg.textContent = "Popup fechado. Tente novamente.";
      }} else if (err.code === "auth/popup-blocked") {{
        msg.textContent = "Popup bloqueado pelo navegador. Permita popups para este site.";
      }} else {{
        msg.textContent = "Erro: " + err.message;
      }}
    }}
  }};
</script>

<!-- Ouvir resposta do Streamlit (confirmação) -->
<script>
  window.addEventListener("message", function(e) {{
    if (e.data && e.data.type === "google_auth_confirmed") {{
      document.getElementById("msg").textContent = "Bem-vinda! Redirecionando...";
    }}
  }});
</script>

</body>
</html>
"""

    # Renderizar o componente e capturar retorno via query params
    components.html(html_code, height=90, scrolling=False)


def handle_google_callback():
    """
    Verifica se há um callback do Google login nos query params
    e processa o login se houver.
    Retorna True se login foi processado, False caso contrário.
    """
    params = st.query_params

    if "google_uid" not in params:
        return False

    uid          = params.get("google_uid", "")
    email        = params.get("google_email", "")
    display_name = params.get("google_name", "")

    if not uid or not email:
        return False

    # Montar sessão igual ao login normal
    from datetime import datetime, timedelta
    from utils.firebase_config import TOKEN_EXPIRY

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

    st.session_state.user         = session_user
    st.session_state.usuario      = usuario_data
    st.session_state.usuario_id   = uid
    st.session_state.authenticated = True
    st.session_state.current_page  = "Dashboard"

    # Inicializar banco
    try:
        from utils.database import Database
        st.session_state.db = Database(usuario_id=uid)
    except Exception as e:
        print(f"Erro ao inicializar DB após Google login: {e}")

    # Salvar sessão persistente
    try:
        from utils.session_persistence import save_session_to_storage
        save_session_to_storage(session_user, usuario_data, uid)
    except Exception as e:
        print(f"Erro ao salvar sessão persistente: {e}")

    # Limpar query params
    st.query_params.clear()

    return True