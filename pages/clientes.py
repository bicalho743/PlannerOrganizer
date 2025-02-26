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

        # Atualizar lista de clientes
        try:
            clientes = st.session_state.db.get_clientes()

            if clientes.empty:
                st.info("Nenhum cliente cadastrado.")
                return

            # Converter datas para datetime
            clientes['data_cadastro'] = pd.to_datetime(clientes['data_cadastro'], errors='coerce')
            clientes['data_aniversario'] = pd.to_datetime(clientes['data_aniversario'], errors='coerce')

            # Definir colunas para exibição na ordem da planilha de importação
            colunas = [
                'id',           # ID sempre primeiro
                'nome',         # Dados básicos
                'tipo_conta',
                'cpf',         # Documentos
                'cnpj',
                'razao_social',
                'email',
                'telefone',
                'estado',      # Endereço
                'cidade',
                'bairro',
                'endereco',
                'data_aniversario',
                'origem_cliente',
                'data_cadastro'
            ]

            rename = {
                'id': 'ID',
                'nome': 'Nome',
                'tipo_conta': 'Tipo de Conta',
                'cpf': 'CPF',
                'cnpj': 'CNPJ',
                'razao_social': 'Razão Social',
                'email': 'Email',
                'telefone': 'Telefone',
                'estado': 'Estado',
                'cidade': 'Cidade',
                'bairro': 'Bairro',
                'endereco': 'Endereço',
                'data_aniversario': 'Aniversário',
                'origem_cliente': 'Origem',
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
                                telefone = str(row.get('telefone', '')) if pd.notna(row.get('telefone')) else None
                                if telefone:
                                    telefone = ''.join(filter(str.isdigit, telefone))

                                # Processar CPF/CNPJ
                                tipo_conta = str(row.get('tipo_conta', 'PF')).upper()
                                cpf = None
                                cnpj = None
                                razao_social = None

                                if tipo_conta == 'PF' and pd.notna(row.get('cpf')):
                                    cpf = str(row['cpf']).strip()
                                elif tipo_conta == 'PJ':
                                    if pd.notna(row.get('cnpj')):
                                        cnpj = str(row['cnpj']).strip()
                                    if pd.notna(row.get('razao_social')):
                                        razao_social = str(row['razao_social']).strip()

                                # Processar data de aniversário
                                data_aniv = None
                                if pd.notna(row.get('data_aniversario')):
                                    try:
                                        if isinstance(row['data_aniversario'], str):
                                            data = datetime.strptime(row['data_aniversario'], '%d/%m')
                                        else:
                                            data = pd.to_datetime(row['data_aniversario'])
                                        data_aniv = datetime.now().replace(
                                            month=data.month,
                                            day=data.day
                                        ).date()
                                    except Exception as e:
                                        st.warning(f"Data de aniversário inválida na linha {index + 2}")

                                st.session_state.db.add_cliente(
                                    nome=str(row['nome']).strip(),
                                    email=str(row.get('email', '')).strip() if pd.notna(row.get('email')) else None,
                                    telefone=telefone,
                                    estado=str(row.get('estado', '')).strip() if pd.notna(row.get('estado')) else None,
                                    cidade=str(row.get('cidade', '')).strip() if pd.notna(row.get('cidade')) else None,
                                    bairro=str(row.get('bairro', '')).strip() if pd.notna(row.get('bairro')) else None,
                                    endereco=str(row.get('endereco', '')).strip() if pd.notna(row.get('endereco')) else None,
                                    cpf=cpf,
                                    tipo_conta=tipo_conta,
                                    cnpj=cnpj,
                                    razao_social=razao_social,
                                    data_aniversario=data_aniv,
                                    origem_cliente=str(row.get('origem_cliente', 'Importação')).strip() if pd.notna(row.get('origem_cliente')) else 'Importação'
                                )
                                success_count += 1
                            except Exception as e:
                                error_count += 1
                                st.error(f"Erro ao importar linha {index + 2}: {str(e)}")

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