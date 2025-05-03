"""
Script simples para download da solução para lançamentos duplicados
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
        page_title="Solução para Lançamentos Duplicados",
        page_icon="📋",
        layout="centered"
    )
    
    st.title("🛠️ Correção de Lançamentos Duplicados em Propostas")
    
    st.write("""
    ## Problema
    
    Quando uma proposta é aprovada e depois finalizada, estão sendo criados dois lançamentos financeiros:
    
    - Um na **aprovação** da proposta (correto)
    - Outro na **finalização** da proposta (incorreto, duplicado)
    
    O comportamento esperado é criar o lançamento financeiro **apenas uma vez**, na aprovação da proposta.
    
    ## Solução
    
    Os arquivos abaixo oferecem uma solução completa para:
    
    1. Remover lançamentos duplicados existentes
    2. Padronizar as descrições dos lançamentos
    3. Modificar o comportamento para não criar novos lançamentos duplicados
    
    ## Download da Solução
    """)
    
    st.markdown(get_binary_file_downloader_html('proposta_fix.zip', 'Baixar Pacote de Correção (ZIP)'), unsafe_allow_html=True)
    
    st.write("""
    ## Instruções de Instalação
    
    1. Descompacte o arquivo ZIP no ambiente Render
    2. Execute o script SQL para corrigir os lançamentos existentes:
       ```
       psql $DATABASE_URL -f fix_proposta_finalizacao.sql
       ```
    3. Execute o script Python para configurar a prevenção de duplicações:
       ```
       python3 fix_duplicate_proposal_entries.py
       ```
    
    ## Modificação Necessária no Código
    
    Para garantir que os lançamentos não sejam duplicados, adicione esta verificação na função de finalização de proposta:
    
    ```python
    # Verificar se já existe lançamento para esta proposta
    cursor.execute("SELECT ja_existe_lancamento_proposta(%s)", (proposta_id,))
    ja_existe = cursor.fetchone()[0]
    
    # Criar lançamento financeiro apenas se não existir
    if not ja_existe:
        adicionar_lancamento_financeiro(...)
    ```
    """)

if __name__ == "__main__":
    main()