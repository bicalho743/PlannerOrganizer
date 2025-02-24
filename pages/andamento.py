import streamlit as st
from datetime import datetime

def show():
    st.title("📋 Andamento do Trabalho")

    # CSS customizado para garantir alinhamento à esquerda
    st.markdown("""
        <style>
        .element-container {
            width: 100% !important;
        }
        .stMarkdown, .stText {
            text-align: left !important;
        }
        div[data-testid="stText"] {
            text-align: left !important;
            width: 100% !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Buscar dados da proposta selecionada
    proposta = st.session_state.get('proposta_selecionada')
    if not proposta:
        st.warning("Selecione uma proposta primeiro")
        return

    # Container principal com informações básicas da proposta
    with st.container():
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"### Proposta #{proposta['numero']}")
            st.markdown(f"**Cliente:** {proposta['cliente_nome']}")
            st.markdown(f"**Valor Base:** R$ {proposta['valor_base']:.2f}")

        with col2:
            st.markdown(f"**Status:** {proposta['status']}")
            st.markdown(f"**Data Início:** {proposta['data_inicio'].strftime('%d/%m/%Y')}")
            if proposta['data_fim']:
                st.markdown(f"**Data Conclusão:** {proposta['data_fim'].strftime('%d/%m/%Y')}")

    # Seção de Assistentes
    st.markdown("### 👥 Assistentes")
    for assistente in proposta.get('assistentes', []):
        with st.container():
            st.markdown(f"**Nome:** {assistente['nome']}")
            st.markdown(f"**Função:** {assistente['funcao']}")
            st.markdown(f"**Valor:** R$ {assistente['valor']:.2f}")
            st.markdown("---")

    # Seção de Fornecedores
    st.markdown("### 🏢 Fornecedores")
    for fornecedor in proposta.get('fornecedores', []):
        with st.container():
            st.markdown(f"**Nome:** {fornecedor['nome']}")
            st.markdown(f"**Produto/Serviço:** {fornecedor['descricao']}")
            st.markdown(f"**Valor:** R$ {fornecedor['valor']:.2f}")
            st.markdown(f"**Status:** {fornecedor['status']}")
            st.markdown("---")

    # Seção de Etapas
    st.markdown("### 📝 Etapas")
    etapas = st.session_state.db.get_andamentos_proposta(proposta['id'])
    if not etapas.empty:
        for _, etapa in etapas.iterrows():
            with st.container():
                st.markdown(f"**Status:** {etapa['status']}")
                if etapa['observacao']:
                    st.markdown(f"**Observação:** {etapa['observacao']}")
                st.markdown(f"**Data:** {etapa['data'].strftime('%d/%m/%Y')}")
                if etapa['comodo']:
                    st.markdown(f"**Cômodo:** {etapa['comodo']}")
                st.markdown("---")
    else:
        st.info("Nenhuma etapa registrada ainda")

    # Adicionar nova etapa
    st.markdown("### ➕ Adicionar Etapa")
    with st.form("nova_etapa"):
        status = st.selectbox("Status", ["Em Andamento", "Concluído", "Pausado", "Cancelado"])
        comodo = st.text_input("Cômodo")
        observacao = st.text_area("Observação")

        if st.form_submit_button("Adicionar"):
            try:
                st.session_state.db.add_andamento_proposta(
                    proposta_id=proposta['id'],
                    status=status,
                    comodo=comodo,
                    observacao=observacao
                )
                st.success("Etapa adicionada com sucesso!")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Erro ao adicionar etapa: {str(e)}")