import streamlit as st
from datetime import datetime

def show():
    st.title("📋 Andamento do Trabalho")
    
    # Buscar dados da proposta selecionada
    proposta = st.session_state.get('proposta_selecionada')
    if not proposta:
        st.warning("Selecione uma proposta primeiro")
        return
        
    # Container principal
    with st.container():
        # Informações básicas da proposta
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(f"Proposta #{proposta['numero']}")
            st.write(f"**Cliente:** {proposta['cliente_nome']}")
            st.write(f"**Valor Base:** R$ {proposta['valor_base']:.2f}")
            
        with col2:
            st.write(f"**Status:** {proposta['status']}")
            st.write(f"**Data Início:** {proposta['data_inicio'].strftime('%d/%m/%Y')}")
            if proposta['data_fim']:
                st.write(f"**Data Conclusão:** {proposta['data_fim'].strftime('%d/%m/%Y')}")
    
    # Seção de Assistentes
    st.subheader("👥 Assistentes")
    for assistente in proposta.get('assistentes', []):
        with st.container():
            st.write(f"**Nome:** {assistente['nome']}")
            st.write(f"**Função:** {assistente['funcao']}")
            st.write(f"**Valor:** R$ {assistente['valor']:.2f}")
            st.write("---")
    
    # Seção de Fornecedores
    st.subheader("🏢 Fornecedores")
    for fornecedor in proposta.get('fornecedores', []):
        with st.container():
            st.write(f"**Nome:** {fornecedor['nome']}")
            st.write(f"**Produto/Serviço:** {fornecedor['descricao']}")
            st.write(f"**Valor:** R$ {fornecedor['valor']:.2f}")
            st.write(f"**Status:** {fornecedor['status']}")
            st.write("---")
    
    # Seção de Etapas
    st.subheader("📝 Etapas")
    etapas = st.session_state.db.get_andamentos_proposta(proposta['id'])
    if not etapas.empty:
        for _, etapa in etapas.iterrows():
            with st.container():
                cols = st.columns([2, 1, 1])
                with cols[0]:
                    st.write(f"**Status:** {etapa['status']}")
                    if etapa['observacao']:
                        st.write(f"**Observação:** {etapa['observacao']}")
                with cols[1]:
                    st.write(f"**Data:** {etapa['data'].strftime('%d/%m/%Y')}")
                with cols[2]:
                    if etapa['comodo']:
                        st.write(f"**Cômodo:** {etapa['comodo']}")
                st.write("---")
    else:
        st.info("Nenhuma etapa registrada ainda")
    
    # Adicionar nova etapa
    st.subheader("➕ Adicionar Etapa")
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
