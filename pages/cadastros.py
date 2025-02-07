import streamlit as st
import pandas as pd
from datetime import datetime

def show():
    st.title("📝 Cadastros")

    tab1, tab2 = st.tabs(["Fornecedores", "Assistentes"])

    with tab1:
        st.subheader("Cadastro de Fornecedores")

        # Formulário de cadastro de fornecedor
        with st.form("cadastro_fornecedor", clear_on_submit=True):
            nome = st.text_input("Nome")
            telefone = st.text_input("Telefone")
            endereco = st.text_area("Endereço")
            pix = st.text_input("Chave PIX")
            categoria = st.selectbox(
                "Categoria",
                ["Produtos", "Serviços", "Marcenaria", "Outro"]
            )
            tipo_conta = st.selectbox("Tipo de Conta", ["PF", "PJ"])
            recorrente = st.checkbox("Fornecedor Recorrente")
            observacoes = st.text_area("Observações")

            submitted = st.form_submit_button("Cadastrar")

            if submitted:
                if nome and telefone:
                    try:
                        st.session_state.db.add_fornecedor(
                            nome=nome,
                            descricao=observacoes,
                            valor=0,  # Valor inicial
                            data_vencimento=None,
                            categoria=categoria,
                            tipo_conta=tipo_conta,
                            pix=pix,
                            contato=telefone,
                            recorrente=recorrente,
                            observacoes=observacoes
                        )
                        st.success("Fornecedor cadastrado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao cadastrar fornecedor: {str(e)}")
                else:
                    st.warning("Por favor, preencha todos os campos obrigatórios.")

        # Lista de fornecedores
        st.subheader("Fornecedores Cadastrados")
        fornecedores = st.session_state.db.get_fornecedores()
        if not fornecedores.empty:
            st.dataframe(
                fornecedores[[
                    'nome', 'contato', 'categoria',
                    'tipo_conta', 'pix', 'recorrente'
                ]],
                use_container_width=True
            )
        else:
            st.info("Nenhum fornecedor cadastrado.")

    with tab2:
        st.subheader("Cadastro de Assistentes")

        # Formulário de cadastro de assistente
        with st.form("cadastro_assistente", clear_on_submit=True):
            nome = st.text_input("Nome")
            telefone = st.text_input("Telefone")
            endereco = st.text_area("Endereço")
            pix = st.text_input("Chave PIX")
            observacoes = st.text_area("Observações")

            submitted = st.form_submit_button("Cadastrar")

            if submitted:
                if nome and telefone:
                    try:
                        st.session_state.db.add_assistente(
                            nome=nome,
                            telefone=telefone,
                            endereco=endereco,
                            pix=pix,
                            observacoes=observacoes
                        )
                        st.success("Assistente cadastrado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao cadastrar assistente: {str(e)}")
                else:
                    st.warning("Por favor, preencha todos os campos obrigatórios.")

        # Lista de assistentes
        st.subheader("Assistentes Cadastrados")
        assistentes = st.session_state.db.get_assistentes()
        if not assistentes.empty:
            st.dataframe(
                assistentes[[
                    'nome', 'telefone', 'endereco',
                    'pix', 'data_cadastro'
                ]],
                use_container_width=True
            )
        else:
            st.info("Nenhum assistente cadastrado.")
