import streamlit as st

def verificar_login():
    """
    Verifica se o usuário está logado e retorna informações básicas
    
    Returns:
        tuple: (usuario_id, usuario_nome, usuario_email) ou (None, None, None) se não estiver logado
    """
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        return None, None, None
    
    # Informações básicas do usuário
    usuario = st.session_state.get('usuario', {})
    usuario_id = usuario.get('id', st.session_state.get('usuario_id'))
    usuario_nome = usuario.get('nome', 'Usuário')
    usuario_email = usuario.get('email', '')
    
    return usuario_id, usuario_nome, usuario_email