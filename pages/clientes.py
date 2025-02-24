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

            if tipo_conta == "PF":
                cpf = st.text_input("CPF")
                cnpj = None
                razao_social = None
            else:
                cpf = None
                cnpj = st.text_input("CNPJ")
                razao_social = st.text_input("Razão Social")

            col1, col2 = st.columns(2)
            with col1:
                email = st.text_input("E-mail")
                data_aniversario = st.date_input("Data de Aniversário", format="DD/MM/YYYY")
            with col2:
                telefone = st.text_input("Telefone")
                origem_cliente = st.selectbox(
                    "Onde conheceu a Personal Organizer?",
                    ["Indicação", "Redes Sociais", "Site", "Evento", "Outro"]
                )

            # Campos de endereço
            st.subheader("Endereço")
            col1, col2 = st.columns(2)
            with col1:
                estado = st.text_input("Estado")
                bairro = st.text_input("Bairro")
            with col2:
                cidade = st.text_input("Cidade")
                endereco = st.text_input("Endereço (Rua, número, complemento)")

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
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao cadastrar cliente: {str(e)}")
                else:
                    st.warning("Por favor, preencha todos os campos obrigatórios.")

    with tab2:
        st.subheader("Clientes Cadastrados")
        busca = st.text_input("🔍 Buscar cliente", "")

        try:
            clientes = st.session_state.db.get_clientes()

            if not clientes.empty:
                # Converter datas para datetime
                clientes['data_cadastro'] = pd.to_datetime(clientes['data_cadastro'], errors='coerce')
                clientes['data_aniversario'] = pd.to_datetime(clientes['data_aniversario'], errors='coerce')

                # Formatar datas para exibição
                clientes['data_cadastro'] = clientes['data_cadastro'].dt.strftime('%d/%m/%Y')
                clientes['data_aniversario'] = clientes['data_aniversario'].dt.strftime('%d/%m')

                # Aplicar filtro de busca
                if busca:
                    mask = clientes.apply(lambda row: any(
                        str(value).lower().find(busca.lower()) != -1
                        for value in [row['nome'], row['email'], row['cpf'], row['cnpj']]
                        if pd.notna(value)
                    ), axis=1)
                    clientes = clientes[mask]

                # Para cada cliente, mostrar os dados e botões de ação
                for _, cliente in clientes.iterrows():
                    with st.container():
                        col1, col2 = st.columns([4, 1])

                        with col1:
                            st.markdown(f"**{cliente['nome']}**")
                            st.markdown(f"Email: {cliente['email']}")
                            st.markdown(f"Telefone: {cliente['telefone']}")
                            if cliente['tipo_conta'] == 'PF':
                                st.markdown(f"CPF: {cliente['cpf']}")
                            else:
                                st.markdown(f"CNPJ: {cliente['cnpj']}")
                                st.markdown(f"Razão Social: {cliente['razao_social']}")

                            # Exibir informações de endereço
                            endereco_completo = []
                            if cliente['endereco']:
                                endereco_completo.append(cliente['endereco'])
                            if cliente['bairro']:
                                endereco_completo.append(cliente['bairro'])
                            if cliente['cidade']:
                                endereco_completo.append(cliente['cidade'])
                            if cliente['estado']:
                                endereco_completo.append(cliente['estado'])

                            if endereco_completo:
                                st.markdown(f"Endereço: {' - '.join(endereco_completo)}")

                        with col2:
                            if st.button("🗑️ Excluir", key=f"del_cliente_{cliente['id']}"):
                                sucesso, msg = st.session_state.db.excluir_cliente(cliente['id'])
                                if sucesso:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)

                        st.markdown("---")
            else:
                st.info("Nenhum cliente cadastrado.")

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
        - data_aniversario (formato: DD/MM)
        - endereco
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

                                tipo_conta = str(row.get('tipo_conta', 'PF')).upper()
                                if tipo_conta not in ['PF', 'PJ']:
                                    tipo_conta = 'PF'

                                st.session_state.db.add_cliente(
                                    nome=str(row['nome']),
                                    tipo_conta=tipo_conta,
                                    email=str(row.get('email', '')),
                                    telefone=str(row.get('telefone', '')),
                                    endereco=str(row.get('endereco', '')),
                                    cpf=str(row.get('cpf', '')) if tipo_conta == 'PF' else None,
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
                        st.rerun()

            except Exception as e:
                st.error(f"Erro ao ler o arquivo: {str(e)}")