"""
Script para download da solução final para problemas no Render
"""
import streamlit as st
import base64
import os

def get_binary_file_downloader_html(bin_file, file_label='Arquivo'):
    """Gera link HTML para download de arquivos binários"""
    with open(bin_file, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{os.path.basename(bin_file)}" class="download-button">{file_label}</a>'
    return href

def main():
    """Função principal"""
    st.set_page_config(
        page_title="Solução para o Render",
        page_icon="🔧",
        layout="centered"
    )
    
    # Estilos CSS personalizados
    st.markdown("""
    <style>
    .title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
    
    .subtitle {
        font-size: 1.5rem;
        font-weight: 500;
        color: #34495e;
        margin-bottom: 2rem;
    }
    
    .download-section {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        margin-top: 2rem;
        border: 1px solid #dee2e6;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    
    .download-button {
        display: inline-block;
        background-color: #2c3e50;
        color: white;
        font-weight: 500;
        padding: 0.75rem 1.5rem;
        border-radius: 5px;
        text-decoration: none;
        margin-top: 1rem;
        transition: all 0.3s ease;
    }
    
    .download-button:hover {
        background-color: #1a252f;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    
    .info-box {
        background-color: #e9f7fe;
        border-left: 4px solid #3498db;
        padding: 1rem;
        margin: 1.5rem 0;
        border-radius: 0 5px 5px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Título e introdução
    st.markdown('<h1 class="title">🔧 Solução Final para Problemas no Render</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Pacote completo com correções para finalização de propostas e exclusão de clientes</p>', unsafe_allow_html=True)
    
    # Verificar se o arquivo MD existe e exibir
    if os.path.exists('solucao_render.md'):
        # Obter o conteúdo do arquivo
        with open('solucao_render.md', 'r', encoding='utf-8') as f:
            md_content = f.read()
        st.markdown(md_content)
    else:
        st.warning("Arquivo de documentação (solucao_render.md) não encontrado.")
    
    # Seção de download
    st.markdown('<div class="download-section">', unsafe_allow_html=True)
    st.subheader("📦 Download do Pacote de Solução")
    
    # Verificar se o arquivo ZIP existe
    zip_file = 'fix_render_final.zip'
    if os.path.exists(zip_file):
        st.success(f"Pacote pronto para download: {zip_file}")
        file_size = os.path.getsize(zip_file) / 1024  # tamanho em KB
        st.info(f"Tamanho do arquivo: {file_size:.1f} KB")
        
        st.markdown("""
        <div class="info-box">
        <strong>Instruções:</strong>
        <ol>
            <li>Faça o download do pacote abaixo</li>
            <li>Descompacte o arquivo no diretório principal da aplicação no Render</li>
            <li>Reinicie o serviço no Render</li>
        </ol>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(get_binary_file_downloader_html(zip_file, '📥 Download Solução para o Render'), unsafe_allow_html=True)
    else:
        st.error(f"Arquivo {zip_file} não encontrado. Por favor, verifique se o arquivo está presente no diretório.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Instruções de deploy
    if os.path.exists('INSTRUCOES_DEPLOY_RENDER.md'):
        st.markdown("## Instruções de Deploy")
        with open('INSTRUCOES_DEPLOY_RENDER.md', 'r', encoding='utf-8') as f:
            instrucoes = f.read()
            # Exibir apenas uma parte resumida das instruções
            linhas = instrucoes.split('\n')
            resumo = '\n'.join(linhas[:20]) + "\n\n..."
            
            st.markdown(resumo)
            
            with st.expander("Ver instruções completas"):
                st.markdown(instrucoes)
    
    # Informações adicionais
    st.markdown("""
    ### ❓ Suporte Técnico
    
    Se precisar de suporte adicional:
    
    1. Execute o script `render_startup.py` manualmente e verifique o arquivo de log gerado
    2. Consulte as funções SQL adicionadas ao banco de dados usando a consola SQL
    3. Verifique se as modificações foram aplicadas no arquivo `pages/propostas.py`
    
    Todas as correções são aplicadas automaticamente durante a inicialização.
    """)

if __name__ == "__main__":
    main()