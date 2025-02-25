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
            if st.button(f"Importar {tipo_cadastro}s"):
                with st.spinner("Importando dados..."):
                    sucesso, mensagem = importar_cadastros(arquivo, tipo_cadastro, st.session_state.db)
                    if sucesso:
                        st.success(mensagem)
                    else:
                        st.error(mensagem)

    with tab2:
        st.subheader("Importar Propostas")

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
            if st.button("Importar Propostas"):
                with st.spinner("Importando dados..."):
                    sucesso, mensagem = importar_propostas(arquivo, st.session_state.db)
                    if sucesso:
                        st.success(mensagem)
                    else:
                        st.error(mensagem)