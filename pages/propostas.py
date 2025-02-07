import streamlit as st
import pandas as pd

def show():
    st.title("📝 Gestão de Propostas")
    
    tab1, tab2 = st.tabs(["Nova Proposta", "Lista de Propostas"])
    
    with tab1:
        st.subheader("Cadastrar Nova Proposta")
        
        with st.form("cadastro_proposta"):
            # Carregar lista de clientes para seleção
            clientes = st.session_state.db.get_clientes()
            cliente_opcoes = clientes['nome'].tolist()
            
            cliente_nome = st.selectbox("Cliente", cliente_opcoes)
            descricao = st.text_area("Descrição do Serviço")
            valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
            status = st.selectbox("Status", ["Aberta", "Fechada", "Cancelada"])
            
            submitted = st.form_submit_button("Cadastrar Proposta")
            
            if submitted:
                if cliente_nome and descricao and valor > 0:
                    try:
                        cliente_id = clientes[clientes['nome'] == cliente_nome]['id'].iloc[0]
                        st.session_state.db.add_proposta(
                            cliente_id, descricao, valor, status
                        )
                        st.success("Proposta cadastrada com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao cadastrar proposta: {str(e)}")
                else:
                    st.warning("Por favor, preencha todos os campos corretamente.")
    
    with tab2:
        st.subheader("Propostas Cadastradas")
        
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            status_filtro = st.multiselect(
                "Filtrar por Status",
                ["Aberta", "Fechada", "Cancelada"]
            )
        with col2:
            data_filtro = st.date_input("Filtrar por Data")
        
        # Carregar e processar dados
        propostas = st.session_state.db.get_propostas()
        clientes = st.session_state.db.get_clientes()
        
        # Merge para obter nome do cliente
        propostas = propostas.merge(
            clientes[['id', 'nome']],
            left_on='cliente_id',
            right_on='id',
            suffixes=('', '_cliente')
        )
        
        # Aplicar filtros
        if status_filtro:
            propostas = propostas[propostas['status'].isin(status_filtro)]
        
        # Exibir tabela de propostas
        if not propostas.empty:
            st.dataframe(
                propostas[['nome', 'descricao', 'valor', 'status', 'data_proposta']],
                use_container_width=True
            )
        else:
            st.info("Nenhuma proposta encontrada.")
