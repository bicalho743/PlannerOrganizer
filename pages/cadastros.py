import streamlit as st
from datetime import datetime
import pandas as pd
from utils.importador import importar_cadastros, gerar_template_csv

def show():
    st.title("📋 Cadastros")

    # Tabs para diferentes tipos de cadastro
    tab_cliente, tab_fornecedor, tab_parceiro, tab_assistente = st.tabs([
        "👥 Clientes",
        "🏢 Fornecedores",
        "🤝 Parceiros",
        "👨‍💼 Assistentes"
    ])

    with tab_cliente:
        from pages import clientes
        clientes.show()

    with tab_fornecedor:
        fornecedor_tab1, fornecedor_tab2 = st.tabs(["Cadastrar/Listar", "Importar"])

        with fornecedor_tab1:
            st.subheader("Cadastro de Fornecedores")
            # Form de cadastro de fornecedor
            with st.form("cadastro_fornecedor", clear_on_submit=True):
                nome = st.text_input("Nome/Razão Social")
                col1, col2 = st.columns(2)
                with col1:
                    contato = st.text_input("Telefone")
                    email = st.text_input("Email")
                    categoria = st.selectbox(
                        "Categoria",
                        ["Produtos", "Serviços", "Marcenaria", "Outro"]
                    )
                with col2:
                    tipo_conta = st.selectbox("Tipo de Conta", ["PF", "PJ"])
                    pix = st.text_input("Chave PIX")
                    recorrente = st.checkbox("Fornecedor Recorrente")

                observacoes = st.text_area("Observações")
                submitted = st.form_submit_button("Cadastrar Fornecedor")

                if submitted:
                    try:
                        st.session_state.db.add_fornecedor(
                            nome=nome,
                            contato=contato,
                            email=email,
                            categoria=categoria,
                            tipo_conta=tipo_conta,
                            pix=pix,
                            recorrente=recorrente,
                            observacoes=observacoes
                        )
                        st.success("Fornecedor cadastrado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao cadastrar fornecedor: {str(e)}")

            # Lista de cadastros do tipo selecionado
            st.subheader(f"Lista de Fornecedores")
            try:
                registros = st.session_state.db.get_fornecedores()
                # Certificar que temos registros antes de tentar acessar
                if not isinstance(registros, pd.DataFrame):
                    st.error("Erro ao carregar fornecedores: dados inválidos")
                    return

                if registros.empty:
                    st.info("Nenhum fornecedor cadastrado.")
                    return

                # Definir apenas as colunas que sabemos que existem
                colunas = ['nome', 'contato', 'categoria', 'tipo_conta', 'recorrente']
                colunas_display = []

                # Verificar quais colunas existem no DataFrame
                for col in colunas:
                    if col in registros.columns:
                        colunas_display.append(col)

                # Criar dicionário de renomeação apenas para colunas existentes
                rename = {
                    'nome': 'Nome',
                    'contato': 'Telefone',
                    'categoria': 'Categoria',
                    'tipo_conta': 'Tipo de Conta',
                    'recorrente': 'Recorrente'
                }

                # Criar uma cópia do DataFrame apenas com as colunas existentes
                df_display = registros[colunas_display].copy()

                # Renomear colunas para exibição
                df_display.columns = [rename[col] for col in colunas_display]

                # Exibir tabela
                st.dataframe(df_display, hide_index=True)

                # Botões de ação abaixo da tabela
                col1, col2 = st.columns(2)
                with col1:
                    registro_id = st.number_input("ID do registro para ação:", min_value=1, 
                                                  max_value=len(registros), step=1)

                with col2:
                    acao = st.selectbox("Ação:", ["Editar", "Excluir"])

                # Formulário de ação
                with st.form(f"acao_registro_fornecedor"):
                    if st.form_submit_button(f"Confirmar {acao}"):
                        registro = registros[registros['id'] == registro_id].iloc[0]

                        if acao == "Excluir":
                            try:
                                st.session_state.db.delete_fornecedor(registro_id)
                                st.success(f"Fornecedor excluído com sucesso!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao excluir Fornecedor: {str(e)}")

                        elif acao == "Editar":
                            st.session_state[f'editing_{registro_id}'] = True
                            st.rerun()

                # Formulário de edição
                if st.session_state.get(f'editing_{registro_id}', False):
                    with st.form(f"edit_form_{registro_id}"):
                        st.subheader("Editar Registro")
                        edited_data = {}
                        registro = registros[registros['id'] == registro_id].iloc[0]

                        # Campos comuns
                        edited_data['nome'] = st.text_input("Nome", value=registro['nome'])
                        edited_data['email'] = st.text_input("Email", value=registro.get('email', ''))
                        edited_data['contato'] = st.text_input("Telefone", value=registro.get('contato', ''))

                        # Campos específicos
                        edited_data['categoria'] = st.selectbox(
                            "Categoria",
                            ["Produtos", "Serviços", "Marcenaria", "Outro"],
                            index=["Produtos", "Serviços", "Marcenaria", "Outro"].index(registro.get('categoria', 'Outro'))
                        )
                        edited_data['recorrente'] = st.checkbox("Fornecedor Recorrente", value=registro.get('recorrente', False))

                        # Campos de endereço
                        edited_data['estado'] = st.text_input("Estado (UF)", value=registro.get('estado', ''))
                        edited_data['cidade'] = st.text_input("Cidade", value=registro.get('cidade', ''))
                        edited_data['bairro'] = st.text_input("Bairro", value=registro.get('bairro', ''))
                        edited_data['endereco'] = st.text_input("Endereço", value=registro.get('endereco', ''))

                        # Botões do formulário
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("Salvar"):
                                try:
                                    st.session_state.db.update_fornecedor(registro_id, **edited_data)
                                    st.session_state[f'editing_{registro_id}'] = False
                                    st.success("Registro atualizado com sucesso!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao atualizar registro: {str(e)}")

                        with col2:
                            if st.form_submit_button("Cancelar"):
                                st.session_state[f'editing_{registro_id}'] = False
                                st.rerun()

            except Exception as e:
                st.error(f"Erro ao carregar lista de fornecedores: {str(e)}")

        with fornecedor_tab2:
            st.subheader("Importar Fornecedores")

            # Botão para baixar template
            template = gerar_template_csv("Fornecedor")
            st.download_button(
                "📝 Baixar Template Fornecedor",
                template,
                "template_fornecedor.csv",
                "text/csv",
                help="Baixe este template, preencha com seus dados e faça upload para importar fornecedores"
            )

            # Upload do arquivo
            arquivo = st.file_uploader("Selecione o arquivo CSV de Fornecedores", type=['csv'])

            if arquivo:
                if st.button("Importar Fornecedores"):
                    with st.spinner("Importando dados..."):
                        sucesso, mensagem = importar_cadastros(arquivo, "Fornecedor", st.session_state.db)
                        if sucesso:
                            st.success(mensagem)
                        else:
                            st.error(mensagem)


    with tab_parceiro:
        parceiro_tab1, parceiro_tab2 = st.tabs(["Cadastrar/Listar", "Importar"])

        with parceiro_tab1:
            st.subheader("Cadastro de Parceiros")
            # Form de cadastro de parceiro
            with st.form("cadastro_parceiro", clear_on_submit=True):
                nome = st.text_input("Nome")
                col1, col2 = st.columns(2)
                with col1:
                    telefone = st.text_input("Telefone")
                    email = st.text_input("Email")
                with col2:
                    area_atuacao = st.text_input("Área de Atuação")
                    tipo_parceria = st.selectbox(
                        "Tipo de Parceria",
                        ["Indicação", "Colaboração", "Projeto Conjunto"]
                    )

                observacoes = st.text_area("Observações")
                submitted = st.form_submit_button("Cadastrar Parceiro")

                if submitted:
                    try:
                        st.session_state.db.add_parceiro(
                            nome=nome,
                            telefone=telefone,
                            email=email,
                            area_atuacao=area_atuacao,
                            tipo_parceria=tipo_parceria,
                            observacoes=observacoes
                        )
                        st.success("Parceiro cadastrado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao cadastrar parceiro: {str(e)}")

            # Lista de cadastros do tipo selecionado
            st.subheader(f"Lista de Parceiros")
            try:
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
                    # Criar uma cópia do DataFrame original
                    df_display = registros[colunas].copy()

                    # Renomear colunas para exibição
                    df_display.columns = [rename[col] for col in colunas]

                    # Adicionar colunas de ação
                    df_display['Ações'] = ''

                    # Exibir tabela
                    st.dataframe(df_display, hide_index=True)

                    # Botões de ação abaixo da tabela
                    col1, col2 = st.columns(2)
                    with col1:
                        registro_id = st.number_input("ID do registro para ação:", min_value=1, 
                                                   max_value=len(registros), step=1)

                    with col2:
                        acao = st.selectbox("Ação:", ["Editar", "Excluir"])

                    # Formulário de ação
                    with st.form(f"acao_registro_parceiro"):
                        if st.form_submit_button(f"Confirmar {acao}"):
                            registro = registros[registros['id'] == registro_id].iloc[0]

                            if acao == "Excluir":
                                try:
                                    st.session_state.db.delete_parceiro(registro_id)
                                    st.success(f"Parceiro excluído com sucesso!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao excluir Parceiro: {str(e)}")

                            elif acao == "Editar":
                                st.session_state[f'editing_{registro_id}'] = True
                                st.rerun()

                    # Formulário de edição
                    if st.session_state.get(f'editing_{registro_id}', False):
                        with st.form(f"edit_form_{registro_id}"):
                            st.subheader("Editar Registro")
                            edited_data = {}
                            registro = registros[registros['id'] == registro_id].iloc[0]

                            # Campos comuns
                            edited_data['nome'] = st.text_input("Nome", value=registro['nome'])
                            edited_data['email'] = st.text_input("Email", value=registro.get('email', ''))
                            edited_data['telefone'] = st.text_input("Telefone", value=registro.get('telefone', ''))

                            # Campos específicos
                            edited_data['area_atuacao'] = st.text_input("Área de Atuação", value=registro.get('area_atuacao', ''))
                            edited_data['tipo_parceria'] = st.selectbox(
                                "Tipo de Parceria",
                                ["Indicação", "Colaboração", "Projeto Conjunto"],
                                index=["Indicação", "Colaboração", "Projeto Conjunto"].index(registro.get('tipo_parceria', 'Indicação'))
                            )

                            # Campos de endereço
                            edited_data['estado'] = st.text_input("Estado (UF)", value=registro.get('estado', ''))
                            edited_data['cidade'] = st.text_input("Cidade", value=registro.get('cidade', ''))
                            edited_data['bairro'] = st.text_input("Bairro", value=registro.get('bairro', ''))
                            edited_data['endereco'] = st.text_input("Endereço", value=registro.get('endereco', ''))

                            # Botões do formulário
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.form_submit_button("Salvar"):
                                    try:
                                        st.session_state.db.update_parceiro(registro_id, **edited_data)
                                        st.session_state[f'editing_{registro_id}'] = False
                                        st.success("Registro atualizado com sucesso!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro ao atualizar registro: {str(e)}")

                            with col2:
                                if st.form_submit_button("Cancelar"):
                                    st.session_state[f'editing_{registro_id}'] = False
                                    st.rerun()

                else:
                    st.info(f"Nenhum parceiro cadastrado.")

            except Exception as e:
                st.error(f"Erro ao carregar lista de parceiros: {str(e)}")

        with parceiro_tab2:
            st.subheader("Importar Parceiros")

            # Botão para baixar template
            template = gerar_template_csv("Parceiro")
            st.download_button(
                "📝 Baixar Template Parceiro",
                template,
                "template_parceiro.csv",
                "text/csv",
                help="Baixe este template, preencha com seus dados e faça upload para importar parceiros"
            )

            # Upload do arquivo
            arquivo = st.file_uploader("Selecione o arquivo CSV de Parceiros", type=['csv'])

            if arquivo:
                if st.button("Importar Parceiros"):
                    with st.spinner("Importando dados..."):
                        sucesso, mensagem = importar_cadastros(arquivo, "Parceiro", st.session_state.db)
                        if sucesso:
                            st.success(mensagem)
                        else:
                            st.error(mensagem)

    with tab_assistente:
        assistente_tab1, assistente_tab2 = st.tabs(["Cadastrar/Listar", "Importar"])

        with assistente_tab1:
            st.subheader("Cadastro de Assistentes")
            # Form de cadastro de assistente
            with st.form("cadastro_assistente", clear_on_submit=True):
                nome = st.text_input("Nome")
                col1, col2 = st.columns(2)
                with col1:
                    telefone = st.text_input("Telefone")
                    email = st.text_input("Email")
                with col2:
                    disponibilidade = st.multiselect(
                        "Disponibilidade",
                        ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"]
                    )
                    pix = st.text_input("Chave PIX")

                observacoes = st.text_area("Observações")
                submitted = st.form_submit_button("Cadastrar Assistente")

                if submitted:
                    try:
                        st.session_state.db.add_assistente(
                            nome=nome,
                            telefone=telefone,
                            email=email,
                            disponibilidade=",".join(disponibilidade) if disponibilidade else None,
                            pix=pix,
                            observacoes=observacoes
                        )
                        st.success("Assistente cadastrado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao cadastrar assistente: {str(e)}")

            # Lista de cadastros do tipo selecionado
            st.subheader(f"Lista de Assistentes")
            try:
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
                if not registros.empty:
                    # Criar uma cópia do DataFrame original
                    df_display = registros[colunas].copy()

                    # Renomear colunas para exibição
                    df_display.columns = [rename[col] for col in colunas]

                    # Adicionar colunas de ação
                    df_display['Ações'] = ''

                    # Exibir tabela
                    st.dataframe(df_display, hide_index=True)

                    # Botões de ação abaixo da tabela
                    col1, col2 = st.columns(2)
                    with col1:
                        registro_id = st.number_input("ID do registro para ação:", min_value=1, 
                                                   max_value=len(registros), step=1)

                    with col2:
                        acao = st.selectbox("Ação:", ["Editar", "Excluir"])

                    # Formulário de ação
                    with st.form(f"acao_registro_assistente"):
                        if st.form_submit_button(f"Confirmar {acao}"):
                            registro = registros[registros['id'] == registro_id].iloc[0]

                            if acao == "Excluir":
                                try:
                                    st.session_state.db.delete_assistente(registro_id)
                                    st.success(f"Assistente excluído com sucesso!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao excluir Assistente: {str(e)}")

                            elif acao == "Editar":
                                st.session_state[f'editing_{registro_id}'] = True
                                st.rerun()

                    # Formulário de edição
                    if st.session_state.get(f'editing_{registro_id}', False):
                        with st.form(f"edit_form_{registro_id}"):
                            st.subheader("Editar Registro")
                            edited_data = {}
                            registro = registros[registros['id'] == registro_id].iloc[0]

                            # Campos comuns
                            edited_data['nome'] = st.text_input("Nome", value=registro['nome'])
                            edited_data['email'] = st.text_input("Email", value=registro.get('email', ''))
                            edited_data['telefone'] = st.text_input("Telefone", value=registro.get('telefone', ''))

                            # Campos específicos
                            disponibilidade_atual = registro.get('disponibilidade', '').split(',') if registro.get('disponibilidade') else []
                            edited_data['disponibilidade'] = st.multiselect(
                                "Disponibilidade",
                                ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"],
                                default=disponibilidade_atual
                            )

                            # Campos de endereço
                            edited_data['estado'] = st.text_input("Estado (UF)", value=registro.get('estado', ''))
                            edited_data['cidade'] = st.text_input("Cidade", value=registro.get('cidade', ''))
                            edited_data['bairro'] = st.text_input("Bairro", value=registro.get('bairro', ''))
                            edited_data['endereco'] = st.text_input("Endereço", value=registro.get('endereco', ''))

                            # Botões do formulário
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.form_submit_button("Salvar"):
                                    try:
                                        if 'disponibilidade' in edited_data and edited_data['disponibilidade']:
                                            edited_data['disponibilidade'] = ','.join(edited_data['disponibilidade'])
                                        st.session_state.db.update_assistente(registro_id, **edited_data)
                                        st.session_state[f'editing_{registro_id}'] = False
                                        st.success("Registro atualizado com sucesso!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro ao atualizar registro: {str(e)}")

                            with col2:
                                if st.form_submit_button("Cancelar"):
                                    st.session_state[f'editing_{registro_id}'] = False
                                    st.rerun()

                else:
                    st.info(f"Nenhum assistente cadastrado.")

            except Exception as e:
                st.error(f"Erro ao carregar lista de assistentes: {str(e)}")

        with assistente_tab2:
            st.subheader("Importar Assistentes")

            # Botão para baixar template
            template = gerar_template_csv("Assistente")
            st.download_button(
                "📝 Baixar Template Assistente",
                template,
                "template_assistente.csv",
                "text/csv",
                help="Baixe este template, preencha com seus dados e faça upload para importar assistentes"
            )

            # Upload do arquivo
            arquivo = st.file_uploader("Selecione o arquivo CSV de Assistentes", type=['csv'])

            if arquivo:
                if st.button("Importar Assistentes"):
                    with st.spinner("Importando dados..."):
                        sucesso, mensagem = importar_cadastros(arquivo, "Assistente", st.session_state.db)
                        if sucesso:
                            st.success(mensagem)
                        else:
                            st.error(mensagem)