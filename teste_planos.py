import streamlit as st
import os

# Configuração da página
st.set_page_config(
    page_title="Planner Organizer - Planos", 
    page_icon="🏆",
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# Título e descrição
st.title("Planner Organizer")
st.markdown("### Escolha o plano ideal para sua organização")

# Função para carregar e exibir o iframe com a página React
def show_react_component():
    # Caminho para o arquivo HTML
    html_path = os.path.join("src", "planos.html")
    
    # Verificar se o arquivo existe
    if not os.path.exists(html_path):
        st.error(f"Arquivo HTML não encontrado: {html_path}")
        return
    
    # Ler o conteúdo do arquivo HTML
    with open(html_path, "r", encoding="utf-8") as file:
        html_content = file.read()
    
    # Exibir o componente React em um iframe
    st.components.v1.html(
        html_content,
        height=800,
        scrolling=True
    )

# Exibir o componente React
show_react_component()

# Rodapé
st.markdown("""
<div style="text-align: center; margin-top: 3rem; padding: 1rem; color: #757575; font-size: 0.9rem;">
    <p>Planner Organizer &copy; 2025 - Todos os direitos reservados</p>
    <p>
        <a href="/termos" style="color: #1E366F; text-decoration: none;">Termos de Uso</a> • 
        <a href="/privacidade" style="color: #1E366F; text-decoration: none;">Política de Privacidade</a> • 
        <a href="mailto:contato@plannerorganizer.com.br" style="color: #1E366F; text-decoration: none;">Contato</a>
    </p>
</div>
""", unsafe_allow_html=True)

# Teste gratuito
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### Não está pronto para assinar?")
st.markdown("Experimente grátis por 7 dias sem necessidade de cartão de crédito.")

if st.button("INICIAR TESTE GRATUITO", type="primary", use_container_width=False):
    st.page_link("/pages/iniciar_teste.py", label="Iniciar teste gratuito", icon="🔄")