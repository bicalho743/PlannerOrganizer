import streamlit as st
import pandas as pd
from datetime import datetime
import io

def show():
    st.title("👥 Gestão de Clientes")

    # Tabs para organizar as operações
    tab1, tab2, tab3 = st.tabs(["Cadastrar Cliente", "Lista de Clientes", "Importar Clientes"])

    with tab1:
        st.subheader("Novo Cliente")

        # Formulário de cadastro
        with st.form("cadastro_cliente"):
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
                    except Exception as e:
                        st.error(f"Erro ao cadastrar cliente: {str(e)}")
                else:
                    st.warning("Por favor, preencha todos os campos obrigatórios.")

    with tab2:
        st.subheader("Clientes Cadastrados")

        # Filtro de busca
        busca = st.text_input("🔍 Buscar cliente", "")

        # Carregar e filtrar dados
        clientes = st.session_state.db.get_clientes()

        if busca:
            clientes = clientes[
                clientes['nome'].str.contains(busca, case=False) |
                clientes['email'].str.contains(busca, case=False) |
                clientes['cpf'].str.contains(busca, case=False)
            ]

        # Exibir tabela de clientes
        if not clientes.empty:
            st.dataframe(
                clientes[[
                    'nome', 'cpf', 'email', 'telefone', 
                    'data_aniversario', 'origem_cliente',
                    'data_cadastro'
                ]],
                use_container_width=True
            )
        else:
            st.info("Nenhum cliente encontrado.")

    with tab3:
        st.subheader("Importar Clientes do Excel")

        # Instruções
        st.write("""
        Para importar clientes, seu arquivo Excel deve conter as seguintes colunas:
        - nome (obrigatório)
        - cpf
        - email
        - telefone
        - data_aniversario (formato: DD/MM/YYYY)
        - endereco
        - origem_cliente
        """)

        # Upload do arquivo
        uploaded_file = st.file_uploader("Escolha o arquivo Excel", type=['xlsx', 'xls'])

        if uploaded_file is not None:
            try:
                # Ler o arquivo Excel
                df = pd.read_excel(uploaded_file)

                # Verificar se tem a coluna obrigatória
                if 'nome' not in df.columns:
                    st.error("O arquivo deve conter uma coluna 'nome'")
                else:
                    # Mostrar preview dos dados
                    st.write("Preview dos dados:")
                    st.dataframe(df.head())

                    if st.button("Confirmar Importação"):
                        # Contador de sucesso
                        success_count = 0
                        error_count = 0

                        # Progress bar
                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        # Processar cada linha
                        for index, row in df.iterrows():
                            try:
                                # Converter data se existir
                                data_aniv = None
                                if 'data_aniversario' in row and pd.notna(row['data_aniversario']):
                                    if isinstance(row['data_aniversario'], str):
                                        data_aniv = datetime.strptime(row['data_aniversario'], '%d/%m/%Y').date()
                                    else:
                                        data_aniv = row['data_aniversario'].date()

                                # Adicionar cliente
                                st.session_state.db.add_cliente(
                                    nome=row['nome'],
                                    email=row.get('email', ''),
                                    telefone=row.get('telefone', ''),
                                    endereco=row.get('endereco', ''),
                                    cpf=row.get('cpf', ''),
                                    data_aniversario=data_aniv,
                                    origem_cliente=row.get('origem_cliente', 'Importação')
                                )
                                success_count += 1
                            except Exception as e:
                                error_count += 1
                                st.error(f"Erro ao importar linha {index + 1}: {str(e)}")

                            # Atualizar progress bar
                            progress = (index + 1) / len(df)
                            progress_bar.progress(progress)
                            status_text.text(f"Processando... {index + 1} de {len(df)}")

                        # Mostrar resultado final
                        st.success(f"""
                        Importação concluída!
                        - Clientes importados com sucesso: {success_count}
                        - Erros de importação: {error_count}
                        """)

            except Exception as e:
                st.error(f"Erro ao ler o arquivo: {str(e)}")