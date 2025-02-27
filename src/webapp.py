# Renomeado de app.py para webapp.py para evitar conflitos
import streamlit as st
from pages import dashboard, cadastros, propostas, financeiro, relatorios, teste_importacao
from utils.custom_styles import load_custom_styles

# Carregar estilos personalizados
load_custom_styles()

def show():
    # Menu lateral
    st.sidebar.title("Menu Principal")
    
    # Informações do usuário
    with st.sidebar:
        if st.session_state.usuario and isinstance(st.session_state.usuario, dict):
            st.write(f"👤 Olá, {st.session_state.usuario.get('nome', 'Usuário')}")
        else:
            st.write("👤 Olá, Usuário")

        # Botão de logout
        if st.button("📤 Sair", key="logout_button"):
            st.session_state.autenticado = False
            st.session_state.usuario = None
            st.rerun()

    # Menu de navegação
    pagina = st.sidebar.radio(
        "Menu",
        ["Dashboard", "Cadastros", "Propostas", "Financeiro", "Relatórios", "Teste de Importação"],
        format_func=lambda x: f"📊 {x}" if x == "Dashboard"
                        else f"👥 {x}" if x == "Cadastros"
                        else f"📝 {x}" if x == "Propostas"
                        else f"💰 {x}" if x == "Financeiro"
                        else f"📈 {x}" if x == "Relatórios"
                        else f"🔄 {x}"  # Teste de Importação
    )

    # Roteamento de páginas
    if pagina == "Dashboard":
        dashboard.show()
    elif pagina == "Cadastros":
        cadastros.show()
    elif pagina == "Propostas":
        propostas.show()
    elif pagina == "Financeiro":
        financeiro.show()
    elif pagina == "Relatórios":
        relatorios.show()
    elif pagina == "Teste de Importação":
        teste_importacao.show()

    # Rodapé
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Desenvolvido com ❤️ usando Streamlit")
