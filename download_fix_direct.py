"""
Script simples para permitir o download do arquivo ZIP com a solução direta para o erro
finalizar_proposta_seguro/finalizar_proposta_segura no Render
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
        page_title="Download da Solução para finalizar_proposta_seguro",
        page_icon="🛠️",
        layout="centered"
    )
    
    st.title("🛠️ Solução para Erro finalizar_proposta_seguro")
    
    st.markdown("""
    ### Correção para o erro: `name 'finalizar_proposta_segura' is not defined`
    
    Este arquivo ZIP contém a solução completa para o erro de função não definida no ambiente Render.
    O problema ocorre porque há uma referência à função `finalizar_proposta_seguro` que não existe no módulo.
    
    #### O que esta solução contém:
    
    * **finalizar_proposta_fix.py** - Arquivo corrigido com a função `finalizar_proposta_seguro` implementada
    * **fix_proposta_simple.py** - Script para corrigir o banco de dados (criar funções SQL)
    * **solucao_render.md** - Instruções detalhadas de aplicação
    
    #### Como aplicar no Render:
    
    1. Faça o download do arquivo ZIP abaixo
    2. Extraia os arquivos
    3. Faça upload do arquivo `finalizar_proposta_fix.py` para a pasta `utils/` no Render
    4. Execute o script `fix_proposta_simple.py` no console do Render para criar as funções SQL
    5. Reinicie o serviço no Render
    
    Alternativamente, você pode copiar o conteúdo do arquivo SQL e executá-lo diretamente no console do banco de dados
    do Render ou via DBeaver.
    """)
    
    st.markdown(f"### Download do Arquivo de Solução 👇")
    
    zip_file = 'fix_render_direct.zip'
    
    if os.path.exists(zip_file):
        st.markdown(
            get_binary_file_downloader_html(zip_file, 'Download da Solução para finalizar_proposta_seguro (ZIP)'),
            unsafe_allow_html=True
        )
    else:
        st.error(f"Arquivo {zip_file} não encontrado. Gere o arquivo ZIP primeiro!")

if __name__ == "__main__":
    main()