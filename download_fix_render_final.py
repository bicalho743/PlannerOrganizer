"""
Script simples para permitir o download do arquivo ZIP com a solução final para o Render
"""
import streamlit as st
import base64
import os

# Configuração da página
st.set_page_config(
    page_title="Download Fix Render Final",
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
    st.title("🛠️ Download da Solução Final para o Render")
    
    st.markdown("""
    ### Solução completa para o problema de finalização de propostas no Render
    
    Este pacote contém uma solução robusta para resolver os problemas de finalização de propostas 
    no ambiente Render. A solução foi desenvolvida para resolver as diferenças de comportamento entre 
    o ambiente de desenvolvimento e produção, especialmente relacionados a:
    
    1. **Problema de conversão de tipos de dados** - Erros de conversão entre strings e numéricos
    2. **Problemas de acesso a banco de dados** - Contorna os problemas de SQLAlchemy com psycopg2
    3. **Propostas não finalizadas corretamente** - Corrige dados inconsistentes no banco
    4. **Garantia de integridade** - Adiciona trigger para manter consistência de dados
    """)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info("""
        ### Conteúdo do pacote
        
        1. `utils/finalizar_proposta_fix.py` - Módulo robusto para finalização de propostas
        2. `pages/propostas.py` - Arquivo modificado para usar a nova função
        3. `solucao_render.md` - Documentação detalhada da solução
        4. `solucao_finalizar_propostas_render.md` - Instruções passo a passo
        5. `modifica_propostas.py` - Script auxiliar para modificação de arquivos
        
        ### Como usar
        
        1. Descompacte o arquivo no ambiente Render
        2. Assegure-se que o diretório `utils` existe
        3. Copie os arquivos para seus respectivos diretórios
        4. Execute `python3 fix_proposta.py` (conforme solucao_render.md)
        """)
        
    with col2:
        st.subheader("Download")
        
        # Verificar se o arquivo existe
        if os.path.exists("fix_render_final.zip"):
            st.markdown(
                get_binary_file_downloader_html("fix_render_final.zip", "📥 Baixar solução (ZIP)"),
                unsafe_allow_html=True
            )
            st.success("Arquivo pronto para download!")
        else:
            st.error("Arquivo não encontrado. Por favor, gere o arquivo primeiro.")
    
    st.markdown("---")
    
    st.markdown("""
    ### Instruções adicionais
    
    A solução aborda dois problemas principais:
    
    1. **Correção do banco de dados atual** - Corrige propostas existentes que estão em um estado inconsistente
    2. **Prevenção de problemas futuros** - Substitui a função de finalização por uma versão robusta
    
    Após aplicar esta solução, todas as propostas finalizadas terão:
    
    - Data de finalização correta
    - Lançamentos financeiros apropriados
    - Consistência entre status e dados financeiros
    """)

if __name__ == "__main__":
    main()