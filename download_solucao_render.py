"""
Script para download da solução para problemas no Render
"""
import streamlit as st
import base64
import os

def get_binary_file_downloader_html(bin_file, file_label='File'):
    """Gera link HTML para download de arquivos binários"""
    with open(bin_file, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{os.path.basename(bin_file)}" style="display:inline-block;padding:0.5rem 1rem;background-color:#2d8cff;color:white;text-decoration:none;border-radius:5px;font-weight:bold;">{file_label}</a>'
    return href

def get_markdown_file_content(md_file):
    """Lê o conteúdo de um arquivo Markdown"""
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Erro ao ler arquivo {md_file}: {str(e)}"

def main():
    """Função principal"""
    st.set_page_config(
        page_title="Solução para Problemas no Render",
        page_icon="🛠️",
        layout="wide"
    )
    
    st.title("🛠️ Solução Completa para Problemas no Render")
    st.subheader("Download do pacote de correções")
    
    # Verificar se o arquivo existe
    if os.path.exists('fix_render_final.zip'):
        # Mostrar instruções
        st.markdown("""
        ## Pacote de Solução 
        
        Este pacote contém todas as correções necessárias para resolver os problemas de:
        
        - Finalização de propostas
        - Exclusão de clientes
        - Lançamentos financeiros automáticos
        - Inconsistências de tipos de dados
        
        **Instruções de instalação estão incluídas no arquivo zip.**
        
        **Tamanho do arquivo:** {:.1f} KB
        """.format(os.path.getsize('fix_render_final.zip') / 1024))
        
        # Mostrar documentação
        if os.path.exists('solucao_render.md'):
            with st.expander("📑 Ver Documentação", expanded=False):
                st.markdown(get_markdown_file_content('solucao_render.md'))
        
        # Botão de download
        st.markdown("""
        ## Download
        
        Clique no botão abaixo para baixar o pacote de solução:
        """)
        st.markdown(get_binary_file_downloader_html('fix_render_final.zip', '📥 Download Solução para Render'), unsafe_allow_html=True)
        
        # Instruções pós-download
        st.markdown("""
        ## Próximos passos após o download
        
        1. Faça login no Render
        2. Navegue até seu serviço web
        3. Vá para a aba "Shell"
        4. Faça upload do arquivo zip baixado
        5. Siga as instruções no arquivo INSTRUCOES_RENDER.md dentro do zip
        """)
    else:
        st.error(f"Arquivo 'fix_render_final.zip' não encontrado. Por favor, gere o arquivo primeiro.")

if __name__ == "__main__":
    main()