import streamlit as st

def apply_page_header():
    """
    Aplica um cabeçalho padronizado em todas as páginas do sistema
    """
    # Adicionando o cabeçalho no topo da página
    st.markdown("""
    <div style="background-color: #1E366F; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; text-align: center;">
        <h2 style="color: white; margin: 0; padding: 0; font-family: 'Poppins', sans-serif;">Planner Organizer</h2>
        <p style="color: #E3F2FD; margin: 0.2rem 0 0 0; padding: 0; font-size: 0.9rem; font-family: 'Poppins', sans-serif;">
            Sistema Profissional de Gestão Personal Organizer
        </p>
    </div>
    """, unsafe_allow_html=True)