import streamlit as st
import pandas as pd
from datetime import datetime
import logging
import traceback

logger = logging.getLogger(__name__)

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
                    except Exception as e:
                        st.error(f"Erro ao cadastrar cliente: {str(e)}")
                else:
                    st.warning("Por favor, preencha todos os campos obrigatórios.")

    with tab2:
        st.subheader("Clientes Cadastrados")

        try:
            clientes = st.session_state.db.get_clientes()

            if clientes.empty:
                st.info("Nenhum cliente cadastrado.")
                return

            # Converter datas para datetime
            clientes['data_cadastro'] = pd.to_datetime(clientes['data_cadastro'], errors='coerce')
            clientes['data_aniversario'] = pd.to_datetime(clientes['data_aniversario'], errors='coerce')

            df_display = clientes.copy()

            # Formatar datas para exibição
            if 'data_cadastro' in df_display.columns:
                df_display['data_cadastro'] = pd.to_datetime(df_display['data_cadastro']).dt.strftime('%d/%m/%Y')
            if 'data_aniversario' in df_display.columns:
                df_display['data_aniversario'] = pd.to_datetime(df_display['data_aniversario']).dt.strftime('%d/%m')

            # Exibir tabela com todos os dados
            st.dataframe(
                df_display,
                hide_index=True,
                use_container_width=True
            )

        except Exception as e:
            st.error(f"Erro ao carregar clientes: {str(e)}")

    with tab3:
        st.subheader("🧪 Teste de Importação")

        # Log do estado da sessão
        logger.info("=== Estado da Sessão ===")
        for key, value in st.session_state.items():
            if key not in ['senha', 'token']:
                logger.info(f"{key}: {value}")

        st.write("""
        Para importar clientes, seu arquivo CSV deve ter o seguinte formato:
        - Usar vírgula (,) como separador
        - Uma linha por cliente
        - As seguintes colunas são esperadas:
          - nome (obrigatório)
          - email
          - telefone
          - tipo_conta (PF ou PJ)
          - cpf (para PF)
          - estado
          - cidade
          - bairro
          - endereco
          - data_aniversario (formato: DD/MM)

        Exemplo:
        nome,telefone,email,tipo_conta,cpf
        João Silva,11999999999,joao@email.com,PF,12345678900
        """)

        uploaded_file = st.file_uploader("Escolha o arquivo CSV", type=['csv'])

        if uploaded_file is not None:
            try:
                # Tentar diferentes codificações
                encodings = ['utf-8', 'latin1', 'iso-8859-1']
                df = None
                encoding_used = None

                for encoding in encodings:
                    try:
                        # Exibir preview do arquivo antes de processar
                        file_preview = uploaded_file.getvalue().decode(encoding, errors='replace').splitlines()[:5]
                        logger.info(f"Preview do arquivo (primeiras 5 linhas):")
                        for line in file_preview:
                            logger.info(line)

                        # Usar sep=',' explicitamente
                        df = pd.read_csv(
                            uploaded_file, 
                            encoding=encoding,
                            sep=',',  # Forçar uso de vírgula como separador
                            skipinitialspace=True,  # Ignorar espaços após a vírgula
                            na_values=['', 'NA', 'null'],  # Valores a serem tratados como NA
                            engine='python',  # Usar engine python para melhor tratamento de erros
                            on_bad_lines='warn'  # Avisar sobre linhas problemáticas ao invés de falhar
                        )
                        encoding_used = encoding
                        break
                    except UnicodeDecodeError:
                        continue
                    except Exception as e:
                        logger.error(f"Erro ao tentar ler o arquivo com codificação {encoding}: {str(e)}")
                        logger.error(f"Stack trace: {traceback.format_exc()}")
                        continue

                if df is None:
                    st.error("""
                    Não foi possível ler o arquivo CSV. Por favor, verifique se:
                    1. O arquivo está usando vírgula (,) como separador
                    2. As colunas estão corretas e separadas por vírgula
                    3. Não há vírgulas dentro dos campos de texto
                    4. O arquivo foi salvo com codificação adequada (UTF-8 ou Latin1)
                    """)
                    return

                logger.info(f"Arquivo carregado com sucesso usando codificação {encoding_used}")
                logger.info(f"Colunas encontradas: {df.columns.tolist()}")

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
                                # Processar dados
                                nome = str(row['nome']).strip() if pd.notna(row.get('nome')) else None
                                if not nome:
                                    raise ValueError("Nome é obrigatório")

                                # Log dos dados antes do processamento
                                logger.info(f"Processando linha {index + 2}:")
                                logger.info(f"CPF original: {row.get('cpf')}")
                                logger.info(f"Tipo conta: {row.get('tipo_conta')}")

                                # Processar telefone
                                telefone = str(row.get('telefone', '')).strip() if pd.notna(row.get('telefone')) else None
                                if telefone:
                                    telefone = ''.join(filter(str.isdigit, telefone))

                                # Processar tipo de conta e documentos
                                tipo_conta = str(row.get('tipo_conta', 'PF')).upper().strip()

                                # Processar CPF
                                cpf = None
                                if tipo_conta == 'PF':
                                    if pd.notna(row.get('cpf')):
                                        cpf = str(row['cpf']).strip()
                                        cpf = ''.join(filter(str.isdigit, cpf))
                                        logger.info(f"CPF processado: {cpf}")

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
                                        logger.warning(f"Erro ao processar data de aniversário na linha {index + 2}: {str(e)}")

                                # Log antes de adicionar ao banco
                                logger.info(f"Dados processados para adicionar ao banco:")
                                logger.info(f"Nome: {nome}")
                                logger.info(f"CPF final: {cpf}")
                                logger.info(f"Tipo conta final: {tipo_conta}")

                                # Adicionar cliente ao banco
                                cliente_id = st.session_state.db.add_cliente(
                                    nome=nome,
                                    email=str(row.get('email', '')).strip() if pd.notna(row.get('email')) else None,
                                    telefone=telefone,
                                    estado=str(row.get('estado', '')).strip() if pd.notna(row.get('estado')) else None,
                                    cidade=str(row.get('cidade', '')).strip() if pd.notna(row.get('cidade')) else None,
                                    bairro=str(row.get('bairro', '')).strip() if pd.notna(row.get('bairro')) else None,
                                    endereco=str(row.get('endereco', '')).strip() if pd.notna(row.get('endereco')) else None,
                                    cpf=cpf,
                                    data_aniversario=data_aniv,
                                    origem_cliente=str(row.get('origem_cliente', 'Importação')).strip() if pd.notna(row.get('origem_cliente')) else 'Importação',
                                    tipo_conta=tipo_conta
                                )
                                logger.info(f"Cliente adicionado com sucesso. ID: {cliente_id}")
                                success_count += 1
                            except Exception as e:
                                error_count += 1
                                error_msg = f"Erro ao importar linha {index + 2}: {str(e)}"
                                logger.error(error_msg)
                                logger.error(f"Stack trace: {traceback.format_exc()}")
                                st.error(error_msg)

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
                logger.error(f"Erro ao ler arquivo CSV: {str(e)}")
                logger.error(f"Stack trace: {traceback.format_exc()}")