import streamlit as st


def require_auth():
    if not st.session_state.get("authenticated", False):
        st.warning("Sessão expirada. Faça login novamente.")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔑 Ir para o login", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.login_page = "login"
                st.rerun()
        st.stop()
