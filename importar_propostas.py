import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import os

# Configuração da página
try:
    st.set_page_config(
        page_title="Importar Propostas",
        page_icon="📊",
        layout="wide"
    )
except:
    pass

st.title("📊 Importar Propostas")
st.write("Esta ferramenta permite importar propostas de um arquivo CSV ou Excel.")

# Inicializar banco de dados
@st.cache_resource
def get_database():
    try:
        from utils.database import Database
        return Database()
    except Exception as e:
        st.error(f"Erro ao conectar com o banco: {str(e)}")
        return None

def importar_propostas_arquivo(arquivo):
    """Importa propostas de um arquivo"""
    try:
        # Ler arquivo
        if arquivo.name.endswith('.csv'):
            df = pd.read_csv(arquivo, encoding='utf-8')
        elif arquivo.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(arquivo)
        else:
            st.error("Formato de arquivo não suportado. Use CSV ou Excel.")
            return False
        
        # Validar colunas obrigatórias
        colunas_obrigatorias = ['cliente_nome', 'descricao', 'valor']
        colunas_faltando = [col for col in colunas_obrigatorias if col not in df.columns]
        
        if colunas_faltando:
            st.error(f"Colunas obrigatórias faltando: {', '.join(colunas_faltando)}")
            return False
        
        # Processar dados
        db = get_database()
        if db is None:
            return False
        
        sucesso = 0
        erros = 0
        
        for index, row in df.iterrows():
            try:
                # Preparar dados da proposta
                proposta_data = {
                    'numero': f"PROP-{datetime.now().strftime('%Y%m%d')}-{index+1:03d}",
                    'cliente_nome': str(row['cliente_nome']).strip(),
                    'descricao': str(row['descricao']).strip(),
                    'valor': float(row['valor']) if pd.notna(row['valor']) else 0.0,
                    'status': row.get('status', 'Aberta'),
                    'tipo_proposta': row.get('tipo_proposta', 'Organização'),
                    'data_criacao': datetime.now(),
                    'data_inicio': pd.to_datetime(row['data_inicio']) if 'data_inicio' in row and pd.notna(row['data_inicio']) else None,
                    'data_fim': pd.to_datetime(row['data_fim']) if 'data_fim' in row and pd.notna(row['data_fim']) else None
                }
                
                # Inserir no banco
                db.add_proposta(**proposta_data)
                sucesso += 1
                
            except Exception as e:
                st.warning(f"Erro na linha {index + 1}: {str(e)}")
                erros += 1
        
        st.success(f"Importação concluída: {sucesso} propostas importadas, {erros} erros.")
        return True
        
    except Exception as e:
        st.error(f"Erro durante importação: {str(e)}")
        return False

# Interface de upload
uploaded_file = st.file_uploader(
    "Escolha um arquivo para importar",
    type=['csv', 'xlsx', 'xls'],
    help="Colunas obrigatórias: cliente_nome, descricao, valor"
)

if uploaded_file is not None:
    st.write(f"Arquivo selecionado: {uploaded_file.name}")
    
    # Mostrar prévia do arquivo
    if st.checkbox("Mostrar prévia dos dados"):
        try:
            if uploaded_file.name.endswith('.csv'):
                preview_df = pd.read_csv(uploaded_file, nrows=5, encoding='utf-8')
            else:
                preview_df = pd.read_excel(uploaded_file, nrows=5)
            
            st.write("Prévia dos dados:")
            st.dataframe(preview_df)
            
            # Reset file pointer
            uploaded_file.seek(0)
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {str(e)}")
    
    # Botão de importação
    if st.button("Importar Propostas", type="primary"):
        with st.spinner("Importando dados..."):
            if importar_propostas_arquivo(uploaded_file):
                st.balloons()

# Instruções
with st.expander("📋 Instruções de Uso"):
    st.markdown("""
    **Formato do arquivo:**
    - Aceita arquivos CSV e Excel (.xlsx, .xls)
    - Encoding UTF-8 para arquivos CSV
    
    **Colunas obrigatórias:**
    - `cliente_nome`: Nome do cliente
    - `descricao`: Descrição da proposta
    - `valor`: Valor da proposta (numérico)
    
    **Colunas opcionais:**
    - `status`: Status da proposta (padrão: "Aberta")
    - `tipo_proposta`: Tipo da proposta (padrão: "Organização")
    - `data_inicio`: Data de início (formato: YYYY-MM-DD)
    - `data_fim`: Data de fim (formato: YYYY-MM-DD)
    """)