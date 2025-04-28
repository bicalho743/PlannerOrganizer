"""
Script simples para permitir o download do arquivo ZIP com as correções para o Render
"""
import base64
import os
import streamlit as st

def get_binary_file_downloader_html(bin_file, file_label='File'):
    """Gera link HTML para download de arquivos binários"""
    with open(bin_file, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:application/zip;base64,{b64}" download="{bin_file}">Download {file_label}</a>'
    return href

def main():
    """Função principal"""
    st.title("Download de Arquivos para Correção do Render")
    
    st.markdown("""
    ## Arquivos para Resolver Problemas no Render
    
    Este utilitário permite baixar os arquivos necessários para corrigir o problema de erro 
    `column clientes.usuario_id does not exist` no Render.
    
    O arquivo ZIP contém:
    - `utils/database.py` (modificado para desabilitar cache)
    - `correcao_banco.py` (script de diagnóstico e correção)
    - `render_no_cache.py` (script de inicialização para o Render)
    
    ### Como usar:
    1. Baixe o arquivo ZIP
    2. Extraia os arquivos
    3. Siga as instruções em INSTRUCOES_DEPLOY_RENDER.md
    """)
    
    # Verificar se o arquivo ZIP existe
    zip_file = 'fix_render_db.zip'
    if os.path.exists(zip_file):
        st.markdown(get_binary_file_downloader_html(zip_file, 'Arquivos de Correção'), unsafe_allow_html=True)
    else:
        st.error(f"Arquivo {zip_file} não encontrado!")
    
    # Mostrar instruções
    with open('INSTRUCOES_DEPLOY_RENDER.md', 'r') as f:
        instructions = f.read()
    
    st.markdown("---")
    st.markdown(instructions)

if __name__ == "__main__":
    main()