"""
Script simples para permitir o download do arquivo ZIP com as alterações
"""
import streamlit as st
import base64
import os

def get_binary_file_downloader_html(bin_file, file_label='File'):
    """Gera link HTML para download de arquivos binários"""
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}">Download {file_label}</a>'
    return href

def main():
    """Função principal"""
    st.title("Download dos Arquivos Alterados")
    
    st.write("""
    ## Arquivos incluídos no ZIP:
    
    - **utils/database.py**: Adicionados métodos `create_perfil` e `get_perfil_by_email`
    - **pages/registrar.py**: Corrigido botão "Voltar ao login"
    - **update_schema.sql**: Script SQL para adicionar colunas usuario_id no Render
    - **populate_usuario_id.sql**: Script para popular colunas usuario_id
    - **INSTRUCOES_RENDER_DATABASE.md**: Instruções de atualização do banco
    """)
    
    # Verificar se o arquivo existe
    if os.path.exists('alteracoes.zip'):
        st.markdown(get_binary_file_downloader_html('alteracoes.zip', 'Arquivos Alterados (ZIP)'), unsafe_allow_html=True)
        
        st.success("Após o download, siga estas etapas:")
        st.write("""
        1. Extraia o arquivo ZIP
        2. Substitua os arquivos `utils/database.py` e `pages/registrar.py` no seu repositório local
        3. Adicione os novos arquivos (`update_schema.sql`, `populate_usuario_id.sql`, `INSTRUCOES_RENDER_DATABASE.md`) à raiz do seu projeto
        4. Execute os comandos git:
        ```
        git add utils/database.py pages/registrar.py update_schema.sql populate_usuario_id.sql INSTRUCOES_RENDER_DATABASE.md
        git commit -m "Adicionados métodos para perfis no PostgreSQL e scripts para atualização do banco"
        git push origin main
        ```
        5. Siga as instruções em `INSTRUCOES_RENDER_DATABASE.md` para atualizar o banco no Render
        """)
    else:
        st.error("Arquivo ZIP não encontrado")

if __name__ == "__main__":
    main()