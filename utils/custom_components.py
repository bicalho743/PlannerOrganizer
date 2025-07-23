import streamlit as st

def custom_info(message, icon="ℹ️"):
    """
    Cria um elemento de informação customizado com estilo consistente
    que substitui st.info() em todos os módulos da aplicação.
    """
    st.markdown(f"""
    <div style="
        background-color: rgba(255, 255, 255, 0.8) !important;
        border: 1px solid rgba(0, 0, 0, 0.1) !important;
        border-radius: 8px !important;
        padding: 0.75rem 1rem !important;
        margin: 0.5rem 0 !important;
        color: #1e1e1e !important;
        font-weight: 500 !important;
        backdrop-filter: blur(5px) !important;
    ">
        {icon} {message}
    </div>
    """, unsafe_allow_html=True)

def custom_success(message, icon="✅"):
    """Elemento de sucesso customizado"""
    st.markdown(f"""
    <div style="
        background-color: rgba(200, 255, 200, 0.8) !important;
        border: 1px solid rgba(0, 150, 0, 0.3) !important;
        border-radius: 8px !important;
        padding: 0.75rem 1rem !important;
        margin: 0.5rem 0 !important;
        color: #1e1e1e !important;
        font-weight: 500 !important;
        backdrop-filter: blur(5px) !important;
    ">
        {icon} {message}
    </div>
    """, unsafe_allow_html=True)

def custom_warning(message, icon="⚠️"):
    """Elemento de aviso customizado"""
    st.markdown(f"""
    <div style="
        background-color: rgba(255, 255, 200, 0.8) !important;
        border: 1px solid rgba(255, 200, 0, 0.3) !important;
        border-radius: 8px !important;
        padding: 0.75rem 1rem !important;
        margin: 0.5rem 0 !important;
        color: #1e1e1e !important;
        font-weight: 500 !important;
        backdrop-filter: blur(5px) !important;
    ">
        {icon} {message}
    </div>
    """, unsafe_allow_html=True)