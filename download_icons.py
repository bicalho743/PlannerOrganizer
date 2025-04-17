import streamlit as st
import base64
import os

def get_base64_encoded_image(image_path):
    """Codifica uma imagem para base64"""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

def download_button(file_path, button_text, file_name):
    """Cria um botão de download para um arquivo"""
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    
    st.download_button(
        label=button_text,
        data=file_bytes,
        file_name=file_name,
        use_container_width=True
    )

def main():
    st.set_page_config(
        page_title="Download de Ícones",
        page_icon="favicon.png",
        layout="wide"
    )
    
    st.title("Download de Ícones - Planner Organizer")
    
    st.markdown("""
    ## Ícones do Sistema
    
    Aqui você pode visualizar e baixar os ícones do sistema em diferentes formatos.
    Estes ícones foram criados especialmente para o Planner Organizer e podem ser usados
    em diferentes contextos, como site, aplicativo, documentação, etc.
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### SVG (Vetorial)")
        try:
            svg_code = open("app-icon.svg", "r").read()
            st.markdown(f"""
            <div style="border: 1px solid #ddd; border-radius: 5px; padding: 20px; text-align: center;">
                {svg_code}
            </div>
            """, unsafe_allow_html=True)
            download_button("app-icon.svg", "📥 Baixar SVG", "planner-icon.svg")
        except Exception as e:
            st.error(f"Erro ao carregar SVG: {e}")
    
    with col2:
        st.markdown("### PNG 512x512")
        try:
            encoded_image = get_base64_encoded_image("generated-icon.png")
            st.markdown(f"""
            <div style="border: 1px solid #ddd; border-radius: 5px; padding: 20px; text-align: center;">
                <img src="data:image/png;base64,{encoded_image}" width="256" height="256">
            </div>
            """, unsafe_allow_html=True)
            download_button("generated-icon.png", "📥 Baixar PNG 512x512", "planner-icon-512.png")
        except Exception as e:
            st.error(f"Erro ao carregar PNG 512x512: {e}")
    
    with col3:
        st.markdown("### PNG 192x192")
        try:
            encoded_image = get_base64_encoded_image("app-icon-192.png")
            st.markdown(f"""
            <div style="border: 1px solid #ddd; border-radius: 5px; padding: 20px; text-align: center;">
                <img src="data:image/png;base64,{encoded_image}" width="192" height="192">
            </div>
            """, unsafe_allow_html=True)
            download_button("app-icon-192.png", "📥 Baixar PNG 192x192", "planner-icon-192.png")
        except Exception as e:
            st.error(f"Erro ao carregar PNG 192x192: {e}")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Favicon 64x64")
        try:
            encoded_image = get_base64_encoded_image("favicon.png")
            st.markdown(f"""
            <div style="border: 1px solid #ddd; border-radius: 5px; padding: 20px; text-align: center;">
                <img src="data:image/png;base64,{encoded_image}" width="64" height="64">
            </div>
            """, unsafe_allow_html=True)
            download_button("favicon.png", "📥 Baixar Favicon", "favicon.png")
        except Exception as e:
            st.error(f"Erro ao carregar Favicon: {e}")
    
    with col2:
        st.markdown("### Como usar os ícones")
        st.info("""
        - **SVG**: Formato vetorial ideal para sites responsivos e documentos
        - **PNG 512x512**: Ideal para ícones de aplicativos e thumbnails de alta resolução
        - **PNG 192x192**: Bom para ícones de aplicativos móveis e web
        - **Favicon 64x64**: Perfeito para favicon de sites
        
        O ícone já está configurado no sistema Planner Organizer e aparece na aba do navegador.
        """)
    
    # Botão para voltar ao sistema principal
    if st.button("↩️ Voltar para o sistema", use_container_width=True):
        st.stop() # Só fecha esta página

if __name__ == "__main__":
    main()