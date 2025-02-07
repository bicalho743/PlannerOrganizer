import streamlit as st
import pandas as pd

def show():
    st.title("👥 Gestão de Clientes")
    
    # Tabs para organizar as operações
    tab1, tab2 = st.tabs(["Cadastrar Cliente", "Lista de Clientes"])
    
    with tab1:
        st.subheader("Novo Cliente")
        
        # Formulário de cadastro
        with st.form("cadastro_cliente"):
            nome = st.text_input("Nome completo")
            email = st.text_input("E-mail")
            telefone = st.text_input("Telefone")
            endereco = st.text_area("Endereço")
            
            submitted = st.form_submit_button("Cadastrar")
            
            if submitted:
                if nome and email and telefone:
                    try:
                        st.session_state.db.add_cliente(
                            nome, email, telefone, endereco
                        )
                        st.success("Cliente cadastrado com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao cadastrar cliente: {str(e)}")
                else:
                    st.warning("Por favor, preencha todos os campos obrigatórios.")
    
    with tab2:
        st.subheader("Clientes Cadastrados")
        
        # Filtro de busca
        busca = st.text_input("🔍 Buscar cliente", "")
        
        # Carregar e filtrar dados
        clientes = st.session_state.db.get_clientes()
        
        if busca:
            clientes = clientes[
                clientes['nome'].str.contains(busca, case=False) |
                clientes['email'].str.contains(busca, case=False)
            ]
        
        # Exibir tabela de clientes
        if not clientes.empty:
            st.dataframe(
                clientes[['nome', 'email', 'telefone', 'data_cadastro']],
                use_container_width=True
            )
        else:
            st.info("Nenhum cliente encontrado.")
