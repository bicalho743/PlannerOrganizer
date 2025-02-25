import os
import sys
import streamlit as st
import pandas as pd
from datetime import datetime

# Adicionar diretório raiz ao path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.append(root_dir)

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

# Lista personalizada de páginas visíveis para o usuário
PAGINAS_VISIVEIS = {
    "📊 Visão Geral": "dashboard",
    "👥 Clientes": "clientes",
    "📝 Propostas": "propostas",
    "💰 Financeiro": "financeiro",
    "📋 Cadastros": "cadastros",
    "💳 Contas": "contas_pagar",
    "📈 Relatórios": "relatorios"
}

# Configuração do menu lateral com ícones
st.sidebar.title("🏠 Menu Principal")

pagina = st.sidebar.selectbox(
    "Navegação",
    list(PAGINAS_VISIVEIS.keys())
)

# Extrair o nome da página sem o ícone
page_name = PAGINAS_VISIVEIS[pagina]

# Roteamento de páginas
if page_name == "dashboard":
    from pages import dashboard
    dashboard.show()
elif page_name == "clientes":
    from pages import clientes
    clientes.show()
elif page_name == "propostas":
    from pages import propostas
    propostas.show()
elif page_name == "financeiro":
    from pages import financeiro
    financeiro.show()
elif page_name == "cadastros":
    from pages import cadastros
    cadastros.show()
elif page_name == "contas_pagar":
    from src.hidden_pages import contas_pagar
    contas_pagar.show()
elif page_name == "relatorios":
    from pages import relatorios
    relatorios.show()

# Dashboard - Página Principal
if page_name == "dashboard":
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

    # Dashboard
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

        # Pagamentos Pendentes
        pendentes = st.session_state.db.get_pagamentos_pendentes()
        if not pendentes.empty:
            st.write("---")
            st.subheader("💰 Pagamentos Pendentes")
            total_pendente = pendentes['valor'].sum()
            st.metric("Total Pendente", f"R$ {total_pendente:.2f}")

            for _, p in pendentes.iterrows():
                if p['tipo'] == 'Valor Base':
                    st.write(f"- Proposta #{p['proposta']} - {p['cliente']}: Valor Base (R$ {p['valor']:.2f})")
                elif p['fornecedor']:
                    st.write(f"- Proposta #{p['proposta']} - {p['cliente']}: {p['tipo']} - {p['fornecedor']} (R$ {p['valor']:.2f})")
                else:
                    st.write(f"- Proposta #{p['proposta']} - {p['cliente']}: {p['tipo']} (R$ {p['valor']:.2f})")

    with col2:
        st.subheader("📋 Propostas em Aberto")

        # Propostas em aberto
        if not propostas.empty:
            propostas['data_proposta'] = pd.to_datetime(propostas['data_proposta'])
            propostas_abertas = propostas[propostas['status'] == 'Aberta'].sort_values('data_proposta', ascending=False)

            if not propostas_abertas.empty:
                for _, p in propostas_abertas.iterrows():
                    with st.expander(f"Proposta #{p['numero']} - {p['descricao']}"):
                        st.write(f"**Valor:** R$ {p['valor']:.2f}")
                        st.write(f"**Data:** {p['data_proposta'].strftime('%d/%m/%Y')}")
                        if p['prazo_entrega']:
                            st.write(f"**Prazo de Entrega:** {p['prazo_entrega'].strftime('%d/%m/%Y')}")
            else:
                st.info("Nenhuma proposta em aberto.")
        else:
            st.info("Nenhuma proposta cadastrada.")

        # Aniversariantes
        if not clientes.empty:
            st.write("---")
            st.subheader("🎂 Aniversariantes")
            # Converter data_aniversario para datetime
            clientes['data_aniversario'] = pd.to_datetime(clientes['data_aniversario'])
            hoje = datetime.now()

            # Aniversariantes do dia
            aniversariantes_dia = clientes[
                (clientes['data_aniversario'].dt.day == hoje.day) &
                (clientes['data_aniversario'].dt.month == hoje.month)
            ]

            if not aniversariantes_dia.empty:
                st.write("**🎈 Hoje:**")
                for _, aniv in aniversariantes_dia.iterrows():
                    st.write(f"- {aniv['nome']}")
            else:
                st.write("**🎈 Hoje:** Nenhum aniversariante")

# Rodapé mais discreto
st.sidebar.markdown("---")
st.sidebar.markdown("<div style='text-align: center; color: #888888; font-size: 0.8em;'>Sistema Personal Organizer</div>", unsafe_allow_html=True)