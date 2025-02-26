import streamlit as st
from datetime import datetime
import pandas as pd
from utils.importador import importar_cadastros, gerar_template_csv

def show():
    # Verificar se o db está na sessão
    if 'db' not in st.session_state:
        st.error("Erro: Conexão com banco de dados não inicializada")
        return

    st.title("📋 Cadastros")

    # Tabs para diferentes tipos de cadastro
    tab_cliente, tab_fornecedor, tab_parceiro, tab_assistente, tab3 = st.tabs([
        "👥 Clientes",
        "🏢 Fornecedores",
        "🤝 Parceiros",
        "👨‍💼 Assistentes",
        "Importar Clientes"
    ])

    with tab_cliente:
        st.subheader("Lista de Clientes")
        try:
            @st.cache_data(ttl=60)
            def load_clientes():
                return st.session_state.db.get_clientes()

            if 'update_clientes' in st.session_state and st.session_state['update_clientes']:
                st.session_state['clientes'] = load_clientes()
                st.session_state['update_clientes'] = False
            elif 'clientes' not in st.session_state:
                st.session_state['clientes'] = load_clientes()

            registros = st.session_state['clientes']

            if not registros.empty:
                # Definir colunas para exibição
                colunas = ['id', 'nome', 'telefone', 'email', 'cpf', 'estado', 'cidade', 'bairro', 
                          'endereco', 'data_aniversario', 'origem_cliente', 'observacoes']
                rename = {
                    'id': 'ID',
                    'nome': 'Nome',
                    'telefone': 'Telefone',
                    'email': 'Email',
                    'cpf': 'CPF',
                    'estado': 'Estado',
                    'cidade': 'Cidade',
                    'bairro': 'Bairro',
                    'endereco': 'Endereço',
                    'data_aniversario': 'Data Aniversário',
                    'origem_cliente': 'Origem',
                    'observacoes': 'Observações'
                }

                # Criar DataFrame para exibição
                df_display = registros[colunas].copy()
                df_display.columns = [rename[col] for col in colunas]

                # Exibir tabela editável
                edited_df = st.data_editor(
                    df_display,
                    num_rows="dynamic",
                    use_container_width=True,
                    hide_index=True
                )

                # Botões de ação
                col1, col2 = st.columns(2)
                with col1:
                    cliente_id = st.number_input(
                        "ID do cliente para ação:",
                        min_value=1,
                        max_value=len(registros) if not registros.empty else 1,
                        step=1
                    )

                with col2:
                    acao = st.selectbox(
                        "Ação:",
                        ["Excluir"]
                    )

                # Botão de confirmação
                if st.button(f"Confirmar {acao}"):
                    if acao == "Excluir":
                        try:
                            st.session_state.db.delete_cliente(cliente_id)
                            st.success(f"Cliente excluído com sucesso!")
                            st.session_state['update_clientes'] = True
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao excluir cliente: {str(e)}")

                # Verificar mudanças na edição
                if edited_df is not None and not edited_df.equals(df_display):
                    for index, row in edited_df.iterrows():
                        original_row = df_display.iloc[index]
                        if not row.equals(original_row):
                            try:
                                cliente_id = int(row['ID'])
                                update_data = {
                                    'nome': row['Nome'],
                                    'telefone': row['Telefone'],
                                    'email': row['Email'],
                                    'cpf': row['CPF'],
                                    'estado': row['Estado'],
                                    'cidade': row['Cidade'],
                                    'bairro': row['Bairro'],
                                    'endereco': row['Endereço'],
                                    'data_aniversario': row['Data Aniversário'],
                                    'origem_cliente': row['Origem'],
                                    'observacoes': row['Observações']
                                }
                                st.session_state.db.update_cliente(cliente_id, **update_data)
                                st.success(f"Cliente {cliente_id} atualizado com sucesso!")
                                st.session_state['update_clientes'] = True
                            except Exception as e:
                                st.error(f"Erro ao atualizar cliente {cliente_id}: {str(e)}")
            else:
                st.info("Nenhum cliente cadastrado.")

        except Exception as e:
            st.error(f"Erro ao carregar clientes: {str(e)}")

    with tab_fornecedor:
        fornecedor_tab1, fornecedor_tab2 = st.tabs(["Cadastrar/Listar", "Importar"])

        with fornecedor_tab1:
            st.subheader("Cadastro de Fornecedores")

            # Form de cadastro de fornecedor
            with st.form("cadastro_fornecedor", clear_on_submit=True):
                nome = st.text_input("Razão Social")
                col1, col2 = st.columns(2)
                with col1:
                    telefone = st.text_input("Telefone")
                    categoria = st.selectbox(
                        "Categoria",
                        ["Produtos", "Serviços", "Marcenaria", "Outro"]
                    )
                with col2:
                    pix = st.text_input("Chave PIX")

                endereco = st.text_input("Endereço")
                observacoes = st.text_area("Observações")
                submitted = st.form_submit_button("Cadastrar")

                if submitted:
                    try:
                        st.session_state.db.add_fornecedor(
                            descricao=nome,
                            contato=telefone,
                            categoria=categoria,
                            endereco=endereco,
                            pix=pix,
                            observacoes=observacoes
                        )
                        st.success("Fornecedor cadastrado com sucesso!")
                        st.session_state['update_fornecedores'] = True
                    except Exception as e:
                        st.error(f"Erro ao cadastrar fornecedor: {str(e)}")

            # Lista de fornecedores
            st.subheader("Lista de Fornecedores")
            try:
                @st.cache_data(ttl=60)
                def load_fornecedores():
                    return st.session_state.db.get_fornecedores()

                if 'update_fornecedores' in st.session_state and st.session_state['update_fornecedores']:
                    st.session_state['fornecedores'] = load_fornecedores()
                    st.session_state['update_fornecedores'] = False
                elif 'fornecedores' not in st.session_state:
                    st.session_state['fornecedores'] = load_fornecedores()

                registros = st.session_state['fornecedores']

                if not registros.empty:
                    # Exibir os fornecedores em cards
                    for idx, fornecedor in registros.iterrows():
                        with st.expander(f"{fornecedor['descricao']} - {fornecedor['categoria']}"):
                            col1, col2 = st.columns([3, 1])

                            with col1:
                                st.write(f"**Contato:** {fornecedor['contato']}")
                                st.write(f"**Email:** {fornecedor['email']}")
                                st.write(f"**PIX:** {fornecedor['pix']}")
                                st.write(f"**Recorrente:** {'Sim' if fornecedor['recorrente'] else 'Não'}")
                                if fornecedor['observacoes']:
                                    st.write(f"**Observações:** {fornecedor['observacoes']}")

                            with col2:
                                if st.button("🗑️ Excluir", key=f"del_forn_{fornecedor['id']}"):
                                    try:
                                        st.session_state.db.delete_fornecedor(fornecedor['id'])
                                        st.success("Fornecedor excluído com sucesso!")
                                        st.session_state['update_fornecedores'] = True
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro ao excluir fornecedor: {str(e)}")

                                if st.button("✏️ Editar", key=f"edit_forn_{fornecedor['id']}"):
                                    st.session_state['editing_fornecedor_id'] = fornecedor['id']
                                    st.rerun()

                    # Formulário de edição
                    if 'editing_fornecedor_id' in st.session_state:
                        st.write("---")
                        st.subheader("Editar Fornecedor")
                        with st.form("edit_fornecedor_form"):
                            fornecedor = registros[registros['id'] == st.session_state['editing_fornecedor_id']].iloc[0]

                            nome = st.text_input("Nome/Razão Social", value=fornecedor['descricao'])
                            contato = st.text_input("Telefone", value=fornecedor['contato'])
                            email = st.text_input("Email", value=fornecedor['email'])
                            categoria = st.selectbox(
                                "Categoria",
                                ["Produtos", "Serviços", "Marcenaria", "Outro"],
                                index=["Produtos", "Serviços", "Marcenaria", "Outro"].index(fornecedor['categoria'])
                            )
                            pix = st.text_input("PIX", value=fornecedor['pix'])
                            recorrente = st.checkbox("Recorrente", value=fornecedor['recorrente'])
                            observacoes = st.text_area("Observações", value=fornecedor['observacoes'])

                            col1, col2 = st.columns(2)
                            with col1:
                                if st.form_submit_button("Salvar"):
                                    try:
                                        st.session_state.db.update_fornecedor(
                                            st.session_state['editing_fornecedor_id'],
                                            descricao=nome,
                                            contato=contato,
                                            email=email,
                                            categoria=categoria,
                                            pix=pix,
                                            recorrente=recorrente,
                                            observacoes=observacoes
                                        )
                                        del st.session_state['editing_fornecedor_id']
                                        st.session_state['update_fornecedores'] = True
                                        st.success("Fornecedor atualizado com sucesso!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro ao atualizar fornecedor: {str(e)}")
                            with col2:
                                if st.form_submit_button("Cancelar"):
                                    del st.session_state['editing_fornecedor_id']
                                    st.rerun()
                else:
                    st.info("Nenhum fornecedor cadastrado.")

            except Exception as e:
                st.error(f"Erro ao carregar lista de fornecedores: {str(e)}")

        with fornecedor_tab2:
            st.subheader("Importar Fornecedores")

            # Download do template
            template = gerar_template_csv("Fornecedor")
            st.download_button(
                "📝 Baixar Template",
                template,
                "template_fornecedor.csv",
                "text/csv",
                help="Baixe este template, preencha com seus dados e faça upload para importar"
            )

            # Upload e importação
            arquivo = st.file_uploader(
                "Selecione o arquivo CSV",
                type=['csv'],
                key="fornecedor_file_uploader"
            )
            if arquivo:
                if st.button("Importar Fornecedores"):
                    with st.spinner("Importando dados..."):
                        sucesso, mensagem = importar_cadastros(arquivo, "Fornecedor", st.session_state.db)
                        if sucesso:
                            st.success(mensagem)
                            st.session_state['update_fornecedores'] = True
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
                    area_atuacao = st.text_input("Área de Atuação")
                with col2:
                    tipo_parceria = st.selectbox(
                        "Tipo de Parceria",
                        ["Indicação", "Colaboração", "Projeto Conjunto"]
                    )

                observacoes = st.text_area("Observações")
                submitted = st.form_submit_button("Cadastrar")

                if submitted:
                    try:
                        st.session_state.db.add_parceiro(
                            nome=nome,
                            telefone=telefone,
                            area_atuacao=area_atuacao,
                            tipo_parceria=tipo_parceria,
                            observacoes=observacoes
                        )
                        st.success("Parceiro cadastrado com sucesso!")
                        st.session_state['update_parceiros'] = True
                    except Exception as e:
                        st.error(f"Erro ao cadastrar parceiro: {str(e)}")

            # Lista de cadastros
            st.subheader(f"Lista de Parceiros")
            try:
                @st.cache_data(ttl=60)
                def load_parceiros():
                    return st.session_state.db.get_parceiros()

                if 'update_parceiros' in st.session_state and st.session_state['update_parceiros']:
                    st.session_state['parceiros'] = load_parceiros()
                    st.session_state['update_parceiros'] = False
                elif 'parceiros' not in st.session_state:
                    st.session_state['parceiros'] = load_parceiros()


                registros = st.session_state['parceiros']
                if not registros.empty:
                    # Definir colunas para exibição
                    colunas = ['nome', 'telefone', 'area_atuacao', 'tipo_parceria']
                    rename = {
                        'nome': 'Nome',
                        'telefone': 'Telefone',
                        'area_atuacao': 'Área de Atuação',
                        'tipo_parceria': 'Tipo de Parceria'
                    }

                    # Criar DataFrame para exibição
                    df_display = registros[colunas].copy()
                    df_display.columns = [rename[col] for col in colunas]

                    # Exibir tabela
                    st.dataframe(df_display, hide_index=True)

                    # Botões de ação
                    col1, col2 = st.columns(2)
                    with col1:
                        registro_id = st.number_input(
                            "ID do registro para ação:",
                            min_value=1,
                            max_value=len(registros),
                            step=1
                        )

                    with col2:
                        acao = st.selectbox(
                            "Ação:",
                            ["Editar", "Excluir"]
                        )

                    # Formulário de ação
                    with st.form(f"acao_registro_parceiro"):
                        if st.form_submit_button(f"Confirmar {acao}"):
                            if acao == "Excluir":
                                try:
                                    st.session_state.db.delete_parceiro(registro_id)
                                    st.success(f"Parceiro excluído com sucesso!")
                                    st.session_state['update_parceiros'] = True
                                except Exception as e:
                                    st.error(f"Erro ao excluir Parceiro: {str(e)}")
                            elif acao == "Editar":
                                st.session_state['editing_parceiro_id'] = registro_id

                    # Formulário de edição
                    if 'editing_parceiro_id' in st.session_state:
                        with st.form(f"edit_form_{registro_id}"):
                            registro = registros[registros['id'] == st.session_state['editing_parceiro_id']].iloc[0]
                            edited_data = {}
                            edited_data['nome'] = st.text_input("Nome", value=registro['nome'])
                            edited_data['email'] = st.text_input("Email", value=registro.get('email', ''))
                            edited_data['telefone'] = st.text_input("Telefone", value=registro.get('telefone', ''))
                            edited_data['area_atuacao'] = st.text_input("Área de Atuação", value=registro.get('area_atuacao', ''))
                            edited_data['tipo_parceria'] = st.selectbox(
                                "Tipo de Parceria",
                                ["Indicação", "Colaboração", "Projeto Conjunto"],
                                index=["Indicação", "Colaboração", "Projeto Conjunto"].index(registro.get('tipo_parceria', 'Indicação'))
                            )

                            col1, col2 = st.columns(2)
                            with col1:
                                if st.form_submit_button("Salvar"):
                                    try:
                                        st.session_state.db.update_parceiro(st.session_state['editing_parceiro_id'], **edited_data)
                                        del st.session_state['editing_parceiro_id']
                                        st.session_state['update_parceiros'] = True
                                        st.success("Registro atualizado com sucesso!")
                                    except Exception as e:
                                        st.error(f"Erro ao atualizar registro: {str(e)}")

                            with col2:
                                if st.form_submit_button("Cancelar"):
                                    del st.session_state['editing_parceiro_id']
                else:
                    st.info("Nenhum parceiro cadastrado.")

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
            arquivo = st.file_uploader(
                "Selecione o arquivo CSV de Parceiros",
                type=['csv'],
                key="parceiro_file_uploader"
            )

            if arquivo:
                if st.button("Importar Parceiros"):
                    with st.spinner("Importando dados..."):
                        sucesso, mensagem = importar_cadastros(arquivo, "Parceiro", st.session_state.db)
                        if sucesso:
                            st.success(mensagem)
                            st.session_state['update_parceiros'] = True
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
                    endereco = st.text_input("Endereço")
                with col2:
                    pix = st.text_input("Chave PIX")

                observacoes = st.text_area("Observações")
                submitted = st.form_submit_button("Cadastrar")

                if submitted:
                    try:
                        st.session_state.db.add_assistente(
                            nome=nome,
                            telefone=telefone,
                            endereco=endereco,
                            pix=pix,
                            observacoes=observacoes
                        )
                        st.success("Assistente cadastrado com sucesso!")
                        st.session_state['update_assistentes'] = True
                    except Exception as e:
                        st.error(f"Erro ao cadastrar assistente: {str(e)}")

            # Lista de cadastros do tipo selecionado
            st.subheader(f"Lista de Assistentes")
            try:
                @st.cache_data(ttl=60)
                def load_assistentes():
                    return st.session_state.db.get_assistentes()

                if 'update_assistentes' in st.session_state and st.session_state['update_assistentes']:
                    st.session_state['assistentes'] = load_assistentes()
                    st.session_state['update_assistentes'] = False
                elif 'assistentes' not in st.session_state:
                    st.session_state['assistentes'] = load_assistentes()

                registros = st.session_state['assistentes']
                colunas = ['nome', 'telefone', 'email', 'disponibilidade']
                rename = {
                    'nome': 'Nome',
                    'telefone': 'Telefone',
                    'email': 'Email',
                    'disponibilidade': 'Disponibilidade'
                }
                if not registros.empty:
                    # Criar uma cópia do DataFrame original
                    df_display = registros[colunas].copy()

                    # Renomear colunas para exibição
                    df_display.columns = [rename[col] for col in colunas]

                    # Exibir tabela
                    st.dataframe(df_display, hide_index=True)

                    # Botões de ação abaixo da tabela
                    col1, col2 = st.columns(2)
                    with col1:
                        registro_id = st.number_input(
                            "ID do registro para ação:",
                            min_value=1,
                            max_value=len(registros),
                            step=1
                        )

                    with col2:
                        acao = st.selectbox(
                            "Ação:",
                            ["Editar", "Excluir"]
                        )

                    # Formulário de ação
                    with st.form(f"acao_registro_assistente"):
                        if st.form_submit_button(f"Confirmar {acao}"):
                            if acao == "Excluir":
                                try:
                                    st.session_state.db.delete_assistente(registro_id)
                                    st.success(f"Assistente excluído com sucesso!")
                                    st.session_state['update_assistentes'] = True
                                except Exception as e:
                                    st.error(f"Erro ao excluir Assistente: {str(e)}")
                            elif acao == "Editar":
                                st.session_state['editing_assistente_id'] = registro_id

                    # Formulário de edição
                    if 'editing_assistente_id' in st.session_state:
                        with st.form(f"edit_form_{registro_id}"):
                            registro = registros[registros['id'] == st.session_state['editing_assistente_id']].iloc[0]
                            edited_data = {}
                            edited_data['nome'] = st.text_input("Nome", value=registro['nome'])
                            edited_data['email'] = st.text_input("Email", value=registro.get('email', ''))
                            edited_data['telefone'] = st.text_input("Telefone", value=registro.get('telefone', ''))
                            disponibilidade_atual = registro.get('disponibilidade', '').split(',') if registro.get('disponibilidade') else []
                            edited_data['disponibilidade'] = st.multiselect(
                                "Disponibilidade",
                                ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"],
                                default=disponibilidade_atual
                            )

                            col1, col2 = st.columns(2)
                            with col1:
                                if st.form_submit_button("Salvar"):
                                    try:
                                        if 'disponibilidade' in edited_data and edited_data['disponibilidade']:
                                            edited_data['disponibilidade'] = ','.join(edited_data['disponibilidade'])
                                        st.session_state.db.update_assistente(st.session_state['editing_assistente_id'], **edited_data)
                                        del st.session_state['editing_assistente_id']
                                        st.session_state['update_assistentes'] = True
                                        st.success("Registro atualizado com sucesso!")
                                    except Exception as e:
                                        st.error(f"Erro ao atualizar registro: {str(e)}")

                            with col2:
                                if st.form_submit_button("Cancelar"):
                                    del st.session_state['editing_assistente_id']
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
            arquivo = st.file_uploader(
                "Selecione o arquivo CSV de Assistentes",
                type=['csv'],
                key="assistente_file_uploader"
            )

            if arquivo:
                if st.button("Importar Assistentes", key="assistente_import_button"):
                    with st.spinner("Importando dados..."):
                        sucesso, mensagem = importar_cadastros(arquivo, "Assistente", st.session_state.db)
                        if sucesso:
                            st.success(mensagem)
                            st.session_state['update_assistentes'] = True
                        else:
                            st.error(mensagem)

    with tab3:
        st.subheader("Importar Clientes")
        st.write("""
        Para importar clientes, seu arquivo deve ter o seguinte formato:
        - Arquivo CSV com separador ponto e vírgula (;)
        - Colunas disponíveis:
            - nome (obrigatório)
            - telefone
            - email
            - cpf
            - estado
            - cidade
            - bairro
            - endereco
            - data_aniversario (formato: DD/MM/YYYY)
            - origem_cliente
        """)

        # Download do template
        template = gerar_template_csv("Cliente")
        st.download_button(
            "📝 Baixar Template",
            template,
            "template_cliente.csv",
            "text/csv",
            help="Baixe este template, preencha com seus dados e faça upload para importar"
        )

        # Upload e importação
        arquivo = st.file_uploader(
            "Selecione o arquivo CSV",
            type=['csv'],
            key="cliente_file_uploader"
        )
        if arquivo:
            try:
                # Ler primeiras linhas para preview
                df_preview = pd.read_csv(arquivo, sep=';', nrows=5)
                st.write("Preview dos dados:")
                st.dataframe(df_preview)

                if st.button("Importar Clientes", key="cliente_import_button"):
                    arquivo.seek(0)  # Voltar ao início do arquivo
                    with st.spinner("Importando dados..."):
                        sucesso, mensagem = importar_cadastros(arquivo, "Cliente", st.session_state.db)
                        if sucesso:
                            st.success(mensagem)
                        else:
                            st.error(mensagem)
            except Exception as e:
                st.error(f"Erro ao processar arquivo: {str(e)}")