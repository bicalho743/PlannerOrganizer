"""
Script simples para permitir o download do arquivo com a correção para o Render
"""
import streamlit as st
import base64
import os

# Configuração da página
st.set_page_config(
    page_title="Download Fix Render Console",
    page_icon="🛠️",
    layout="wide"
)

def get_binary_file_downloader_html(bin_file, file_label='File'):
    """Gera link HTML para download de arquivos binários"""
    with open(bin_file, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{os.path.basename(bin_file)}">{file_label}</a>'
    return href

def main():
    """Função principal"""
    st.title("🛠️ Download da Solução para Propostas no Render")
    
    st.markdown("""
    ### Ferramenta para corrigir problemas no banco de dados do Render
    
    Este script resolve os seguintes problemas:
    
    1. **Atualiza propostas finalizadas** adicionando data_finalizacao quando ausente
    2. **Atualiza propostas finalizadas** adicionando data_proposta quando ausente
    3. **Cria lançamentos financeiros** para propostas finalizadas que não os têm
    4. **Cria um trigger SQL** para manter a consistência entre propostas e lançamentos
    
    #### Como utilizar:
    
    1. Baixe o arquivo zip
    2. Descompacte no ambiente Render
    3. Execute com `python3 fix_proposta_render_console.py`
    4. Veja os resultados no console
    """)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info("Este script foi desenvolvido especificamente para o ambiente Render e funciona diretamente no console, sem depender de interface gráfica.")
        
        st.markdown("""
        #### Conteúdo do pacote:
        
        - `fix_proposta_render_console.py` - Script Python para corrigir as propostas
        
        O script detecta automaticamente a estrutura do banco de dados e se adapta a ela,
        funcionando mesmo que a estrutura seja diferente entre desenvolvimento e produção.
        """)
    
    with col2:
        st.subheader("Download")
        
        # Verificar se o arquivo existe
        if os.path.exists("fix_render_console.zip"):
            st.markdown(
                get_binary_file_downloader_html("fix_render_console.zip", "📥 Baixar solução (ZIP)"),
                unsafe_allow_html=True
            )
            st.success("Arquivo pronto para download!")
        else:
            st.error("Arquivo não encontrado. Por favor, gere o arquivo primeiro.")
    
    # Mostrar conteúdo do script
    with st.expander("Ver conteúdo do script Python"):
        if os.path.exists("fix_proposta_render_console.py"):
            with open("fix_proposta_render_console.py", "r") as f:
                st.code(f.read(), language="python")
        else:
            st.warning("Arquivo do script não encontrado.")
    
    st.markdown("---")
    st.markdown("""
    ### Instruções para o Render
    
    1. Acesse o console do seu projeto no Render
    2. Faça upload do arquivo ZIP
    3. Descompacte com `unzip fix_render_console.zip`
    4. Execute o script com `python3 fix_proposta_render_console.py`
    5. Verifique se as propostas foram corrigidas
    """)

if __name__ == "__main__":
    main()