import streamlit as st
import pandas as pd
from utils.importador import importar_cadastros, gerar_template_excel, testar_conexao_db

def show():
    # Verificar se o db está na sessão
    if 'db' not in st.session_state:
        st.error("Erro: Conexão com banco de dados não inicializada")
        return

    st.title("📥 Importação de Dados")

    # Testar conexão com o banco de dados
    if not testar_conexao_db(st.session_state.db):
        st.error("Erro de conexão com o banco de dados. Por favor, verifique se o banco está disponível.")
        return

    # Abas para diferentes tipos de importação
    tab1, tab2 = st.tabs(["Importar Cadastros", "Importar Propostas"])

    with tab1:
        st.subheader("Importar Cadastros")

        # Seletor de tipo de cadastro
        tipo_cadastro = st.selectbox(
            "Tipo de Cadastro",
            ["Cliente", "Fornecedor", "Assistente", "Parceiro"],
            key="tipo_cadastro_import"
        )

        if tipo_cadastro == "Cliente":
            st.write("""
            ### Instruções para importação de Clientes:
            1. Primeiro, baixe o template Excel clicando no botão abaixo
            2. Preencha o arquivo com os dados dos clientes:
               - **Campos obrigatórios**: nome, telefone, email
               - **Tipo de conta**: deve ser 'PF' ou 'PJ' (em maiúsculas)
               - Para clientes PF:
                 * Preencha o campo CPF
               - Para clientes PJ:
                 * Preencha os campos CNPJ e Razão Social
               - **Data de aniversário**: formato DD/MM/YYYY
            3. **IMPORTANTE**: Não altere o nome das colunas no arquivo
            4. Salve o arquivo e faça o upload abaixo

            ### Exemplo de preenchimento:
            Para cliente PF:
            - nome: João Silva
            - telefone: (11) 98765-4321
            - email: joao@email.com
            - tipo_conta: PF
            - cpf: 123.456.789-00
            - data_aniversario: 15/03/1980

            Para cliente PJ:
            - nome: Empresa XYZ
            - telefone: (11) 3456-7890
            - email: contato@xyz.com
            - tipo_conta: PJ
            - cnpj: 12.345.678/0001-90
            - razao_social: XYZ Comércio Ltda
            """)
        else:
            st.write("""
            ### Instruções para importação:
            1. Primeiro, baixe o template Excel clicando no botão abaixo
            2. Preencha o arquivo seguindo as instruções:
               - Campos obrigatórios: nome, telefone, email
               - Não altere o nome das colunas
            3. Salve o arquivo e faça o upload
            """)

        # Botão para baixar template
        template = gerar_template_excel(tipo_cadastro)
        st.download_button(
            f"📝 Baixar Template {tipo_cadastro}",
            template,
            f"template_{tipo_cadastro.lower()}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help=f"Baixe este template Excel, preencha com seus dados e faça upload para importar {tipo_cadastro}s",
            key=f"download_template_{tipo_cadastro.lower()}"
        )

        # Upload do arquivo
        st.write("### Upload do Arquivo")
        arquivo = st.file_uploader(
            f"Selecione o arquivo Excel de {tipo_cadastro}s",
            type=['xlsx', 'xls', 'csv'],
            help="Você pode fazer upload de arquivos Excel (.xlsx, .xls) ou CSV",
            key=f"upload_file_{tipo_cadastro.lower()}"
        )

        if arquivo:
            try:
                # Mostrar preview dos dados
                if arquivo.name.endswith(('.xlsx', '.xls')):
                    preview = pd.read_excel(arquivo)
                else:
                    preview = pd.read_csv(arquivo)

                st.write("### Preview dos dados:")
                st.info("Verifique se os dados estão corretos antes de confirmar a importação:")
                st.dataframe(preview.head())

                # Mostrar colunas encontradas
                st.write("### Colunas encontradas no arquivo:")
                colunas = preview.columns.tolist()
                st.write(", ".join(colunas))

                # Usar um prefixo único para cada botão
                button_key = f"confirmar_importacao_{tipo_cadastro.lower()}"
                if st.button(f"Confirmar Importação de {tipo_cadastro}s", key=button_key):
                    with st.spinner("Importando dados..."):
                        sucesso, mensagem = importar_cadastros(arquivo, tipo_cadastro, st.session_state.db)
                        if sucesso:
                            st.success(mensagem)
                            # Atualizar a lista do tipo correspondente
                            st.session_state[f'update_{tipo_cadastro.lower()}s'] = True
                            # Limpar o arquivo do estado da sessão
                            st.session_state[f"upload_file_{tipo_cadastro.lower()}"] = None
                        else:
                            st.error(mensagem)

            except Exception as e:
                st.error(f"Erro ao ler o arquivo: {str(e)}")

    with tab2:
        st.subheader("Importar Propostas")
        st.info("Funcionalidade em desenvolvimento")