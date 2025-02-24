import streamlit as st
import pandas as pd
from datetime import datetime

def show():
    st.title("👥 Cadastros")

    # Seletor de tipo de cadastro
    tipo_cadastro = st.selectbox(
        "Tipo de Cadastro",
        ["Cliente", "Fornecedor", "Assistente", "Parceiro"]
    )

    # Formulário específico para cada tipo
    with st.form(f"cadastro_{tipo_cadastro.lower()}", clear_on_submit=True):
        # Campos comuns
        nome = st.text_input("Nome")
        telefone = st.text_input("Telefone")
        email = st.text_input("Email")

        # Campos específicos por tipo
        if tipo_cadastro == "Cliente":
            data_aniversario = st.date_input("Data de Aniversário")
            origem_cliente = st.selectbox(
                "Como conheceu?",
                ["Indicação", "Instagram", "Facebook", "Google", "Outro"]
            )
            tipo_cliente = st.selectbox("Tipo", ["PF", "PJ"])

        elif tipo_cadastro == "Fornecedor":
            categoria = st.selectbox(
                "Categoria",
                ["Produtos", "Serviços", "Marcenaria", "Outro"]
            )
            tipo_conta = st.selectbox("Tipo de Conta", ["PF", "PJ"])
            recorrente = st.checkbox("Fornecedor Recorrente")

        elif tipo_cadastro == "Assistente":
            endereco = st.text_area("Endereço")
            disponibilidade = st.multiselect(
                "Disponibilidade",
                ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"]
            )

        elif tipo_cadastro == "Parceiro":
            area_atuacao = st.text_input("Área de Atuação")
            tipo_parceria = st.selectbox(
                "Tipo de Parceria",
                ["Indicação", "Colaboração", "Projeto Conjunto"]
            )

        # Campo comum de observações
        observacoes = st.text_area("Observações")
        pix = st.text_input("Chave PIX")

        submitted = st.form_submit_button("Cadastrar")

        if submitted:
            try:
                dados_cadastro = {
                    "nome": nome,
                    "telefone": telefone,
                    "email": email,
                    "observacoes": observacoes if observacoes else None,
                    "pix": pix if pix else None,
                    "tipo_cadastro": tipo_cadastro
                }

                if tipo_cadastro == "Cliente":
                    dados_cadastro.update({
                        "data_aniversario": data_aniversario,
                        "origem_cliente": origem_cliente,
                        "tipo_cliente": tipo_cliente
                    })
                    st.session_state.db.add_cliente(**dados_cadastro)

                elif tipo_cadastro == "Fornecedor":
                    dados_cadastro.update({
                        "categoria": categoria,
                        "tipo_conta": tipo_conta,
                        "recorrente": recorrente
                    })
                    st.session_state.db.add_fornecedor(**dados_cadastro)

                elif tipo_cadastro == "Assistente":
                    dados_cadastro.update({
                        "endereco": endereco,
                        "disponibilidade": ",".join(disponibilidade) if disponibilidade else None
                    })
                    st.session_state.db.add_assistente(**dados_cadastro)

                elif tipo_cadastro == "Parceiro":
                    dados_cadastro.update({
                        "area_atuacao": area_atuacao,
                        "tipo_parceria": tipo_parceria
                    })
                    st.session_state.db.add_parceiro(**dados_cadastro)

                st.success(f"{tipo_cadastro} cadastrado com sucesso!")
                st.rerun()

            except Exception as e:
                st.error(f"Erro ao cadastrar {tipo_cadastro.lower()}: {str(e)}")

    # Lista de cadastros do tipo selecionado
    st.subheader(f"Lista de {tipo_cadastro}s")
    try:
        if tipo_cadastro == "Cliente":
            registros = st.session_state.db.get_clientes()
            colunas = ['nome', 'telefone', 'email', 'data_aniversario', 'origem_cliente']
            rename = {
                'nome': 'Nome',
                'telefone': 'Telefone',
                'email': 'Email',
                'data_aniversario': 'Aniversário',
                'origem_cliente': 'Origem'
            }
        elif tipo_cadastro == "Fornecedor":
            registros = st.session_state.db.get_fornecedores()
            colunas = ['nome', 'telefone', 'categoria', 'tipo_conta', 'recorrente']
            rename = {
                'nome': 'Nome',
                'telefone': 'Telefone',
                'categoria': 'Categoria',
                'tipo_conta': 'Tipo de Conta',
                'recorrente': 'Recorrente'
            }
        elif tipo_cadastro == "Assistente":
            registros = st.session_state.db.get_assistentes()
            colunas = ['nome', 'telefone', 'email', 'endereco', 'disponibilidade']
            rename = {
                'nome': 'Nome',
                'telefone': 'Telefone',
                'email': 'Email',
                'endereco': 'Endereço',
                'disponibilidade': 'Disponibilidade'
            }
        elif tipo_cadastro == "Parceiro":
            registros = st.session_state.db.get_parceiros()
            colunas = ['nome', 'telefone', 'area_atuacao', 'tipo_parceria']
            rename = {
                'nome': 'Nome',
                'telefone': 'Telefone',
                'area_atuacao': 'Área de Atuação',
                'tipo_parceria': 'Tipo de Parceria'
            }

        if not registros.empty:
            st.dataframe(
                registros[colunas].rename(columns=rename),
                use_container_width=True
            )
        else:
            st.info(f"Nenhum {tipo_cadastro.lower()} cadastrado.")

    except Exception as e:
        st.error(f"Erro ao carregar lista de {tipo_cadastro.lower()}s: {str(e)}")