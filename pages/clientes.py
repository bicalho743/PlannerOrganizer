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
            cpf = st.text_input("CPF")
            email = st.text_input("E-mail")
            telefone = st.text_input("Telefone")
            data_aniversario = st.date_input("Data de Aniversário")
            endereco = st.text_area("Endereço")
            origem_cliente = st.selectbox(
                "Onde conheceu a Personal Organizer?",
                ["Indicação", "Redes Sociais", "Site", "Evento", "Outro"]
            )

            submitted = st.form_submit_button("Cadastrar")

            if submitted:
                if nome and cpf and telefone:
                    try:
                        st.session_state.db.add_cliente(
                            nome=nome,
                            email=email,
                            telefone=telefone,
                            endereco=endereco,
                            cpf=cpf,
                            data_aniversario=data_aniversario,
                            origem_cliente=origem_cliente
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
                clientes['data_cadastro'] = pd.to_datetime(clientes['data_cadastro'])
                clientes['data_aniversario'] = pd.to_datetime(clientes['data_aniversario'], errors='coerce')

                # Formatar datas para exibição
                clientes['data_cadastro'] = clientes['data_cadastro'].dt.strftime('%d/%m/%Y')
                clientes['data_aniversario'] = clientes['data_aniversario'].dt.strftime('%d/%m')

                # Aplicar filtro de busca
                if busca:
                    mask = (
                        clientes['nome'].str.contains(busca, case=False, na=False) |
                        clientes['email'].str.contains(busca, case=False, na=False) |
                        clientes['cpf'].str.contains(busca, case=False, na=False)
                    )
                    clientes = clientes[mask]

                # Exibir tabela de clientes
                st.dataframe(
                    clientes[[
                        'nome', 'cpf', 'email', 'telefone',
                        'data_aniversario', 'origem_cliente',
                        'data_cadastro'
                    ]],
                    use_container_width=True
                )
            else:
                st.info("Nenhum cliente cadastrado.")

        except Exception as e:
            st.error(f"Erro ao carregar clientes: {str(e)}")

    with tab3:
        st.subheader("Importar Clientes do Excel")

        st.write("""
        Para importar clientes, seu arquivo Excel deve conter as seguintes colunas:
        - nome (obrigatório)
        - cpf
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
                                        data = pd.to_datetime(row['data_aniversario'])
                                        data_aniv = datetime.now().replace(
                                            day=data.day,
                                            month=data.month
                                        ).date()
                                    except:
                                        pass

                                st.session_state.db.add_cliente(
                                    nome=str(row['nome']),
                                    email=str(row.get('email', '')),
                                    telefone=str(row.get('telefone', '')),
                                    endereco=str(row.get('endereco', '')),
                                    cpf=str(row.get('cpf', '')),
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