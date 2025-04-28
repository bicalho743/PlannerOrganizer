"""
Script simples para permitir o download do arquivo ZIP com a solução final para o Render
"""
import streamlit as st
import base64
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
        page_title="Download - Correção Completa Render",
        page_icon="⬇️",
        layout="centered"
    )
    
    st.title("⬇️ Download de Correção Completa para o Render")
    
    st.markdown("""
    ## Instruções de uso

    Este pacote contém duas soluções para corrigir problemas de finalização de propostas no Render:

    ### 1. Script Python Interativo
    O arquivo `fix_proposta_render.py` é um script Python interativo que permite:
    - Verificar o status atual de propostas
    - Finalizar uma proposta específica completamente (incluindo todos os campos necessários)
    - Finalizar todas as propostas pendentes

    Para usar:
    ```
    # No terminal do Render
    python fix_proposta_render.py
    ```

    ### 2. Consultas SQL Diretas
    O arquivo `fix_render_proposta_sql.sql` contém várias consultas SQL que você pode executar diretamente no console do DBeaver:
    - Script para verificar estrutura das tabelas
    - Script para finalizar uma proposta específica
    - Script para finalizar todas as propostas
    
    Ambas as soluções garantem que:
    - O status da proposta seja atualizado para 'Finalizada'
    - A data de finalização (data_finalizacao) seja preenchida
    - A data da proposta (data_proposta) seja preenchida (usando data_inicio se necessário)
    - O lançamento financeiro correspondente seja criado
    """)
    
    st.markdown("---")
    
    st.subheader("Download do arquivo de correção completa")
    
    zip_file = "fix_render_final.zip"
    if os.path.exists(zip_file):
        st.markdown(
            get_binary_file_downloader_html(zip_file, 'Clique aqui para baixar a solução completa'),
            unsafe_allow_html=True
        )
        st.success(f"O arquivo {zip_file} está pronto para download!")
    else:
        st.error(f"Arquivo {zip_file} não encontrado!")
        st.info("Execute o script que cria o arquivo ZIP primeiro.")

if __name__ == "__main__":
    main()