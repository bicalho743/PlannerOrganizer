"""
Componente de autenticação Google para Streamlit
Usa arquivo estático servido pelo próprio Replit para evitar
bloqueio do Firebase com origem null (iframe)
"""
import streamlit as st
import streamlit.components.v1 as components
import os

def google_login_button():
    """
    Renderiza o botão de login com Google via iframe apontando
    para o arquivo estático servido pelo próprio domínio do Replit.
    """
    api_key     = os.getenv("FIREBASE_API_KEY", "")
    auth_domain = os.getenv("FIREBASE_AUTH_DOMAIN", "")
    project_id  = os.getenv("FIREBASE_PROJECT_ID", "")
    app_id      = os.getenv("FIREBASE_APP_ID", "")

    # URL base do Replit — usa a variável de ambiente ou detecta pelo referer
    replit_url = os.getenv("REPLIT_DEV_DOMAIN", "")
    if not replit_url:
        replit_url = os.getenv("REPLIT_DEPLOYMENT_URL", "")
    if not replit_url:
        # fallback manual
        replit_url = "e793124a-608d-4baa-9b36-f1c10d18b5f4-00-er4f29bufe88.worf.replit.dev"

    # Montar URL do arquivo estático com as credenciais como query params
    static_url = (
        f"https://{replit_url}/static/google_auth.html"
        f"?apiKey={api_key}"
        f"&authDomain={auth_domain}"
        f"&projectId={project_id}"
        f"&appId={app_id}"
    )

    # HTML que carrega o arquivo estático via iframe e escuta o postMessage
    html = f"""
<style>
  iframe#google-auth-frame {{
    width: 100%;
    border: none;
    height: 72px;
    background: transparent;
  }}
</style>
<iframe id="google-auth-frame" src="{static_url}" allow="popup"></iframe>
<script>
window.addEventListener("message", function(e) {{
  if (e.data && e.data.type === "google_auth_success") {{
    // Redirecionar com os dados como query params para o Streamlit capturar
    const uid   = encodeURIComponent(e.data.uid   || "");
    const email = encodeURIComponent(e.data.email || "");
    const name  = encodeURIComponent(e.data.displayName || "");
    window.parent.location.href =
      window.parent.location.pathname +
      "?google_uid=" + uid +
      "&google_email=" + email +
      "&google_name=" + name;
  }}
}});
</script>
"""
    components.html(html, height=80, scrolling=False)


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
