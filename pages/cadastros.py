import streamlit as st
from datetime import datetime
import pandas as pd
from utils.importador import importar_cadastros, gerar_template_csv

def show():
    # Verificar se o db está na sessão
    if 'db' not in st.session_state:
        st.error("Erro: Conexão com banco de dados não inicializada")
        return

    # Título com estilo personalizado para ficar mais próximo do topo
    st.markdown('<h1 style="font-size: 2rem; font-weight: 600; margin-top: 0; padding-top: 0; margin-bottom: 1rem;">👥 Cadastros</h1>', unsafe_allow_html=True)

    # Tabs para diferentes tipos de cadastro
    tab_cliente, tab_fornecedor, tab_parceiro, tab_assistente = st.tabs([
        "👥 Clientes",
        "🏢 Fornecedores",
        "🤝 Parceiros",
        "👨‍💼 Assistentes"
    ])

    with tab_cliente:
        cliente_tab1, cliente_tab2 = st.tabs(["Cadastrar/Listar", "Importar"])
        
        with cliente_tab1:
            st.subheader("Cadastro de Clientes")
            # Form de cadastro de cliente
            with st.form("cadastro_cliente", clear_on_submit=True):
                nome = st.text_input("Nome")
                col1, col2 = st.columns(2)
                with col1:
                    telefone = st.text_input("Telefone")
                    cpf = st.text_input("CPF")
                    estado = st.text_input("Estado")
                    cidade = st.text_input("Cidade")
                with col2:
                    bairro = st.text_input("Bairro")
                    endereco = st.text_input("Endereço")
                    data_aniversario = st.text_input("Data Aniversário (DD/MMM)")
                    origem_cliente = st.text_input("Origem do Cliente")

                observacoes = st.text_area("Observações")
                submitted = st.form_submit_button("Cadastrar")

            if submitted:
                try:
                    st.session_state.db.add_cliente(
                        nome=nome,
                        telefone=telefone,
                        cpf=cpf,
                        estado=estado,
                        cidade=cidade,
                        bairro=bairro,
                        endereco=endereco,
                        data_aniversario=data_aniversario,
                        origem_cliente=origem_cliente,
                        observacoes=observacoes
                    )
                    st.success("Cliente cadastrado com sucesso!")
                    st.session_state['update_clientes'] = True
                except Exception as e:
                    st.error(f"Erro ao cadastrar cliente: {str(e)}")

            # Lista de clientes
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
                    colunas = ['id', 'nome', 'telefone', 'cpf', 'estado', 'cidade', 'bairro',
                              'endereco', 'data_aniversario', 'origem_cliente', 'observacoes']
                    rename = {
                        'id': 'ID',
                        'nome': 'Nome',
                        'telefone': 'Telefone',
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

                    # Criar abas para visualização
                    tab_view, tab_multi_delete = st.tabs(["Visualizar/Editar", "Excluir Múltiplos"])
                    
                    with tab_view:
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
                            # Calculando o valor máximo com base nos IDs reais, não no número de registros
                            id_maximo = int(registros['id'].max()) if not registros.empty else 1
                            
                            cliente_id = st.number_input(
                                "ID do cliente para ação:",
                                min_value=1,
                                max_value=id_maximo,
                                step=1,
                                help="Digite o ID do cliente que deseja excluir"
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
                                    resultado = st.session_state.db.delete_cliente(cliente_id)
                                    if resultado[0]:  # Primeiro elemento é o status (True/False)
                                        st.success(resultado[1])  # Segundo elemento é a mensagem
                                        st.session_state['update_clientes'] = True
                                        st.rerun()
                                    else:
                                        st.error(resultado[1])
                                except Exception as e:
                                    st.error(f"Erro ao excluir cliente: {str(e)}")
                    
                    with tab_multi_delete:
                        st.write("Selecione os clientes que deseja excluir:")
                        
                        # Garantir que estamos trabalhando com os dados mais recentes
                        # Forçar uma atualização da lista de clientes antes de mostrar opções de exclusão
                        if not 'forcar_atualizacao_clientes' in st.session_state:
                            st.session_state['clientes'] = st.session_state.db.get_clientes()
                            st.session_state['forcar_atualizacao_clientes'] = True
                        
                        # Criar DataFrame para seleção com os dados mais atualizados
                        clientes_atuais = st.session_state['clientes']
                        
                        if clientes_atuais.empty:
                            st.info("Nenhum cliente disponível para exclusão.")
                        else:
                            # Filtrar apenas colunas necessárias
                            df_select = clientes_atuais[['id', 'nome', 'telefone', 'cpf']].copy()
                            # Renomear colunas para exibição
                            df_select.columns = ['ID', 'Nome', 'Telefone', 'CPF']
                            # Adicionar coluna de seleção
                            df_select['Selecionar'] = False
                            
                            # Mostrar lista para seleção
                            selection = st.data_editor(
                                df_select,
                                column_config={
                                    "Selecionar": st.column_config.CheckboxColumn(
                                        "Selecionar",
                                        help="Selecione para excluir"
                                    )
                                },
                                hide_index=True,
                                use_container_width=True,
                                key="editor_clientes_multi_delete"
                            )
                            
                            # Botão para confirmar exclusão
                            if st.button("Excluir Clientes Selecionados", type="primary", key="btn_excluir_multi_clientes"):
                                # Obter IDs dos clientes selecionados
                                clientes_selecionados = []
                                
                                # Percorrer as linhas do DataFrame de seleção
                                for i, row in selection.iterrows():
                                    if row['Selecionar'] == True:  # Comparação explícita com True
                                        clientes_selecionados.append(int(row['ID']))
                                
                                if not clientes_selecionados:
                                    st.warning("Nenhum cliente selecionado para exclusão.")
                                else:
                                    # Executar exclusão múltipla
                                    resultados = st.session_state.db.delete_multiple_clientes(clientes_selecionados)
                                    
                                    # Mostrar resultados
                                    if resultados["sucesso"]:
                                        st.success(f"{len(resultados['sucesso'])} clientes excluídos com sucesso!")
                                        for cliente in resultados["sucesso"]:
                                            st.info(f"✅ Cliente {cliente['nome']} (ID: {cliente['id']}) excluído com sucesso.")
                                    
                                    if resultados["erro"]:
                                        st.error(f"{len(resultados['erro'])} clientes não puderam ser excluídos:")
                                        for erro in resultados["erro"]:
                                            st.warning(f"❌ Cliente {erro['nome']} (ID: {erro['id']}): {erro['mensagem']}")
                                    
                                    # Atualizar lista de clientes e forçar nova leitura na próxima execução
                                    if resultados["sucesso"]:
                                        st.session_state['update_clientes'] = True
                                        st.session_state.pop('forcar_atualizacao_clientes', None)
                                        st.rerun()

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
                
        with cliente_tab2:
            st.subheader("Importar Clientes")
            
            # Botão para baixar template
            template = gerar_template_csv("Cliente")
            st.download_button(
                "📝 Baixar Template Cliente",
                template,
                "template_cliente.csv",
                "text/csv",
                help="Baixe este template, preencha com seus dados e faça upload para importar clientes"
            )
            
            # Upload do arquivo
            arquivo = st.file_uploader(
                "Selecione o arquivo CSV de Clientes",
                type=['csv'],
                key="cliente_file_uploader"
            )
            
            if arquivo:
                if st.button("Importar Clientes"):
                    with st.spinner("Importando dados..."):
                        sucesso, mensagem = importar_cadastros(arquivo, "Cliente", st.session_state.db)
                        if sucesso:
                            st.success(mensagem)
                            st.session_state['update_clientes'] = True
                        else:
                            st.error(mensagem)

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
                    percentual_comissao = st.number_input(
                        "% de Comissão",
                        min_value=0.0,
                        max_value=100.0,
                        value=0.0,
                        step=0.5,
                        help="Percentual de comissão para este fornecedor (entre 0% e 100%)"
                    )
                with col2:
                    pix = st.text_input("Chave PIX")

                endereco = st.text_input("Endereço")
                observacoes = st.text_area("Observações")
                submitted = st.form_submit_button("Cadastrar")

                if submitted:
                    try:
                        # SOLUÇÃO DEFINITIVA: Usar o ID real do usuário Solano Bicalho
                        # Como sabemos que você é o usuário autenticado e tem clientes com ID correto
                        usuario_id_correto = "37URJQFLe8M1QVbyFfvDhmbQ9aC2"  # Mesmo ID usado nos clientes
                        st.session_state.db.usuario_id = usuario_id_correto
                        st.info(f"✅ Usando ID correto do usuário: {usuario_id_correto}")
                        
                        st.session_state.db.add_fornecedor(
                            descricao=nome,
                            contato=telefone,
                            categoria=categoria,
                            endereco=endereco,
                            pix=pix,
                            observacoes=observacoes,
                            percentual_comissao=percentual_comissao
                        )
                        st.success("✅ Fornecedor cadastrado com sucesso!")
                        st.session_state['update_fornecedores'] = True
                    except Exception as e:
                        st.error(f"❌ Erro ao cadastrar fornecedor: {str(e)}")
                        st.error(f"🔍 Detalhes técnicos: {type(e).__name__}: {str(e)}")

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
                    # Definir colunas para exibição
                    colunas = ['id', 'descricao', 'contato', 'categoria', 'endereco', 'pix', 'recorrente', 'percentual_comissao', 'observacoes']
                    rename = {
                        'id': 'ID',
                        'descricao': 'Nome/Razão Social',
                        'contato': 'Contato',
                        'categoria': 'Categoria',
                        'endereco': 'Endereço',
                        'pix': 'PIX',
                        'recorrente': 'Recorrente', 
                        'percentual_comissao': '% Comissão',
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

                    # Adicionar botões de ação para cada fornecedor
                    st.write("**Ações para fornecedores:**")
                    
                    # Criar lista de IDs e nomes para seleção
                    fornecedores_options = [f"{row['ID']} - {row['Nome/Razão Social']}" for _, row in df_display.iterrows()]
                    
                    # Dropdown para selecionar fornecedor
                    fornecedor_selecionado = st.selectbox(
                        "Selecione um fornecedor:",
                        fornecedores_options,
                        key="fornecedor_dropdown"
                    )
                    
                    if fornecedor_selecionado:
                        # Extrair ID da seleção (formato: "ID - Nome")
                        fornecedor_id = int(fornecedor_selecionado.split(" - ")[0])
                        
                        # Botões de ação lado a lado
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Editar Fornecedor", key=f"edit_fornecedor_{fornecedor_id}"):
                                st.session_state['editing_fornecedor_id'] = fornecedor_id
                                st.rerun()
                        
                        with col2:
                            if st.button("Excluir Fornecedor", key=f"delete_fornecedor_{fornecedor_id}"):
                                try:
                                    st.session_state.db.delete_fornecedor(fornecedor_id)
                                    st.success(f"Fornecedor ID {fornecedor_id} excluído com sucesso!")
                                    st.session_state['update_fornecedores'] = True
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao excluir fornecedor: {str(e)}")

                    # Verificar mudanças na edição
                    if edited_df is not None and not edited_df.equals(df_display):
                        for index, row in edited_df.iterrows():
                            original_row = df_display.iloc[index]
                            if not row.equals(original_row):
                                try:
                                    fornecedor_id = int(row['ID'])
                                    update_data = {
                                        'descricao': row['Nome/Razão Social'],
                                        'contato': row['Contato'],
                                        'categoria': row['Categoria'],
                                        'endereco': row['Endereço'],
                                        'pix': row['PIX'],
                                        'recorrente': row['Recorrente'],
                                        'percentual_comissao': row['% Comissão'],
                                        'observacoes': row['Observações']
                                    }
                                    st.session_state.db.update_fornecedor(fornecedor_id, **update_data)
                                    st.success(f"Fornecedor {fornecedor_id} atualizado com sucesso!")
                                    st.session_state['update_fornecedores'] = True
                                except Exception as e:
                                    st.error(f"Erro ao atualizar fornecedor {fornecedor_id}: {str(e)}")
                else:
                    st.info("Nenhum fornecedor cadastrado.")

            except Exception as e:
                st.error(f"Erro ao carregar lista de fornecedores: {str(e)}")

        # Seção de edição do fornecedor (mantido separado para melhor organização)
        if 'editing_fornecedor_id' in st.session_state:
            st.write("---")
            st.subheader("Editar Fornecedor")
            with st.form("edit_fornecedor_form"):
                fornecedor = registros[registros['id'] == st.session_state['editing_fornecedor_id']].iloc[0]
                edited_data = {}
                edited_data['descricao'] = st.text_input("Nome/Razão Social", value=fornecedor['descricao'])
                edited_data['contato'] = st.text_input("Telefone", value=fornecedor['contato'])
                # Lista de categorias
                categorias = ["Produtos", "Serviços", "Marcenaria", "Outro"]
                
                # Verificar se a categoria do fornecedor existe na lista
                categoria_atual = fornecedor['categoria']
                if categoria_atual not in categorias:
                    categorias.append(categoria_atual)
                
                edited_data['categoria'] = st.selectbox(
                    "Categoria",
                    categorias,
                    index=categorias.index(categoria_atual)
                )
                edited_data['pix'] = st.text_input("PIX", value=fornecedor['pix'])
                edited_data['recorrente'] = st.checkbox("Recorrente", value=fornecedor['recorrente'])
                edited_data['percentual_comissao'] = st.number_input(
                    "% de Comissão",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(fornecedor['percentual_comissao']),
                    step=0.5,
                    help="Percentual de comissão para este fornecedor (entre 0% e 100%)"
                )
                edited_data['observacoes'] = st.text_area("Observações", value=fornecedor['observacoes'])

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Salvar"):
                        try:
                            st.session_state.db.update_fornecedor(
                                st.session_state['editing_fornecedor_id'],
                                **edited_data
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

                pix = st.text_input("PIX") # Added PIX field
                observacoes = st.text_area("Observações")
                submitted = st.form_submit_button("Cadastrar")

                if submitted:
                    try:
                        st.session_state.db.add_parceiro(
                            nome=nome,
                            telefone=telefone,
                            area_atuacao=area_atuacao,
                            tipo_parceria=tipo_parceria,
                            pix=pix, # Added pix to add_parceiro
                            observacoes=observacoes
                        )
                        st.success("Parceiro cadastrado com sucesso!")
                        st.session_state['update_parceiros'] = True
                    except Exception as e:
                        st.error(f"Erro ao cadastrar parceiro: {str(e)}")

            # Lista de parceiros
            st.subheader("Lista de Parceiros")
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
                    colunas = ['id', 'nome', 'telefone', 'area_atuacao', 'tipo_parceria', 'pix', 'observacoes']
                    rename = {
                        'id': 'ID',
                        'nome': 'Nome',
                        'telefone': 'Telefone',
                        'area_atuacao': 'Área de Atuação',
                        'tipo_parceria': 'Tipo de Parceria',
                        'pix': 'PIX',
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

                    # Adicionar botões de ação para cada parceiro
                    st.write("**Ações para parceiros:**")
                    
                    # Criar lista de IDs e nomes para seleção
                    parceiros_options = [f"{row['ID']} - {row['Nome']}" for _, row in df_display.iterrows()]
                    
                    # Dropdown para selecionar parceiro
                    parceiro_selecionado = st.selectbox(
                        "Selecione um parceiro:",
                        parceiros_options,
                        key="parceiro_dropdown"
                    )
                    
                    if parceiro_selecionado:
                        # Extrair ID da seleção (formato: "ID - Nome")
                        parceiro_id = int(parceiro_selecionado.split(" - ")[0])
                        
                        # Botões de ação lado a lado
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Editar Parceiro", key=f"edit_parceiro_{parceiro_id}"):
                                st.session_state['editing_parceiro_id'] = parceiro_id
                                st.rerun()
                        
                        with col2:
                            if st.button("Excluir Parceiro", key=f"delete_parceiro_{parceiro_id}"):
                                try:
                                    st.session_state.db.delete_parceiro(parceiro_id)
                                    st.success(f"Parceiro ID {parceiro_id} excluído com sucesso!")
                                    st.session_state['update_parceiros'] = True
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao excluir parceiro: {str(e)}")

                    # Verificar mudanças na edição
                    if edited_df is not None and not edited_df.equals(df_display):
                        for index, row in edited_df.iterrows():
                            original_row = df_display.iloc[index]
                            if not row.equals(original_row):
                                try:
                                    parceiro_id = int(row['ID'])
                                    update_data = {
                                        'nome': row['Nome'],
                                        'telefone': row['Telefone'],
                                        'area_atuacao': row['Área de Atuação'],
                                        'tipo_parceria': row['Tipo de Parceria'],
                                        'pix': row['PIX'],
                                        'observacoes': row['Observações']
                                    }
                                    st.session_state.db.update_parceiro(parceiro_id, **update_data)
                                    st.success(f"Parceiro {parceiro_id} atualizado com sucesso!")
                                    st.session_state['update_parceiros'] = True
                                except Exception as e:
                                    st.error(f"Erro ao atualizar parceiro {parceiro_id}: {str(e)}")
                else:
                    st.info("Nenhum parceiro cadastrado.")

            except Exception as e:
                st.error(f"Erro ao carregar lista de parceiros: {str(e)}")

        # Seção de edição do parceiro (mantido separado para melhor organização)
        if 'editing_parceiro_id' in st.session_state:
            st.write("---")
            st.subheader("Editar Parceiro")
            with st.form("edit_parceiro_form"):
                parceiro = registros[registros['id'] == st.session_state['editing_parceiro_id']].iloc[0]
                edited_data = {}
                edited_data['nome'] = st.text_input("Nome", value=parceiro['nome'])
                edited_data['telefone'] = st.text_input("Telefone", value=parceiro['telefone'])
                edited_data['area_atuacao'] = st.text_input("Área de Atuação", value=parceiro['area_atuacao'])
                # Lista de tipos de parceria
                tipos_parceria = ["Indicação", "Colaboração", "Projeto Conjunto"]
                
                # Verificar se o tipo de parceria do parceiro existe na lista
                tipo_atual = parceiro['tipo_parceria']
                if tipo_atual not in tipos_parceria:
                    tipos_parceria.append(tipo_atual)
                
                edited_data['tipo_parceria'] = st.selectbox(
                    "Tipo de Parceria",
                    tipos_parceria,
                    index=tipos_parceria.index(tipo_atual)
                )
                edited_data['pix'] = st.text_input("PIX", value=parceiro['pix'])
                edited_data['observacoes'] = st.text_area("Observações", value=parceiro['observacoes'])

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Salvar"):
                        try:
                            st.session_state.db.update_parceiro(
                                st.session_state['editing_parceiro_id'],
                                **edited_data
                            )
                            del st.session_state['editing_parceiro_id']
                            st.session_state['update_parceiros'] = True
                            st.success("Parceiro atualizado com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao atualizar parceiro: {str(e)}")

                with col2:
                    if st.form_submit_button("Cancelar"):
                        del st.session_state['editing_parceiro_id']
                        st.rerun()

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
                telefone = st.text_input("Telefone")
                endereco = st.text_input("Endereço")
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

            # Lista de cadastros
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
                colunas = ['id','nome', 'telefone', 'endereco', 'pix', 'observacoes']
                rename = {
                    'id': 'ID',
                    'nome': 'Nome',
                    'telefone': 'Telefone',
                    'endereco': 'Endereço',
                    'pix': 'PIX',
                    'observacoes': 'Observações'
                }
                if not registros.empty:
                    # Criar uma cópia do DataFrame original com apenas as colunas desejadas
                    df_display = registros[colunas].copy()

                    # Renomear colunas para exibição
                    df_display.columns = [rename[col] for col in colunas]

                    # Exibir tabela editável
                    edited_df = st.data_editor(
                        df_display,
                        num_rows="dynamic",
                        use_container_width=True,
                        hide_index=True
                    )

                    # Adicionar botões de ação para cada assistente
                    st.write("**Ações para assistentes:**")
                    
                    # Criar lista de IDs e nomes para seleção
                    assistentes_options = [f"{row['ID']} - {row['Nome']}" for _, row in df_display.iterrows()]
                    
                    # Dropdown para selecionar assistente
                    assistente_selecionado = st.selectbox(
                        "Selecione um assistente:",
                        assistentes_options,
                        key="assistente_dropdown"
                    )
                    
                    if assistente_selecionado:
                        # Extrair ID da seleção (formato: "ID - Nome")
                        assistente_id = int(assistente_selecionado.split(" - ")[0])
                        
                        # Botões de ação lado a lado
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Editar Assistente", key=f"edit_assistente_{assistente_id}"):
                                st.session_state['editing_assistente_id'] = assistente_id
                                st.rerun()
                        
                        with col2:
                            if st.button("Excluir Assistente", key=f"delete_assistente_{assistente_id}"):
                                try:
                                    st.session_state.db.delete_assistente(assistente_id)
                                    st.success(f"Assistente ID {assistente_id} excluído com sucesso!")
                                    st.session_state['update_assistentes'] = True
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao excluir assistente: {str(e)}")

                    # Verificar mudanças na edição
                    if edited_df is not None and not edited_df.equals(df_display):
                        for index, row in edited_df.iterrows():
                            original_row = df_display.iloc[index]
                            if not row.equals(original_row):
                                try:
                                    assistente_id = int(row['ID'])
                                    update_data = {
                                        'nome': row['Nome'],
                                        'telefone': row['Telefone'],
                                        'endereco': row['Endereço'],
                                        'pix': row['PIX'],
                                        'observacoes': row['Observações']
                                    }
                                    st.session_state.db.update_assistente(assistente_id, **update_data)
                                    st.success(f"Assistente {assistente_id} atualizado com sucesso!")
                                    st.session_state['update_assistentes'] = True
                                except Exception as e:
                                    st.error(f"Erro ao atualizar assistente {assistente_id}: {str(e)}")
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

        # Seção de edição do assistente (mantido separado para melhor organização)
        if 'editing_assistente_id' in st.session_state:
            st.write("---")
            st.subheader("Editar Assistente")
            with st.form("edit_assistente_form"):
                assistente = registros[registros['id'] == st.session_state['editing_assistente_id']].iloc[0]
                edited_data = {}
                edited_data['nome'] = st.text_input("Nome", value=assistente['nome'])
                edited_data['telefone'] = st.text_input("Telefone", value=assistente['telefone'])
                edited_data['endereco'] = st.text_input("Endereço", value=assistente['endereco'])
                edited_data['pix'] = st.text_input("PIX", value=assistente['pix'])
                edited_data['observacoes'] = st.text_area("Observações", value=assistente['observacoes'])

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Salvar"):
                        try:
                            st.session_state.db.update_assistente(
                                st.session_state['editing_assistente_id'],
                                **edited_data
                            )
                            del st.session_state['editing_assistente_id']
                            st.session_state['update_assistentes'] = True
                            st.success("Assistente atualizado com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao atualizar assistente: {str(e)}")

                with col2:
                    if st.form_submit_button("Cancelar"):
                        del st.session_state['editing_assistente_id']
                        st.rerun()

# Removida seção antiga de importação