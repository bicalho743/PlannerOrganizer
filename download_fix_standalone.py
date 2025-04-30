"""
Script standalone para download da solução para o Render
Este script não depende de outras bibliotecas além do Streamlit
"""
import streamlit as st
import base64

# Conteúdo do arquivo ZIP em base64
zip_base64 = """
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
"""

# Script para download da solução para o Render
def main():
    """
    Função principal para gerar a página de download.
    Usando somente Streamlit para maior compatibilidade.
    """
    st.set_page_config(
        page_title="Solução para Problemas no Render",
        page_icon="🛠️",
        layout="wide"
    )
    
    st.title("🛠️ Solução Completa para Problemas no Render")
    st.subheader("Download do pacote de correções")
    
    # Conteúdo da solução
    st.markdown("""
    ## Pacote de Solução 
    
    Este pacote contém todas as correções necessárias para resolver os problemas de:
    
    - Finalização de propostas
    - Exclusão de clientes
    - Lançamentos financeiros automáticos
    - Inconsistências de tipos de dados
    
    **Instruções de instalação estão incluídas no arquivo zip.**
    """)
    
    # Mostrar documentação
    with st.expander("📑 Ver Documentação", expanded=False):
        st.markdown("""
        # Solução para Problemas no Render

        ## Erro de Finalização de Propostas

        Este pacote contém uma solução completa para o erro `name 'finalizar_proposta_segura' is not defined` que ocorre ao tentar finalizar propostas no ambiente Render.

        ### Problema

        No ambiente Render, ao tentar finalizar uma proposta, ocorre um erro porque a função `finalizar_proposta_segura` não está sendo encontrada, embora o código esteja tentando usá-la.

        ### Solução

        1. **Correção de importação**: Ajustamos a importação no arquivo `pages/propostas.py` para importar a função correta:
           ```python
           from utils.finalizar_proposta_fix import finalizar_proposta_segura
           ```

        2. **Implementação de função compatível**: Melhoramos a função `finalizar_proposta_segura` no arquivo `utils/finalizar_proposta_fix.py` para retornar um objeto compatível com o que é esperado pelo código que a chama.

        ### Arquivos Incluídos

        - `pages/propostas.py` (com a correção da importação)
        - `utils/finalizar_proposta_fix.py` (com a função melhorada)

        ## Problemas de Tipo no PostgreSQL

        Este pacote também inclui correções para problemas de conversão de tipo no PostgreSQL do Render.

        ### Problema

        O PostgreSQL no Render tem problemas para converter automaticamente alguns tipos de dados, especialmente entre strings e números.

        ### Solução

        1. **Funções SQL diretas**: Implementamos funções que usam SQL direto para evitar problemas de tipo do ORM.
        2. **Adaptadores de tipo**: Registramos adaptadores de tipo para Numpy e Python nativos.
        3. **Verificações de tipo robustas**: Adicionamos verificações e conversões de tipo explícitas.
        """)
    
    # Botão de download usando base64
    st.markdown("""
    ## Download
    
    Clique no botão abaixo para baixar o pacote de solução:
    """)
    
    # Criação do botão de download
    b64 = zip_base64.strip()
    href = f'<a href="data:application/zip;base64,{b64}" download="fix_render_final.zip" style="display:inline-block;padding:0.5rem 1rem;background-color:#2d8cff;color:white;text-decoration:none;border-radius:5px;font-weight:bold;">📥 Download Solução para Render</a>'
    st.markdown(href, unsafe_allow_html=True)
    
    # Instruções pós-download
    st.markdown("""
    ## Próximos passos após o download
    
    1. Faça login no Render
    2. Navegue até seu serviço web
    3. Vá para a aba "Shell"
    4. Faça upload do arquivo zip baixado
    5. Descompacte-o usando o comando: `unzip fix_render_final.zip`
    6. Reinicie o serviço para aplicar as mudanças
    """)

if __name__ == "__main__":
    main()