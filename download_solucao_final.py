"""
Script para download da solução final para problemas no Render
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

def get_markdown_file_content(md_file):
    """Lê o conteúdo de um arquivo Markdown"""
    try:
        with open(md_file, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Erro ao ler arquivo: {str(e)}"

def main():
    """Função principal"""
    # Configuração da página
    st.set_page_config(
        page_title="Solução Final para Render",
        page_icon="🔧",
        layout="wide"
    )
    
    st.title("🔧 Solução Final para Problemas no Render")
    
    st.markdown("""
    ## Solução Completa para Múltiplos Problemas
    
    Este pacote contém soluções para **todos** os problemas identificados no ambiente Render:
    
    1. ✅ **Finalização de Propostas**
    2. ✅ **Exclusão de Clientes com Propostas**
    3. ✅ **Erros de Conversão de Tipos**
    4. ✅ **Problemas com PyArrow**
    
    ### Uma solução que funciona direto no banco de dados
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if os.path.exists("instrucoes_render_final.md"):
            st.markdown(get_markdown_file_content("instrucoes_render_final.md"))
        else:
            st.error("Arquivo de instruções não encontrado!")
            
    with col2:
        st.markdown("### Download dos Arquivos")
        st.info("""
        1. Baixe o arquivo ZIP
        2. Extraia no ambiente Render
        3. Execute o script Python
        4. Todos os problemas serão corrigidos automaticamente
        """)
        
        if os.path.exists("fix_render_all.zip"):
            st.markdown(
                get_binary_file_downloader_html("fix_render_all.zip", "📥 Baixar Solução Completa (ZIP)"),
                unsafe_allow_html=True
            )
            st.success("Arquivo pronto para download!")
        else:
            st.error("Arquivo ZIP não encontrado!")
            
        st.markdown("---")
        
        if os.path.exists("fix_render_type_errors.py"):
            with st.expander("Ver código do script"):
                with open("fix_render_type_errors.py", "r") as f:
                    st.code(f.read(), language="python")
        
        st.markdown("""
        ### Implantação
        
        Após baixar e extrair o arquivo:
        
        1. Faça upload no ambiente Render
        2. Execute via console Python:
        ```bash
        python3 fix_render_type_errors.py
        ```
        3. Aguarde a finalização do script
        4. Use normalmente a aplicação
        """)

if __name__ == "__main__":
    main()