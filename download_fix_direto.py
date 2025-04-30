"""
Script simples para permitir o download do arquivo ZIP com a solução direta para o Render
"""
import streamlit as st
import base64
import os

# Configuração da página
st.set_page_config(
    page_title="Download Fix Render Direto",
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
    st.title("🛠️ Solução Definitiva para Finalização de Propostas no Render")
    
    st.markdown("""
    ## Solução Direta para o Problema de Finalização

    Este script cria funções SQL diretamente no banco de dados que garantirão:

    1. **Correção de propostas existentes** - Todas as propostas finalizadas terão seus lançamentos financeiros
    2. **Nova função SQL** - A função `finalizar_proposta(id)` para finalizar propostas diretamente via SQL
    3. **Trigger automático** - Mantém consistência entre propostas e lançamentos financeiros
    
    ### Vantagens deste método:
    
    * **Não depende de alterações no código** - Tudo funciona no nível do banco de dados
    * **Robusto contra problemas de tipo** - Evita erros de conversão entre strings e números
    * **Não interfere em funções existentes** - É um complemento, não uma substituição
    * **Independente de ORM** - Contorna problemas com SQLAlchemy ou schema caching
    """)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info("""
        ### Como usar:
        
        1. Baixe o arquivo `fix_render_direto.zip`
        2. Descompacte no ambiente Render
        3. Execute o script Python:
           ```bash
           python3 fix_proposta_render_simple.py
           ```
        4. O script automaticamente:
           - Corrige as propostas existentes
           - Cria a função SQL `finalizar_proposta(id)`
           - Configura um trigger para manter consistência
           
        ### Para finalizar propostas diretamente:
        
        Você pode usar o console SQL do Render para finalizar uma proposta:
        ```sql
        SELECT finalizar_proposta(123);  -- onde 123 é o ID da proposta
        ```
        
        Esta solução é complementar à sua aplicação - não é necessário alterar o código Python.
        """)
        
        st.markdown("""
        ### Como funciona:
        
        1. O script cria uma função SQL que encapsula toda a lógica de finalização:
           - Atualiza o status da proposta para "Finalizada"
           - Define data_finalizacao se estiver ausente
           - Define data_proposta se estiver ausente
           - Cria lançamento financeiro se não existir
           
        2. Também cria um procedimento que corrige todas as propostas finalizadas existentes
        
        3. O trigger garante que o campo usuario_id seja sempre preenchido corretamente
        """)
        
    with col2:
        st.subheader("Download")
        
        # Verificar se o arquivo existe
        if os.path.exists("fix_render_direto.zip"):
            st.markdown(
                get_binary_file_downloader_html("fix_render_direto.zip", "📥 Baixar solução direta (ZIP)"),
                unsafe_allow_html=True
            )
            st.success("Arquivo pronto para download!")
        else:
            st.error("Arquivo não encontrado. Por favor, gere o arquivo primeiro.")
    
    st.markdown("---")
    
    with st.expander("Ver conteúdo do script"):
        if os.path.exists("fix_proposta_render_simple.py"):
            with open("fix_proposta_render_simple.py", "r") as f:
                st.code(f.read(), language="python")
        else:
            st.warning("Arquivo do script não encontrado.")

if __name__ == "__main__":
    main()