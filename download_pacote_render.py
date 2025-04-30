"""
Script para download do pacote de correção para o Render
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

def main():
    """Função principal"""
    st.set_page_config(
        page_title="Pacote de Correção para o Render",
        page_icon="🛠️",
        layout="wide"
    )
    
    st.title("🛠️ Correção Finalização de Propostas no Render")
    st.subheader("Download do pacote de correções")
    
    # Verificar se o arquivo existe
    if os.path.exists('fix_proposta_render.zip'):
        # Mostrar instruções
        st.markdown("""
        ## Correção para o erro: "name 'finalizar_proposta_segura' is not defined"
        
        Este pacote contém os arquivos corrigidos para resolver o problema de finalização 
        de propostas no ambiente Render. O pacote inclui:
        
        - Correção da importação na página de propostas
        - Implementação correta da função `finalizar_proposta_segura`
        - Instruções detalhadas de instalação
        
        **Tamanho do arquivo:** {:.1f} KB
        """.format(os.path.getsize('fix_proposta_render.zip') / 1024))
        
        # Botão de download
        st.markdown("""
        ## Download
        
        Clique no botão abaixo para baixar o pacote de correção:
        """)
        st.markdown(get_binary_file_downloader_html('fix_proposta_render.zip', '📥 Download Pacote Correção'), unsafe_allow_html=True)
        
        # Instruções de instalação
        with st.expander("📝 Instruções de Instalação", expanded=True):
            st.markdown("""
            ### Como aplicar a correção no Render
            
            1. Faça o download do pacote usando o botão acima
            2. Acesse o seu serviço no Render
            3. Vá para a aba "Shell"
            4. Faça upload do arquivo ZIP
            5. Descompacte o arquivo usando o comando:
               ```
               unzip fix_proposta_render.zip
               ```
            6. Os arquivos corrigidos serão extraídos mantendo a estrutura de diretórios
            7. Reinicie o serviço no Render
            
            ### Verificação
            
            Para verificar se a correção foi aplicada com sucesso:
            
            1. Acesse a aplicação
            2. Vá para a seção de Propostas
            3. Tente finalizar uma proposta em execução
            4. A proposta deve ser finalizada sem erros
            
            Se você continuar enfrentando problemas, entre em contato para suporte adicional.
            """)
    else:
        st.error(f"Arquivo 'fix_proposta_render.zip' não encontrado. Por favor, gere o arquivo primeiro.")

if __name__ == "__main__":
    main()