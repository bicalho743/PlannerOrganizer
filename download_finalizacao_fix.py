"""
Script simples para permitir o download do arquivo ZIP com a solução para lançamentos duplicados
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
        page_title="Solução para Lançamentos na Finalização",
        page_icon="📋",
        layout="centered"
    )
    
    st.title("🛠️ Remover Lançamento de Receita na Finalização")
    
    st.write("""
    ## Problema
    
    Atualmente, quando uma proposta é finalizada, o sistema está criando um lançamento financeiro duplicado.
    Isso ocorre porque:
    
    1. Um lançamento é criado na **aprovação** da proposta (correto)
    2. Outro lançamento é criado na **finalização** da proposta (incorreto)
    
    ## Solução
    
    Esta solução foca especificamente em:
    
    1. Criar função SQL para verificar se já existe um lançamento para a proposta
    2. Modificar a função de finalização para não criar um lançamento duplicado
    
    ## Download da Solução
    """)
    
    st.markdown(get_binary_file_downloader_html('finalizacao_fix.zip', 'Baixar Correção Finalização (ZIP)'), unsafe_allow_html=True)
    
    st.write("""
    ## Arquivos na Solução
    
    1. **remove_finalizacao_lancamento.py** - Script Python que:
       - Cria função SQL para verificar se já existe lançamento
       - Localiza a função de finalização de proposta
       - Modifica o código para adicionar uma verificação
    
    2. **remover_lancamento_finalizacao.sql** - Script SQL que:
       - Cria função para verificar se já existe lançamento para uma proposta
       - Inclui exemplo de como modificar o código Python
    
    ## Instruções de Instalação
    
    ### Opção 1: Instalar via SQL (mais simples)
    
    1. Execute o script SQL para criar a função de verificação:
       ```
       psql $DATABASE_URL -f remover_lancamento_finalizacao.sql
       ```
    
    2. Localize o arquivo que contém a função `finalizar_proposta` ou `finalizar_proposta_segura`
    
    3. Modifique a função conforme o exemplo no arquivo SQL
    
    ### Opção 2: Executar Script Python (automático)
    
    1. Execute o script Python que fará todas as modificações:
       ```
       python3 remove_finalizacao_lancamento.py
       ```
    
    2. Este script tentará identificar e modificar automaticamente o arquivo correto
    """)
    
    st.info("""
    Importante: Esta solução não remove lançamentos duplicados existentes, apenas previne a criação 
    de novos lançamentos duplicados durante a finalização. Para remover lançamentos duplicados existentes, 
    seria necessária uma solução diferente que analise e limpe o banco de dados.
    """)

if __name__ == "__main__":
    main()