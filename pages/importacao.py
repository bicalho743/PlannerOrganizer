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

        # Instruções de importação
        st.write("""
        ### Instruções para importação:
        1. Primeiro, baixe o template Excel clicando no botão abaixo
        2. Preencha o arquivo seguindo as instruções:
           - Campos obrigatórios: nome, telefone, email
           - Data de aniversário deve estar no formato DD/MM/YYYY
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
        arquivo = st.file_uploader(
            f"Selecione o arquivo Excel de {tipo_cadastro}s",
            type=['xlsx', 'xls', 'csv'],
            help="Você pode fazer upload de arquivos Excel (.xlsx, .xls) ou CSV"
        )

        if arquivo:
            # Mostrar preview dos dados
            try:
                if arquivo.name.endswith(('.xlsx', '.xls')):
                    preview = pd.read_excel(arquivo)
                else:
                    preview = pd.read_csv(arquivo)

                st.write("### Preview dos dados:")
                st.dataframe(preview.head())

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