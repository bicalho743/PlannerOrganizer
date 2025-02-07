import streamlit as st
import pandas as pd
from datetime import datetime

def show():
    st.title("👥 Gestão de Clientes")

    # Tabs para organizar as operações
    tab1, tab2 = st.tabs(["Cadastrar Cliente", "Lista de Clientes"])

    with tab1:
        st.subheader("Novo Cliente")

        # Formulário de cadastro
        with st.form("cadastro_cliente"):
            nome = st.text_input("Nome completo")
            cpf = st.text_input("CPF")
            email = st.text_input("E-mail")
            telefone = st.text_input("Telefone")
            data_aniversario = st.date_input("Data de Aniversário")
            endereco = st.text_area("Endereço")
            origem_cliente = st.selectbox(
                "Onde conheceu a Personal Organizer?",
                ["Indicação", "Redes Sociais", "Site", "Evento", "Outro"]
            )

            submitted = st.form_submit_button("Cadastrar")

            if submitted:
                if nome and cpf and telefone:
                    try:
                        st.session_state.db.add_cliente(
                            nome=nome,
                            email=email,
                            telefone=telefone,
                            endereco=endereco,
                            cpf=cpf,
                            data_aniversario=data_aniversario,
                            origem_cliente=origem_cliente
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
                clientes['email'].str.contains(busca, case=False) |
                clientes['cpf'].str.contains(busca, case=False)
            ]

        # Exibir tabela de clientes
        if not clientes.empty:
            st.dataframe(
                clientes[[
                    'nome', 'cpf', 'email', 'telefone', 
                    'data_aniversario', 'origem_cliente',
                    'data_cadastro'
                ]],
                use_container_width=True
            )
        else:
            st.info("Nenhum cliente encontrado.")