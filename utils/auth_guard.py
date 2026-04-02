import streamlit as st


def require_auth():
    if not st.session_state.get("authenticated", False):
        st.warning("Você precisa estar logado para acessar esta página.")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔑 Ir para o login", use_container_width=True):
                st.session_state.current_page = "login"
                st.rerun()
        st.stop()
