import streamlit as st
import pandas as pd
from datetime import datetime

def show():
    st.title("📝 Cadastros")

    tab1, tab2 = st.tabs(["Fornecedores", "Assistentes"])

    with tab1:
        st.subheader("Cadastro de Fornecedores")

        with st.form("cadastro_fornecedor", clear_on_submit=True):
            descricao = st.text_input("Nome/Descrição")
            contato = st.text_input("Contato")
            categoria = st.selectbox(
                "Categoria",
                ["Produtos", "Serviços", "Marcenaria", "Outro"]
            )
            tipo_conta = st.selectbox("Tipo de Conta", ["PF", "PJ"])
            pix = st.text_input("Chave PIX")
            recorrente = st.checkbox("Fornecedor Recorrente")
            observacoes = st.text_area("Observações")

            submitted = st.form_submit_button("Cadastrar")

            if submitted:
                if descricao and contato:
                    try:
                        st.session_state.db.add_fornecedor(
                            descricao=descricao,
                            contato=contato,
                            categoria=categoria,
                            tipo_conta=tipo_conta,
                            pix=pix if pix else None,
                            recorrente=recorrente,
                            observacoes=observacoes if observacoes else None
                        )
                        st.success("Fornecedor cadastrado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao cadastrar fornecedor: {str(e)}")
                else:
                    st.warning("Por favor, preencha Nome/Descrição e Contato.")

        st.subheader("Fornecedores Cadastrados")
        try:
            fornecedores = st.session_state.db.get_fornecedores()
            if not fornecedores.empty:
                # Update column order and selection based on actual database schema
                st.dataframe(
                    fornecedores[[
                        'descricao', 'contato', 'categoria',
                        'tipo_conta', 'pix', 'recorrente'
                    ]].rename(columns={
                        'descricao': 'Nome/Descrição',
                        'contato': 'Contato',
                        'categoria': 'Categoria',
                        'tipo_conta': 'Tipo de Conta',
                        'pix': 'PIX',
                        'recorrente': 'Recorrente'
                    }),
                    use_container_width=True
                )
            else:
                st.info("Nenhum fornecedor cadastrado.")
        except Exception as e:
            st.error(f"Erro ao carregar lista de fornecedores: {str(e)}")

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
                            endereco=endereco if endereco else None,
                            pix=pix if pix else None,
                            observacoes=observacoes if observacoes else None
                        )
                        st.success("Assistente cadastrado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao cadastrar assistente: {str(e)}")
                else:
                    st.warning("Por favor, preencha os campos Nome e Telefone.")

        st.subheader("Assistentes Cadastrados")
        try:
            assistentes = st.session_state.db.get_assistentes()
            if not assistentes.empty:
                st.dataframe(
                    assistentes[[
                        'nome', 'telefone', 'endereco',
                        'pix', 'observacoes'
                    ]].rename(columns={
                        'nome': 'Nome',
                        'telefone': 'Telefone',
                        'endereco': 'Endereço',
                        'pix': 'PIX',
                        'observacoes': 'Observações'
                    }),
                    use_container_width=True
                )
            else:
                st.info("Nenhum assistente cadastrado.")
        except Exception as e:
            st.error(f"Erro ao carregar lista de assistentes: {str(e)}")