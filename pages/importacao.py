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
        file_uploader_key = f"upload_file_{tipo_cadastro.lower()}"
        arquivo = st.file_uploader(
            f"Selecione o arquivo Excel de {tipo_cadastro}s",
            type=['xlsx', 'xls'],
            help="Você pode fazer upload de arquivos Excel (.xlsx, .xls)",
            key=file_uploader_key
        )

        if arquivo:
            try:
                preview = pd.read_excel(arquivo)
                st.write("### Preview dos dados:")
                st.info("Verifique se os dados estão corretos antes de confirmar a importação:")
                st.dataframe(preview.head())

                # Mostrar colunas encontradas
                st.write("### Colunas encontradas no arquivo:")
                colunas = preview.columns.tolist()
                st.write(", ".join(colunas))

                # Botão de importação com key única
                button_key = f"confirmar_importacao_{tipo_cadastro.lower()}"
                if st.button(f"Confirmar Importação de {tipo_cadastro}s", key=button_key):
                    with st.spinner("Importando dados..."):
                        sucesso, mensagem = importar_cadastros(arquivo, tipo_cadastro, st.session_state.db)
                        if sucesso:
                            st.success(mensagem)
                            # Atualizar a lista correspondente
                            st.session_state[f'update_{tipo_cadastro.lower()}s'] = True
                            # Limpar o arquivo do estado da sessão
                            st.session_state[file_uploader_key] = None
                        else:
                            st.error(mensagem)

            except Exception as e:
                st.error(f"Erro ao processar arquivo: {str(e)}")

    with tab2:
        st.subheader("Importar Propostas")
        st.info("Funcionalidade em desenvolvimento")