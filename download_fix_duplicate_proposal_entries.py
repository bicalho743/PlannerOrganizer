"""
Script para download da solução para problema de lançamentos financeiros duplicados em propostas
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
        page_title="Correção de Lançamentos Duplicados em Propostas",
        page_icon="💼",
        layout="centered"
    )
    
    st.title("🛠️ Correção de Lançamentos Duplicados em Propostas")
    
    st.markdown("""
    ## Problema
    
    Atualmente, estão sendo criados dois lançamentos financeiros para a mesma proposta:
    
    1. Um na **aprovação** da proposta
    2. Outro na **finalização** da proposta
    
    O comportamento correto é criar o lançamento financeiro **apenas na aprovação** da proposta.
    
    ## Solução
    
    Esta solução:
    
    1. Remove lançamentos duplicados, mantendo apenas o mais antigo
    2. Padroniza as descrições dos lançamentos no formato "Proposta #{id} - {nome_cliente}"
    3. Adiciona validação para não criar novos lançamentos se já existir um para a proposta
    4. Implementa triggers SQL para padronizar automaticamente novas descrições
    
    ## Arquivos disponíveis para download:
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Script Python")
        st.markdown("Script Python para identificar e corrigir lançamentos duplicados.")
        st.code('''
# Como usar:
# 1. Faça upload do arquivo no Render
# 2. Execute no terminal:
#    python3 fix_duplicate_proposal_entries.py
        ''')
        st.markdown(get_binary_file_downloader_html('fix_duplicate_proposal_entries.py', 'Baixar Script Python'), unsafe_allow_html=True)
    
    with col2:
        st.subheader("Script SQL")
        st.markdown("Script SQL para executar diretamente no banco de dados.")
        st.code('''
# Como usar:
# 1. Execute no console do Render:
#    psql $DATABASE_URL -f fix_proposta_finalizacao.sql
        ''')
        st.markdown(get_binary_file_downloader_html('fix_proposta_finalizacao.sql', 'Baixar Script SQL'), unsafe_allow_html=True)
    
    st.markdown("""
    ## Alterações necessárias no código
    
    Além de executar os scripts acima, você precisa modificar as funções de finalização de proposta no seu código:
    
    ```python
    def finalizar_proposta(proposta_id, usuario_id=None):
        # Código existente para atualizar status da proposta
        ...
        
        # ADICIONAR ESTA VERIFICAÇÃO:
        # Verificar se já existe lançamento para esta proposta
        cursor.execute("SELECT ja_existe_lancamento_proposta(%s)", (proposta_id,))
        ja_existe = cursor.fetchone()[0]
        
        if not ja_existe:
            # Criar lançamento financeiro apenas se não existir
            adicionar_lancamento_financeiro(...)
        else:
            logger.info(f"Proposta #{proposta_id} já possui lançamento financeiro, não será criado outro")
    ```
    
    Este código evita a criação de lançamentos duplicados, garantindo que o lançamento seja feito apenas na aprovação da proposta.
    
    ## Após a instalação
    
    Depois de aplicar as correções, os seguintes comportamentos serão observados:
    
    1. Todos os lançamentos duplicados serão removidos
    2. Todas as descrições serão padronizadas
    3. Novos lançamentos não serão criados para propostas que já possuem um
    4. Novas descrições de lançamentos serão automaticamente padronizadas
    """)

if __name__ == "__main__":
    main()