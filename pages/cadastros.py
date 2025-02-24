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
        col1, col2 = st.columns(2)
        with col1:
            telefone = st.text_input("Telefone")
            email = st.text_input("Email")

        # Campos específicos por tipo
        if tipo_cadastro == "Cliente":
            with col2:
                data_aniversario = st.date_input("Data de Aniversário")
                origem_cliente = st.selectbox(
                    "Como conheceu?",
                    ["Indicação", "Instagram", "Facebook", "Google", "Outro"]
                )
            tipo_cliente = st.selectbox("Tipo", ["PF", "PJ"])

        elif tipo_cadastro == "Fornecedor":
            with col2:
                categoria = st.selectbox(
                    "Categoria",
                    ["Produtos", "Serviços", "Marcenaria", "Outro"]
                )
                tipo_conta = st.selectbox("Tipo de Conta", ["PF", "PJ"])
            recorrente = st.checkbox("Fornecedor Recorrente")

        elif tipo_cadastro == "Assistente":
            with col2:
                disponibilidade = st.multiselect(
                    "Disponibilidade",
                    ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"]
                )

        elif tipo_cadastro == "Parceiro":
            with col2:
                area_atuacao = st.text_input("Área de Atuação")
                tipo_parceria = st.selectbox(
                    "Tipo de Parceria",
                    ["Indicação", "Colaboração", "Projeto Conjunto"]
                )

        # Seção de Endereço (comum para todos)
        st.write("---")
        st.subheader("Endereço")
        col1, col2 = st.columns(2)
        with col1:
            estado = st.text_input("Estado (UF)")
            cidade = st.text_input("Cidade")
        with col2:
            bairro = st.text_input("Bairro")
            endereco = st.text_input("Endereço completo (Rua, número, complemento)")

        # Campo comum de observações e PIX
        st.write("---")
        col1, col2 = st.columns(2)
        with col1:
            observacoes = st.text_area("Observações")
        with col2:
            pix = st.text_input("Chave PIX")

        # Botão de submissão
        submitted = st.form_submit_button("Cadastrar")

    # Processamento do formulário (fora do form)
    if submitted:
        try:
            dados_cadastro = {
                "nome": nome,
                "email": email,
                "estado": estado,
                "cidade": cidade,
                "bairro": bairro,
                "endereco": endereco,
                "pix": pix if pix else None,
                "observacoes": observacoes if observacoes else None
            }

            if tipo_cadastro == "Cliente":
                dados_cadastro.update({
                    "telefone": telefone,
                    "data_aniversario": data_aniversario,
                    "origem_cliente": origem_cliente,
                    "tipo_cliente": tipo_cliente
                })
                st.session_state.db.add_cliente(**dados_cadastro)

            elif tipo_cadastro == "Fornecedor":
                # Remove campos que não são usados no add_fornecedor
                fornecedor_data = {
                    "nome": nome,
                    "contato": telefone,  # Usar telefone como contato
                    "categoria": categoria,
                    "tipo_conta": tipo_conta,
                    "estado": estado,
                    "cidade": cidade,
                    "bairro": bairro,
                    "endereco": endereco,
                    "pix": pix if pix else None,
                    "recorrente": recorrente,
                    "observacoes": observacoes if observacoes else None
                }
                st.session_state.db.add_fornecedor(**fornecedor_data)

            elif tipo_cadastro == "Assistente":
                dados_cadastro.update({
                    "telefone": telefone,
                    "disponibilidade": ",".join(disponibilidade) if disponibilidade else None
                })
                st.session_state.db.add_assistente(**dados_cadastro)

            elif tipo_cadastro == "Parceiro":
                dados_cadastro.update({
                    "telefone": telefone,
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
            colunas = ['nome', 'telefone', 'email', 'data_aniversario', 'origem_cliente', 'estado', 'cidade', 'bairro', 'endereco']
            rename = {
                'nome': 'Nome',
                'telefone': 'Telefone',
                'email': 'Email',
                'data_aniversario': 'Aniversário',
                'origem_cliente': 'Origem',
                'estado': 'Estado',
                'cidade': 'Cidade',
                'bairro': 'Bairro',
                'endereco': 'Endereço'
            }
        elif tipo_cadastro == "Fornecedor":
            registros = st.session_state.db.get_fornecedores()
            colunas = ['nome', 'contato', 'categoria', 'tipo_conta', 'recorrente', 'estado', 'cidade', 'bairro', 'endereco']
            rename = {
                'nome': 'Nome',
                'contato': 'Telefone',
                'categoria': 'Categoria',
                'tipo_conta': 'Tipo de Conta',
                'recorrente': 'Recorrente',
                'estado': 'Estado',
                'cidade': 'Cidade',
                'bairro': 'Bairro',
                'endereco': 'Endereço'
            }
        elif tipo_cadastro == "Assistente":
            registros = st.session_state.db.get_assistentes()
            colunas = ['nome', 'telefone', 'email', 'disponibilidade', 'estado', 'cidade', 'bairro', 'endereco']
            rename = {
                'nome': 'Nome',
                'telefone': 'Telefone',
                'email': 'Email',
                'disponibilidade': 'Disponibilidade',
                'estado': 'Estado',
                'cidade': 'Cidade',
                'bairro': 'Bairro',
                'endereco': 'Endereço'
            }
        elif tipo_cadastro == "Parceiro":
            registros = st.session_state.db.get_parceiros()
            colunas = ['nome', 'telefone', 'area_atuacao', 'tipo_parceria', 'estado', 'cidade', 'bairro', 'endereco']
            rename = {
                'nome': 'Nome',
                'telefone': 'Telefone',
                'area_atuacao': 'Área de Atuação',
                'tipo_parceria': 'Tipo de Parceria',
                'estado': 'Estado',
                'cidade': 'Cidade',
                'bairro': 'Bairro',
                'endereco': 'Endereço'
            }

        if not registros.empty:
            # Exibir registros com botões de ação
            for idx, registro in registros.iterrows():
                with st.expander(f"{registro['nome']} ({registro['telefone'] if 'telefone' in registro else registro.get('contato', '')})"):
                    # Exibir informações do registro
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        for col in colunas:
                            if col in registro and registro[col]:
                                st.write(f"**{rename[col]}:** {registro[col]}")

                    # Botões de ação
                    with col2:
                        edit_key = f"edit_{tipo_cadastro}_{registro['id']}"
                        delete_key = f"delete_{tipo_cadastro}_{registro['id']}"

                        with st.form(f"actions_{edit_key}"):
                            if st.form_submit_button("✏️ Editar"):
                                st.session_state[edit_key] = True
                                st.rerun()

                        with st.form(f"actions_{delete_key}"):
                            if st.form_submit_button("🗑️ Excluir"):
                                if st.session_state.get(f'confirm_delete_{tipo_cadastro}_{registro["id"]}', False):
                                    try:
                                        if tipo_cadastro == "Cliente":
                                            st.session_state.db.delete_cliente(registro['id'])
                                        elif tipo_cadastro == "Fornecedor":
                                            st.session_state.db.delete_fornecedor(registro['id'])
                                        elif tipo_cadastro == "Assistente":
                                            st.session_state.db.delete_assistente(registro['id'])
                                        elif tipo_cadastro == "Parceiro":
                                            st.session_state.db.delete_parceiro(registro['id'])
                                        st.success(f"{tipo_cadastro} excluído com sucesso!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro ao excluir {tipo_cadastro}: {str(e)}")
                                else:
                                    st.session_state[f'confirm_delete_{tipo_cadastro}_{registro["id"]}'] = True
                                    st.warning(f"Confirma a exclusão de {registro['nome']}?")
                                    st.rerun()

                    # Formulário de edição
                    if st.session_state.get(edit_key, False):
                        with st.form(f"edit_form_{tipo_cadastro}_{registro['id']}"):
                            st.subheader("Editar Registro")
                            edited_data = {}

                            # Campos comuns
                            edited_data['nome'] = st.text_input("Nome", value=registro['nome'])

                            # Campo de telefone/contato
                            if tipo_cadastro == "Fornecedor":
                                edited_data['contato'] = st.text_input("Telefone", value=registro.get('contato', ''))
                            else:
                                edited_data['telefone'] = st.text_input("Telefone", value=registro.get('telefone', ''))

                            edited_data['email'] = st.text_input("Email", value=registro.get('email', ''))

                            # Campos específicos
                            if tipo_cadastro == "Cliente":
                                edited_data['data_aniversario'] = st.date_input("Data de Aniversário", value=registro.get('data_aniversario'))
                                edited_data['origem_cliente'] = st.selectbox("Como conheceu?", 
                                    ["Indicação", "Instagram", "Facebook", "Google", "Outro"],
                                    index=["Indicação", "Instagram", "Facebook", "Google", "Outro"].index(registro.get('origem_cliente', 'Outro')))

                            elif tipo_cadastro == "Fornecedor":
                                edited_data['categoria'] = st.selectbox("Categoria",
                                    ["Produtos", "Serviços", "Marcenaria", "Outro"],
                                    index=["Produtos", "Serviços", "Marcenaria", "Outro"].index(registro.get('categoria', 'Outro')))
                                edited_data['recorrente'] = st.checkbox("Fornecedor Recorrente", value=registro.get('recorrente', False))

                            elif tipo_cadastro == "Assistente":
                                disponibilidade_atual = registro.get('disponibilidade', '').split(',') if registro.get('disponibilidade') else []
                                edited_data['disponibilidade'] = st.multiselect("Disponibilidade",
                                    ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"],
                                    default=disponibilidade_atual)

                            elif tipo_cadastro == "Parceiro":
                                edited_data['area_atuacao'] = st.text_input("Área de Atuação", value=registro.get('area_atuacao', ''))
                                edited_data['tipo_parceria'] = st.selectbox("Tipo de Parceria",
                                    ["Indicação", "Colaboração", "Projeto Conjunto"],
                                    index=["Indicação", "Colaboração", "Projeto Conjunto"].index(registro.get('tipo_parceria', 'Indicação')))

                            # Campos de endereço
                            edited_data['estado'] = st.text_input("Estado (UF)", value=registro.get('estado', ''))
                            edited_data['cidade'] = st.text_input("Cidade", value=registro.get('cidade', ''))
                            edited_data['bairro'] = st.text_input("Bairro", value=registro.get('bairro', ''))
                            edited_data['endereco'] = st.text_input("Endereço", value=registro.get('endereco', ''))

                            col1, col2 = st.columns(2)
                            with col1:
                                if st.form_submit_button("Salvar"):
                                    try:
                                        if tipo_cadastro == "Cliente":
                                            st.session_state.db.update_cliente(registro['id'], **edited_data)
                                        elif tipo_cadastro == "Fornecedor":
                                            st.session_state.db.update_fornecedor(registro['id'], **edited_data)
                                        elif tipo_cadastro == "Assistente":
                                            if 'disponibilidade' in edited_data and edited_data['disponibilidade']:
                                                edited_data['disponibilidade'] = ','.join(edited_data['disponibilidade'])
                                            st.session_state.db.update_assistente(registro['id'], **edited_data)
                                        elif tipo_cadastro == "Parceiro":
                                            st.session_state.db.update_parceiro(registro['id'], **edited_data)

                                        st.session_state[edit_key] = False
                                        st.success("Registro atualizado com sucesso!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro ao atualizar registro: {str(e)}")

                            with col2:
                                if st.form_submit_button("Cancelar"):
                                    st.session_state[edit_key] = False
                                    st.rerun()

        else:
            st.info(f"Nenhum {tipo_cadastro.lower()} cadastrado.")

    except Exception as e:
        st.error(f"Erro ao carregar lista de {tipo_cadastro.lower()}s: {str(e)}")