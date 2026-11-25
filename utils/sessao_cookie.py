"""
Login que sobrevive a recarregar a página e às publicações do site.

O Streamlit guarda a sessão só na memória da conexão: recarregar a página, uma queda de rede ou uma publicação nova
(o servidor reinicia) apagavam o login. Agora, ao entrar, o site grava no navegador um cookie `po_sessao` com o id da
conta, a validade e uma assinatura (HMAC-SHA256 com um segredo do servidor). Na abertura seguinte, se o cookie for
válido, a sessão volta sozinha. Sair apaga o cookie.

- O cookie não leva senha nem dados da conta, só o id e a validade; sem o segredo do servidor não dá para forjar.
- Segredo: variável SESSAO_SEGREDO; sem ela, derivado da DATABASE_URL (também secreta e fixa entre publicações).
- Validade: 30 dias desde o último login.
"""
import base64
import hashlib
import hmac
import os
import time

import streamlit as st

COOKIE = "po_sessao"
VALIDADE = 30 * 24 * 3600


def _segredo():
    s = os.environ.get("SESSAO_SEGREDO") or ("po-sessao|" + os.environ.get("DATABASE_URL", "planner-organiza"))
    return hashlib.sha256(s.encode()).digest()


def _b64(b):
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def criar_token(uid, email="", agora=None):
    venc = int((agora or time.time()) + VALIDADE)
    corpo = f"{uid}|{venc}|{_b64(str(email or '').encode())}"
    assin = hmac.new(_segredo(), corpo.encode(), hashlib.sha256).digest()
    return _b64(corpo.encode()) + "." + _b64(assin)


def ler_token(token, agora=None):
    """(uid, email) se o token for válido e não vencido; senão None."""
    try:
        corpo_b64, assin_b64 = str(token).split(".", 1)
        pad = lambda s: s + "=" * (-len(s) % 4)  # noqa: E731
        corpo = base64.urlsafe_b64decode(pad(corpo_b64)).decode()
        certa = hmac.new(_segredo(), corpo.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(certa, base64.urlsafe_b64decode(pad(assin_b64))):
            return None
        uid, venc, email_b64 = corpo.split("|", 2)
        if int(venc) < (agora or time.time()) or not uid:
            return None
        return uid, base64.urlsafe_b64decode(pad(email_b64)).decode()
    except Exception:
        return None


def _js(codigo):
    import streamlit.components.v1 as components
    components.html(f"<script>try{{{codigo}}}catch(e){{}}</script>", height=0)


def gravar(uid, email=""):
    """Grava o cookie de login no navegador (chamado em todo login que dá certo)."""
    token = criar_token(uid, email)
    st.session_state.pop("_sessao_saiu", None)
    _js(f"var d = window.parent.document; d.cookie = '{COOKIE}={token}; path=/; max-age={VALIDADE}; SameSite=Lax'"
        " + (d.location.protocol === 'https:' ? '; Secure' : '');")


def apagar():
    _js(f"var d = window.parent.document; d.cookie = '{COOKIE}=; path=/; max-age=0; SameSite=Lax'"
        " + (d.location.protocol === 'https:' ? '; Secure' : '');")
    st.session_state["_sessao_saiu"] = True


def sair():
    """Botão Sair: marca a saída (o cookie é apagado quando a tela de login abrir, em app.py)."""
    st.session_state["_sessao_saiu"] = True
    # sem isto a tela de boas-vindas via o id da conta ainda na sessão e entrava de novo sozinha
    for k in ("_cookie_sessao", "usuario_id", "user", "usuario", "db"):
        st.session_state.pop(k, None)
    st.session_state.login_page = "login"


def restaurar():
    """Se não está logada e o navegador tem um cookie válido, refaz a sessão (antes da tela de login)."""
    if st.session_state.get("authenticated") or st.session_state.get("_sessao_saiu"):
        return False
    try:
        token = st.context.cookies.get(COOKIE)
    except Exception:
        token = None
    dados = ler_token(token) if token else None
    if not dados:
        return False
    uid, email = dados
    try:
        from utils.database import Database
        db = Database(usuario_id=uid)
        perfil = db.get_perfil_usuario() or {}
    except Exception as e:
        print(f"[sessao] não restaurou {uid}: {e}")
        return False
    email = perfil.get("email") or email
    nome = (perfil.get("nome") or "").strip() or (email.split("@")[0].title() if email else "")
    st.session_state.user = {"localId": uid, "email": email, "idToken": "", "displayName": nome}
    st.session_state.usuario = {"email": email, "nome": nome, "empresa": perfil.get("empresa") or "", "role": "user"}
    st.session_state.usuario_id = uid
    st.session_state.db = db
    st.session_state.authenticated = True
    st.session_state.setdefault("current_page", "Dashboard")
    print(f"[sessao] login restaurado pelo cookie: {uid}")
    return True
