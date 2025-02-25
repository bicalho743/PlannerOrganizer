import streamlit as st
import pandas as pd
from utils.importador import importar_cadastros, importar_propostas, gerar_template_excel

def show():
    st.title("📥 Importação de Dados")

    # Abas para diferentes tipos de importação
    tab1, tab2 = st.tabs(["Importar Cadastros", "Importar Propostas"])

    with tab1:
        st.subheader("Importar Cadastros")

        # Seletor de tipo de cadastro
        tipo_cadastro = st.selectbox(
            "Tipo de Cadastro",
            ["Cliente", "Fornecedor", "Assistente", "Parceiro"]
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
            help=f"Baixe este template Excel, preencha com seus dados e faça upload para importar {tipo_cadastro}s"
        )

        # Upload do arquivo
        st.write("### Upload do Arquivo")
        arquivo = st.file_uploader(
            f"Selecione o arquivo Excel de {tipo_cadastro}s",
            type=['xlsx', 'xls', 'csv'],
            help="Você pode fazer upload de arquivos Excel (.xlsx, .xls) ou CSV"
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

                if st.button(f"Confirmar Importação de {tipo_cadastro}s"):
                    with st.spinner("Importando dados..."):
                        sucesso, mensagem = importar_cadastros(arquivo, tipo_cadastro, st.session_state.db)
                        if sucesso:
                            st.success(mensagem)
                            st.rerun()
                        else:
                            st.error(mensagem)
            except Exception as e:
                st.error(f"Erro ao ler o arquivo: {str(e)}")

    with tab2:
        st.subheader("Importar Propostas")

        st.write("""
        ### Instruções para importação de propostas:
        1. Baixe o template Excel
        2. Preencha os dados seguindo o formato:
           - cliente_id: ID do cliente (número)
           - valor: valor da proposta (número)
           - datas: formato DD/MM/YYYY
        3. Não altere o nome das colunas
        """)

        # Botão para baixar template
        template = gerar_template_excel("Proposta")
        st.download_button(
            "📝 Baixar Template Proposta",
            template,
            "template_proposta.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Baixe este template Excel, preencha com seus dados e faça upload para importar propostas"
        )

        # Upload do arquivo
        arquivo = st.file_uploader(
            "Selecione o arquivo Excel de Propostas",
            type=['xlsx', 'xls', 'csv'],
            help="Você pode fazer upload de arquivos Excel (.xlsx, .xls) ou CSV"
        )

        if arquivo:
            try:
                if arquivo.name.endswith(('.xlsx', '.xls')):
                    preview = pd.read_excel(arquivo)
                else:
                    preview = pd.read_csv(arquivo)

                st.write("### Preview dos dados:")
                st.dataframe(preview.head())

                if st.button("Confirmar Importação de Propostas"):
                    with st.spinner("Importando dados..."):
                        sucesso, mensagem = importar_propostas(arquivo, st.session_state.db)
                        if sucesso:
                            st.success(mensagem)
                            st.rerun()
                        else:
                            st.error(mensagem)
            except Exception as e:
                st.error(f"Erro ao ler o arquivo: {str(e)}")