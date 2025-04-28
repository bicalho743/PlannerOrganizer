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
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}">{file_label}</a>'
    return href

def main():
    """Função principal"""
    st.set_page_config(
        page_title="Download da Solução Final para o Render",
        page_icon="📦",
        layout="centered"
    )
    
    st.title("📦 Download da Solução Final para o Render")
    
    st.markdown("""
    ### Solução Completa para Problemas no Render
    
    Este arquivo ZIP contém o script corrigido `fix_render_type_errors.py` e instruções detalhadas em `solucao_render.md` 
    para resolver os problemas de finalização de propostas e exclusão de clientes no ambiente Render.
    
    #### O que esta solução corrige:
    
    * ✅ Finalização de propostas
    * ✅ Exclusão de clientes com propostas associadas
    * ✅ Consistência na relação entre tabelas
    * ✅ Normalização de dados
    
    #### Como aplicar:
    
    1. Faça o download do arquivo ZIP abaixo
    2. Faça upload dos arquivos no ambiente Render
    3. Acesse o console Shell no Render
    4. Execute o script com `python fix_render_type_errors.py`
    5. Reinicie o serviço no Render
    
    Para instruções detalhadas, consulte o arquivo `solucao_render.md` incluído no ZIP.
    """)
    
    st.markdown(f"### Download do Arquivo de Solução 👇")
    
    zip_file = 'fix_render_final.zip'
    
    if os.path.exists(zip_file):
        st.markdown(
            get_binary_file_downloader_html(zip_file, 'Download da Solução Final (ZIP)'),
            unsafe_allow_html=True
        )
        
        with open("solucao_render.md", "r") as f:
            instructions = f.read()
        
        st.markdown("---")
        st.markdown("### Instruções de Aplicação")
        st.markdown(instructions)
    else:
        st.error(f"Arquivo {zip_file} não encontrado. Gere o arquivo ZIP primeiro!")

if __name__ == "__main__":
    main()