import streamlit as st
import pandas as pd
import io
from utils.importador import gerar_template_csv, gerar_template_excel, validar_dataframe
import traceback

def interface_importacao(tipo_cadastro, db, pagina_titulo="Importação"):
    """
    Interface para importação de vários tipos de cadastros.
    
    Args:
        tipo_cadastro (str): Tipo de cadastro a importar ('Cliente', 'Fornecedor', 'Produto', etc.)
        db: Objeto de conexão com o banco de dados
        pagina_titulo (str): Título da página de importação
    
    Returns:
        bool: True se a importação foi concluída com sucesso, False caso contrário
    """
    st.subheader(f"{pagina_titulo} em Massa")
    
    # Instruções
    st.info(f"""
    ℹ️ **Como importar {tipo_cadastro}s:**
    1. Baixe o template abaixo (Excel ou CSV)
    2. Preencha os dados no arquivo
    3. Faça upload do arquivo preenchido
    4. Clique em "Importar Dados"
    """)
    
    # Download de templates
    col1, col2 = st.columns(2)
    
    with col1:
        template_csv = gerar_template_csv(tipo_cadastro)
        st.download_button(
            label=f"📥 Baixar Template CSV",
            data=template_csv,
            file_name=f"template_{tipo_cadastro.lower()}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        template_excel = gerar_template_excel(tipo_cadastro)
        st.download_button(
            label=f"📥 Baixar Template Excel",
            data=template_excel,
            file_name=f"template_{tipo_cadastro.lower()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    # Upload e importação
    st.divider()
    
    uploaded_file = st.file_uploader(f"Selecione o arquivo de {tipo_cadastro}s para importar", 
                                    type=["csv", "xlsx", "xls"], 
                                    accept_multiple_files=False)
    
    if uploaded_file is not None:
        try:
            # Detectar tipo de arquivo
            file_type = uploaded_file.name.split(".")[-1].lower()
            
            # Ler arquivo
            if file_type == "csv":
                try:
                    # Tentar vários encodings
                    try:
                        df = pd.read_csv(uploaded_file, sep=';')
                    except:
                        df = pd.read_csv(uploaded_file, sep=',')
                except Exception as e:
                    st.error(f"Erro ao ler arquivo CSV: {str(e)}")
                    return False
            else:  # Excel
                try:
                    df = pd.read_excel(uploaded_file)
                except Exception as e:
                    st.error(f"Erro ao ler arquivo Excel: {str(e)}")
                    st.error(traceback.format_exc())
                    return False
            
            # Exibir preview dos dados
            st.subheader("Preview dos dados")
            st.dataframe(df.head(5))
            
            # Botão para confirmar importação
            if st.button("Importar Dados", type="primary", use_container_width=True):
                with st.spinner(f"Importando {tipo_cadastro}s..."):
                    try:
                        # Validar dados
                        valido, mensagem = validar_dataframe(df, tipo_cadastro)
                        
                        if not valido:
                            st.error(f"Erro na validação dos dados: {mensagem}")
                            return False
                        
                        # Importar dados
                        if tipo_cadastro.lower() in ["cliente", "clientes"]:
                            from utils.importador import importar_cadastros
                            sucesso, mensagem = importar_cadastros(uploaded_file, "Cliente", db)
                        elif tipo_cadastro.lower() in ["fornecedor", "fornecedores"]:
                            from utils.importador import importar_cadastros
                            sucesso, mensagem = importar_cadastros(uploaded_file, "Fornecedor", db)
                        elif tipo_cadastro.lower() in ["assistente", "assistentes"]:
                            from utils.importador import importar_cadastros
                            sucesso, mensagem = importar_cadastros(uploaded_file, "Assistente", db)
                        elif tipo_cadastro.lower() in ["parceiro", "parceiros"]:
                            from utils.importador import importar_cadastros
                            sucesso, mensagem = importar_cadastros(uploaded_file, "Parceiro", db)
                        elif tipo_cadastro.lower() in ["proposta", "propostas"]:
                            from utils.importador import importar_propostas
                            sucesso, mensagem = importar_propostas(uploaded_file, db)
                        elif tipo_cadastro.lower() in ["produto", "produtos"]:
                            from utils.importador import importar_cadastros
                            sucesso, mensagem = importar_cadastros(uploaded_file, "Produto", db)
                        else:
                            st.error(f"Tipo de cadastro não suportado: {tipo_cadastro}")
                            return False
                        
                        # Exibir resultado
                        if sucesso:
                            st.success(mensagem)
                            return True
                        else:
                            st.error(mensagem)
                            return False
                    
                    except Exception as e:
                        st.error(f"Erro ao importar dados: {str(e)}")
                        st.error(traceback.format_exc())
                        return False
        
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {str(e)}")
            st.error(traceback.format_exc())
            return False
    
    return False