"""
Script simples para permitir o download do arquivo ZIP com a solução para desativar lançamentos automáticos
"""
import base64
import streamlit as st
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
        page_title="Remover Lançamentos Automáticos",
        page_icon="📋",
        layout="centered"
    )
    
    st.title("🛠️ Desativar Todos os Lançamentos Financeiros Automáticos")
    
    st.write("""
    ## Solução Completa
    
    Esta solução irá **remover todos os lançamentos financeiros automáticos** relacionados a propostas
    e **impedir que novos lançamentos sejam criados** nas operações de aprovação e finalização de propostas.
    
    ### O que esta solução faz:
    
    1. **Remove lançamentos existentes**:
       - Exclui todos os lançamentos financeiros vinculados a uma proposta
       - Exclui lançamentos com descrição contendo "Proposta #"
    
    2. **Impede novos lançamentos**:
       - Cria trigger SQL para bloquear inserções automáticas
       - Modifica o código para desativar a função de criação de lançamentos
       - Cria uma função que sempre informa que já existe lançamento
    
    ### Como usar:
    
    **Opção 1 (Recomendada)**: Execute o script Python que faz tudo automaticamente
    ```
    python3 limpar_lancamentos_automaticos.py
    ```
    
    **Opção 2**: Execute apenas o script SQL para remover lançamentos e criar bloqueios
    ```
    psql $DATABASE_URL -f desativar_lancamentos_automaticos.sql
    ```
    
    ## Download da Solução
    """)
    
    st.markdown(get_binary_file_downloader_html('remover_lancamentos_automaticos.zip', 'Baixar Pacote Completo (ZIP)'), unsafe_allow_html=True)
    
    st.warning("""
    ⚠️ **ATENÇÃO**: Esta solução irá remover TODOS os lançamentos financeiros vinculados a propostas.
    Os lançamentos não poderão ser recuperados após a execução desta solução.
    
    Recomendamos fazer um backup do banco de dados antes de executar se não tiver certeza.
    """)

if __name__ == "__main__":
    main()