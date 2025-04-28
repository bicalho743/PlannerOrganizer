"""
Script simples para permitir o download do arquivo ZIP com a solução para o problema de finalização de propostas
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
        page_title="Download - Correção para Propostas",
        page_icon="⬇️",
        layout="centered"
    )
    
    st.title("⬇️ Download de Correção para Finalização de Propostas")
    
    st.markdown("""
    ## Instruções de uso

    1. Baixe o arquivo ZIP clicando no link abaixo
    2. Extraia o conteúdo no servidor onde a aplicação está rodando
    3. Execute o script `fix_proposta_simples.py` via terminal:
       ```
       python fix_proposta_simples.py
       ```
    4. Você verá um menu interativo para finalizar propostas específicas ou todas de uma vez
    5. Siga as instruções do menu para finalizar as propostas desejadas

    Alternativamente, você pode usar as consultas SQL do arquivo `fix_render_database_query.py` 
    diretamente no console SQL do banco de dados.
    """)
    
    st.markdown("---")
    
    st.subheader("Download do arquivo de correção")
    
    zip_file = "fix_proposta_final.zip"
    if os.path.exists(zip_file):
        st.markdown(
            get_binary_file_downloader_html(zip_file, 'Clique aqui para baixar a solução'),
            unsafe_allow_html=True
        )
        st.success(f"O arquivo {zip_file} está pronto para download!")
    else:
        st.error(f"Arquivo {zip_file} não encontrado!")
        st.info("Execute o script que cria o arquivo ZIP primeiro.")

if __name__ == "__main__":
    main()