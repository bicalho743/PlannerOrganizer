"""
Script para download da solução para problema de lançamentos financeiros duplicados
"""
import base64
import streamlit as st
import os

def get_binary_file_downloader_html(bin_file, file_label='File'):
    """Gera link HTML para download de arquivos binários"""
    with open(bin_file, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{os.path.basename(bin_file)}">{file_label}</a>'
    return href

def main():
    """Função principal"""
    st.set_page_config(
        page_title="Solução para Lançamentos Financeiros Duplicados",
        page_icon="💰",
        layout="centered"
    )
    
    st.title("🛠️ Solução para Lançamentos Financeiros Duplicados")
    
    st.markdown("""
    ## Problema
    
    Existem lançamentos financeiros duplicados para a mesma proposta, com formatos de descrição diferentes:
    
    - `Proposta #83` 
    - `Proposta #83 - organização - Ana Barreto`
    
    Quando uma proposta é finalizada, só deve existir **um** lançamento financeiro associado.
    
    ## Solução
    
    Esta solução implementa:
    
    1. **Detecção e remoção** de lançamentos duplicados, mantendo apenas o mais antigo
    2. **Padronização** das descrições no formato `Proposta #{id} - {nome_cliente}`
    3. **Trigger** para garantir que novos lançamentos usem o formato padronizado
    4. **Funções** para verificar existência de lançamentos por `proposta_id` em vez de descrição
    
    ## Arquivos disponíveis para download:
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Script Python")
        st.markdown("Script Python para identificar e corrigir lançamentos duplicados:")
        st.code('''
# Como usar:
# 1. Faça upload do arquivo no Render
# 2. Execute via console do Render:
#    python3 fix_duplicated_financial_entries.py
        ''')
        st.markdown(get_binary_file_downloader_html('fix_duplicated_financial_entries.py', 'Baixar Script Python'), unsafe_allow_html=True)
    
    with col2:
        st.subheader("Script SQL")
        st.markdown("Script SQL para executar diretamente no banco de dados:")
        st.code('''
# Como usar:
# 1. Execute no DBeaver ou ferramenta similar
# 2. Ou via psql no console do Render:
#    psql $DATABASE_URL -f fix_duplicated_financial_entries.sql
        ''')
        st.markdown(get_binary_file_downloader_html('fix_duplicated_financial_entries.sql', 'Baixar Script SQL'), unsafe_allow_html=True)
    
    st.markdown("""
    ## Instruções de instalação
    
    ### Opção 1: Via Python (recomendado)
    
    1. Faça upload do arquivo `fix_duplicated_financial_entries.py` para o ambiente Render
    2. Acesse o console do Render e execute:
       ```
       python3 fix_duplicated_financial_entries.py
       ```
    3. Verifique os logs para confirmar a correção dos lançamentos duplicados
    
    ### Opção 2: Via SQL direto
    
    1. Faça upload do arquivo `fix_duplicated_financial_entries.sql` para o ambiente Render
    2. Acesse o console do Render e execute:
       ```
       psql $DATABASE_URL -f fix_duplicated_financial_entries.sql
       ```
    3. Ou execute o conteúdo do arquivo via DBeaver ou outra ferramenta de acesso ao banco de dados
    
    ## Resultado esperado
    
    - Todos os lançamentos duplicados serão removidos, mantendo apenas o mais antigo
    - As descrições serão padronizadas no formato `Proposta #{id} - {nome_cliente}`
    - Novos lançamentos usarão automaticamente o formato padronizado
    - A verificação de lançamentos existentes passará a usar o `proposta_id` em vez da descrição
    """)

if __name__ == "__main__":
    main()