import streamlit as st
import pandas as pd
from datetime import datetime

def show():
    st.title("👥 Gestão de Clientes")

    tab1, tab2, tab3 = st.tabs(["Cadastrar Cliente", "Lista de Clientes", "Importar Clientes"])

    with tab1:
        st.subheader("Novo Cliente")
        with st.form("cadastro_cliente", clear_on_submit=True):
            nome = st.text_input("Nome completo")
            tipo_conta = st.selectbox(
                "Tipo de Conta",
                ["PF", "PJ"]
            )

            telefone = st.text_input("Telefone")
            if telefone:
                # Remover pontuação e espaços
                telefone = ''.join(filter(str.isdigit, telefone))
                if len(telefone) != 11:
                    st.error("Telefone deve ter 11 dígitos")
                    return

            if tipo_conta == "PF":
                cpf = st.text_input("CPF")
                if cpf:
                    # Remover pontuação e espaços
                    cpf = ''.join(filter(str.isdigit, cpf))
                    if len(cpf) != 11:
                        st.error("CPF deve ter 11 dígitos")
                        return
                cnpj = None
                razao_social = None
            else:
                cpf = None
                cnpj = st.text_input("CNPJ")
                razao_social = st.text_input("Razão Social")

            col1, col2 = st.columns(2)
            with col1:
                email = st.text_input("E-mail")
            with col2:
                data_aniversario = st.date_input("Data de Aniversário", format="DD/MM/YYYY")
                origem_cliente = st.selectbox(
                    "Onde conheceu a Personal Organizer?",
                    ["Indicação", "Redes Sociais", "Site", "Evento", "Outro"]
                )

            # Seção de Endereço
            st.write("---")
            st.subheader("Endereço")
            col1, col2 = st.columns(2)
            with col1:
                estado = st.text_input("Estado (UF)")
                cidade = st.text_input("Cidade")
            with col2:
                bairro = st.text_input("Bairro")
                endereco = st.text_input("Endereço completo (Rua, número, complemento)")

            submitted = st.form_submit_button("Cadastrar")

            if submitted:
                if nome and telefone and (
                    (tipo_conta == "PF" and cpf) or 
                    (tipo_conta == "PJ" and cnpj and razao_social)
                ):
                    try:
                        st.session_state.db.add_cliente(
                            nome=nome,
                            email=email,
                            telefone=telefone,
                            estado=estado,
                            cidade=cidade,
                            bairro=bairro,
                            endereco=endereco,
                            cpf=cpf,
                            data_aniversario=data_aniversario,
                            origem_cliente=origem_cliente,
                            tipo_conta=tipo_conta,
                            cnpj=cnpj,
                            razao_social=razao_social
                        )
                        st.success("Cliente cadastrado com sucesso!")
                        st.session_state['update_clientes'] = True
                    except Exception as e:
                        st.error(f"Erro ao cadastrar cliente: {str(e)}")
                else:
                    st.warning("Por favor, preencha todos os campos obrigatórios.")

    with tab2:
        st.subheader("Clientes Cadastrados")
        busca = st.text_input("🔍 Buscar cliente", "")

        try:
            @st.cache_data(ttl=60)
            def load_clientes():
                return st.session_state.db.get_clientes()

            if 'update_clientes' in st.session_state and st.session_state['update_clientes']:
                st.session_state['clientes'] = load_clientes()
                st.session_state['update_clientes'] = False
            elif 'clientes' not in st.session_state:
                st.session_state['clientes'] = load_clientes()

            clientes = st.session_state['clientes']

            if clientes.empty:
                st.info("Nenhum cliente cadastrado.")
                return

            # Converter datas para datetime
            clientes['data_cadastro'] = pd.to_datetime(clientes['data_cadastro'], errors='coerce')
            clientes['data_aniversario'] = pd.to_datetime(clientes['data_aniversario'], errors='coerce')

            # Aplicar filtro de busca
            if busca:
                mask = clientes.apply(lambda row: any(
                    str(value).lower().find(busca.lower()) != -1
                    for value in [row['nome'], row['email'], row['cpf'], row['cnpj']]
                    if pd.notna(value)
                ), axis=1)
                clientes = clientes[mask]

            # Definir colunas para exibição
            colunas = ['id', 'nome', 'email', 'telefone', 'tipo_conta', 'cpf', 'cnpj', 
                      'razao_social', 'data_aniversario', 'origem_cliente', 'estado', 
                      'cidade', 'bairro', 'endereco', 'data_cadastro']
            rename = {
                'id': 'ID',
                'nome': 'Nome',
                'email': 'Email',
                'telefone': 'Telefone',
                'tipo_conta': 'Tipo de Conta',
                'cpf': 'CPF',
                'cnpj': 'CNPJ',
                'razao_social': 'Razão Social',
                'data_aniversario': 'Aniversário',
                'origem_cliente': 'Origem',
                'estado': 'Estado',
                'cidade': 'Cidade',
                'bairro': 'Bairro',
                'endereco': 'Endereço',
                'data_cadastro': 'Data Cadastro'
            }

            # Criar DataFrame para exibição
            df_display = clientes[colunas].copy()
            df_display.columns = [rename[col] for col in colunas]

            # Formatar datas para exibição
            if 'Data Cadastro' in df_display.columns:
                df_display['Data Cadastro'] = pd.to_datetime(df_display['Data Cadastro']).dt.strftime('%d/%m/%Y')
            if 'Aniversário' in df_display.columns:
                df_display['Aniversário'] = pd.to_datetime(df_display['Aniversário']).dt.strftime('%d/%m')

            # Exibir tabela com todos os dados
            st.dataframe(
                df_display,
                hide_index=True,
                use_container_width=True
            )

            # Botões de ação
            col1, col2 = st.columns(2)
            with col1:
                registro_id = st.number_input(
                    "ID do cliente para ação:",
                    min_value=1,
                    max_value=len(clientes) if not clientes.empty else 1,
                    step=1
                )

            with col2:
                acao = st.selectbox("Ação:", ["Editar", "Excluir"])

            # Formulário de ação
            with st.form(f"acao_cliente"):
                if st.form_submit_button(f"Confirmar {acao}"):
                    cliente = clientes[clientes['id'] == registro_id].iloc[0]

                    if acao == "Excluir":
                        try:
                            sucesso, msg = st.session_state.db.excluir_cliente(registro_id)
                            if sucesso:
                                st.success(msg)
                                st.session_state['update_clientes'] = True
                            else:
                                st.error(msg)
                        except Exception as e:
                            st.error(f"Erro ao excluir cliente: {str(e)}")
                    elif acao == "Editar":
                        st.session_state[f'editing_{registro_id}'] = True

            # Formulário de edição
            if st.session_state.get(f'editing_{registro_id}', False):
                with st.form(f"edit_form_{registro_id}"):
                    cliente = clientes[clientes['id'] == registro_id].iloc[0]

                    edited_data = {}
                    edited_data['nome'] = st.text_input("Nome", value=cliente['nome'])
                    edited_data['email'] = st.text_input("Email", value=cliente['email'] or '')
                    edited_data['telefone'] = st.text_input("Telefone", value=cliente['telefone'] or '')
                    edited_data['endereco'] = st.text_input("Endereço", value=cliente['endereco'] or '')

                    col1, col2 = st.columns(2)
                    with col1:
                        edited_data['estado'] = st.text_input("Estado", value=cliente['estado'] or '')
                        edited_data['cidade'] = st.text_input("Cidade", value=cliente['cidade'] or '')
                    with col2:
                        edited_data['bairro'] = st.text_input("Bairro", value=cliente['bairro'] or '')
                        edited_data['data_aniversario'] = st.date_input(
                            "Data Aniversário",
                            value=pd.to_datetime(cliente['data_aniversario']).date() if pd.notna(cliente['data_aniversario']) else None
                        )

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("Salvar Alterações"):
                            try:
                                st.session_state.db.atualizar_cliente(
                                    cliente['id'],
                                    **edited_data
                                )
                                del st.session_state[f'editing_{registro_id}']
                                st.success("Cliente atualizado com sucesso!")
                                st.session_state['update_clientes'] = True
                            except Exception as e:
                                st.error(f"Erro ao atualizar cliente: {str(e)}")

                    with col2:
                        if st.form_submit_button("Cancelar"):
                            del st.session_state[f'editing_{registro_id}']

        except Exception as e:
            st.error(f"Erro ao carregar clientes: {str(e)}")

    with tab3:
        st.subheader("Importar Clientes do Excel")

        st.write("""
        Para importar clientes, seu arquivo Excel deve conter as seguintes colunas:
        - nome (obrigatório)
        - tipo_conta (PF ou PJ)
        - cpf (para PF)
        - cnpj (para PJ)
        - razao_social (para PJ)
        - email
        - telefone
        - estado
        - cidade
        - bairro
        - endereco
        - data_aniversario (formato: DD/MM)
        - origem_cliente
        """)

        uploaded_file = st.file_uploader("Escolha o arquivo Excel", type=['xlsx', 'xls'])

        if uploaded_file is not None:
            try:
                df = pd.read_excel(uploaded_file)

                if 'nome' not in df.columns:
                    st.error("O arquivo deve conter uma coluna 'nome'")
                else:
                    st.write("Preview dos dados:")
                    st.dataframe(df.head())

                    if st.button("Confirmar Importação"):
                        success_count = 0
                        error_count = 0

                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        for index, row in df.iterrows():
                            try:
                                # Processar telefone
                                telefone = str(row.get('telefone', ''))
                                telefone = ''.join(filter(str.isdigit, telefone))
                                if len(telefone) != 11:
                                    st.warning(f"Telefone inválido na linha {index + 1}")
                                    continue

                                # Processar CPF
                                tipo_conta = str(row.get('tipo_conta', 'PF')).upper()
                                if tipo_conta == 'PF':
                                    cpf = str(row.get('cpf', ''))
                                    cpf = ''.join(filter(str.isdigit, cpf))
                                    if len(cpf) != 11:
                                        st.warning(f"CPF inválido na linha {index + 1}")
                                        continue

                                # Processar data de aniversário
                                data_aniv = None
                                if 'data_aniversario' in row and pd.notna(row['data_aniversario']):
                                    try:
                                        if isinstance(row['data_aniversario'], str):
                                            data = datetime.strptime(row['data_aniversario'], '%d/%m')
                                        else:
                                            data = pd.to_datetime(row['data_aniversario'])
                                        data_aniv = datetime.now().replace(
                                            month=data.month,
                                            day=data.day
                                        ).date()
                                    except Exception:
                                        st.warning(f"Data de aniversário inválida na linha {index + 1}")

                                st.session_state.db.add_cliente(
                                    nome=str(row['nome']),
                                    tipo_conta=tipo_conta,
                                    email=str(row.get('email', '')),
                                    telefone=telefone,
                                    estado=str(row.get('estado', '')),
                                    cidade=str(row.get('cidade', '')),
                                    bairro=str(row.get('bairro', '')),
                                    endereco=str(row.get('endereco', '')),
                                    cpf=cpf if tipo_conta == 'PF' else None,
                                    cnpj=str(row.get('cnpj', '')) if tipo_conta == 'PJ' else None,
                                    razao_social=str(row.get('razao_social', '')) if tipo_conta == 'PJ' else None,
                                    data_aniversario=data_aniv,
                                    origem_cliente=str(row.get('origem_cliente', 'Importação'))
                                )
                                success_count += 1
                            except Exception as e:
                                error_count += 1
                                st.error(f"Erro ao importar linha {index + 1}: {str(e)}")

                            progress = (index + 1) / len(df)
                            progress_bar.progress(progress)
                            status_text.text(f"Processando... {index + 1} de {len(df)}")

                        st.success(f"""
                        Importação concluída!
                        - Clientes importados com sucesso: {success_count}
                        - Erros de importação: {error_count}
                        """)

            except Exception as e:
                st.error(f"Erro ao ler o arquivo: {str(e)}")