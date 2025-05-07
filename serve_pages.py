import streamlit as st
import os

# Configuração da página
st.set_page_config(
    page_title="Servidor de Páginas HTML", 
    page_icon="📄",
    layout="centered"
)

# Título
st.title("Servidor de Páginas HTML")

# Lista de páginas disponíveis
files = [f for f in os.listdir('.') if f.endswith('.html')]

# Interface para selecionar um arquivo
selected_file = st.selectbox("Escolha uma página para visualizar:", files)

if selected_file:
    st.write(f"Exibindo: {selected_file}")
    
    # Ler o conteúdo do arquivo
    with open(selected_file, 'r', encoding='utf-8') as file:
        html_content = file.read()
    
    # Exibir o conteúdo do arquivo em um componente HTML
    st.components.v1.html(
        html_content,
        height=800,  # Altura em pixels
        scrolling=True  # Permitir rolagem se o conteúdo for maior que a altura
    )
    
    # Opção para baixar o arquivo
    st.download_button(
        label="Baixar Arquivo",
        data=html_content,
        file_name=selected_file,
        mime="text/html"
    )