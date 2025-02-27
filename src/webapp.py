# Renomeado de app.py para webapp.py para evitar conflitos
import streamlit as st
from pages import dashboard, cadastros, propostas, financeiro, relatorios, teste_importacao
from utils.custom_styles import load_custom_styles

# Carregar estilos personalizados
load_custom_styles()

def show():
    # Menu na parte superior
    st.title("Menu Principal")
    
    # Informações do usuário na barra lateral
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
    
    # Menu de navegação horizontal
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        dashboard_btn = st.button("📊 Dashboard", use_container_width=True)
    with col2:
        cadastros_btn = st.button("👥 Cadastros", use_container_width=True)
    with col3:
        propostas_btn = st.button("📝 Propostas", use_container_width=True)
    with col4:
        financeiro_btn = st.button("💰 Financeiro", use_container_width=True)
    with col5:
        relatorios_btn = st.button("📈 Relatórios", use_container_width=True)
    with col6:
        teste_importacao_btn = st.button("🔄 Teste de Importação", use_container_width=True)
    
    # Determinar a página selecionada com base nos botões
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Dashboard"  # Página padrão
    
    if dashboard_btn:
        st.session_state.current_page = "Dashboard"
    elif cadastros_btn:
        st.session_state.current_page = "Cadastros"
    elif propostas_btn:
        st.session_state.current_page = "Propostas"
    elif financeiro_btn:
        st.session_state.current_page = "Financeiro"
    elif relatorios_btn:
        st.session_state.current_page = "Relatórios"
    elif teste_importacao_btn:
        st.session_state.current_page = "Teste de Importação"
    
    pagina = st.session_state.current_page
    
    # Adicionar separador visual após o menu
    st.markdown("---")

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
