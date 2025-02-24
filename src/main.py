import streamlit as st
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# Adicionar diretórios ao path para importar módulos
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))
sys.path.append(str(Path(__file__).parent))

from utils.database import Database

# Configuração da página
st.set_page_config(
    page_title="Sistema Personal Organizer",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicialização da base de dados
if 'db' not in st.session_state:
    st.session_state.db = Database()

# Menu lateral personalizado
st.sidebar.title("Menu Principal")
pagina = st.sidebar.radio(
    "",  # Label vazio para não mostrar título do radio
    ["Dashboard", "Propostas", "Cadastros", "Financeiro", "Relatórios"],
    format_func=lambda x: f"📊 {x}" if x == "Dashboard"
                    else f"📝 {x}" if x == "Propostas"
                    else f"👥 {x}" if x == "Cadastros"
                    else f"💰 {x}" if x == "Financeiro"
                    else f"📈 {x}"  # Relatórios
)

# Dashboard - Página Principal
if pagina == "Dashboard":
    st.title("📋 Sistema de Gestão - Personal Organizer")

    # Add test data button in sidebar if database is empty
    clientes = st.session_state.db.get_clientes()
    if clientes.empty:
        st.sidebar.warning("Banco de dados vazio")
        if st.sidebar.button("Adicionar Dados de Teste"):
            if st.session_state.db.add_test_data():
                st.sidebar.success("Dados de teste adicionados com sucesso!")
                st.rerun()
            else:
                st.sidebar.error("Erro ao adicionar dados de teste")

    # Dashboard content
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Resumo")

        # Estatísticas básicas
        clientes = st.session_state.db.get_clientes()
        propostas = st.session_state.db.get_propostas()
        financeiro = st.session_state.db.get_financeiro()

        st.metric("Total de Clientes", len(clientes) if not clientes.empty else 0)
        propostas_ativas = len(propostas[propostas['status'] == 'Aberta']) if not propostas.empty else 0
        st.metric("Propostas Ativas", propostas_ativas)

        # Resumo financeiro
        if not financeiro.empty:
            valores_receber = financeiro[
                (financeiro['tipo'] == 'receita') & 
                (financeiro['tipo_receita'].isin(['organização', 'venda']))
            ]['valor'].sum()
        else:
            valores_receber = 0.0

        st.metric("Valores a Receber", f"R$ {valores_receber:.2f}")

    with col2:
        st.subheader("📋 Propostas em Aberto")
        if not propostas.empty:
            propostas_abertas = propostas[propostas['status'] == 'Aberta']
            if not propostas_abertas.empty:
                for _, p in propostas_abertas.iterrows():
                    with st.expander(f"Proposta #{p['numero']} - {p['descricao']}"):
                        st.write(f"**Valor:** R$ {p['valor']:.2f}")
                        if 'prazo_entrega' in p and p['prazo_entrega']:
                            st.write(f"**Prazo de Entrega:** {p['prazo_entrega']}")
            else:
                st.info("Nenhuma proposta em aberto.")
        else:
            st.info("Nenhuma proposta cadastrada.")

elif pagina == "Cadastros":
    import pages.cadastros as cadastros
    cadastros.show()

elif pagina == "Propostas":
    import pages.propostas as propostas
    propostas.show()

elif pagina == "Financeiro":
    import pages.financeiro as financeiro
    financeiro.show()

elif pagina == "Relatórios":
    import pages.relatorios as relatorios
    relatorios.show()

# Rodapé
st.sidebar.markdown("---")
st.sidebar.markdown("### Desenvolvido com ❤️ usando Streamlit")