import streamlit as st
import pandas as pd
from datetime import datetime

def show():
    st.title("📝 Cadastros")

    tab1, tab2 = st.tabs(["Fornecedores", "Assistentes"])

    with tab1:
        st.subheader("Cadastro de Fornecedores")

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
                            telefone=telefone,
                            endereco=endereco or None,
                            categoria=categoria,
                            tipo_conta=tipo_conta,
                            pix=pix or None,
                            recorrente=recorrente,
                            observacoes=observacoes or None
                        )
                        st.success("Fornecedor cadastrado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao cadastrar fornecedor: {str(e)}")
                else:
                    st.warning("Por favor, preencha todos os campos obrigatórios.")

        # Lista de fornecedores
        try:
            st.subheader("Fornecedores Cadastrados")
            fornecedores = st.session_state.db.get_fornecedores()
            if not fornecedores.empty:
                # Converter data de cadastro para exibição
                fornecedores['data_cadastro'] = pd.to_datetime(fornecedores['data_cadastro'])
                fornecedores['data_cadastro'] = fornecedores['data_cadastro'].dt.strftime('%d/%m/%Y')

                st.dataframe(
                    fornecedores[[
                        'nome', 'telefone', 'categoria',
                        'tipo_conta', 'pix', 'recorrente',
                        'data_cadastro'
                    ]],
                    use_container_width=True
                )
            else:
                st.info("Nenhum fornecedor cadastrado.")
        except Exception as e:
            st.error(f"Erro ao carregar fornecedores: {str(e)}")

    with tab2:
        st.subheader("Cadastro de Assistentes")

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
                            endereco=endereco or None,
                            pix=pix or None,
                            observacoes=observacoes or None
                        )
                        st.success("Assistente cadastrado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao cadastrar assistente: {str(e)}")
                else:
                    st.warning("Por favor, preencha todos os campos obrigatórios.")

        # Lista de assistentes
        try:
            st.subheader("Assistentes Cadastrados")
            assistentes = st.session_state.db.get_assistentes()
            if not assistentes.empty:
                # Converter data de cadastro para exibição
                assistentes['data_cadastro'] = pd.to_datetime(assistentes['data_cadastro'])
                assistentes['data_cadastro'] = assistentes['data_cadastro'].dt.strftime('%d/%m/%Y')

                st.dataframe(
                    assistentes[[
                        'nome', 'telefone', 'endereco',
                        'pix', 'data_cadastro'
                    ]],
                    use_container_width=True
                )
            else:
                st.info("Nenhum assistente cadastrado.")
        except Exception as e:
            st.error(f"Erro ao carregar assistentes: {str(e)}")