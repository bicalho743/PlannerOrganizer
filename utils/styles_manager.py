
"""
Gerenciador centralizado de estilos para o Planner Organizer
"""
import streamlit as st

class StylesManager:
    """Classe para gerenciar todos os estilos da aplicação de forma centralizada"""
    
    @staticmethod
    def load_base_styles():
        """Carrega os estilos base da aplicação"""
        try:
            with open('.streamlit/style.css', 'r', encoding='utf-8') as f:
                css_content = f.read()
                st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
        except FileNotFoundError:
            st.warning("Arquivo de estilos não encontrado")
    
    @staticmethod
    def apply_sidebar_fix():
        """Aplica correções específicas para a sidebar"""
        st.markdown("""
        <style>
        section[data-testid="stSidebar"] .stButton {
            margin: 4px 0 !important;
        }
        </style>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def apply_selectbox_fix():
        """Aplica correções específicas para selectbox"""
        st.markdown("""
        <script>
        function fixSelectboxVisibility() {
            const selectboxes = document.querySelectorAll('[data-testid="stSelectbox"]');
            selectboxes.forEach(selectbox => {
                const elements = selectbox.querySelectorAll('*');
                elements.forEach(el => {
                    el.style.setProperty('color', '#1e1e1e', 'important');
                    el.style.setProperty('background-color', 'transparent', 'important');
                });
            });
        }
        
        // Executar na inicialização e em intervalos
        document.addEventListener('DOMContentLoaded', fixSelectboxVisibility);
        setInterval(fixSelectboxVisibility, 1000);
        </script>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def apply_page_header():
        """Aplica o cabeçalho padrão da página"""
        st.markdown("""
        <div class="app-header">
            <h1 style="margin: 0; font-size: 1.5rem;">📋 Planner Organizer</h1>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def apply_all_fixes():
        """Aplica todas as correções de estilo necessárias"""
        StylesManager.load_base_styles()
        StylesManager.apply_sidebar_fix()
        StylesManager.apply_selectbox_fix()
        StylesManager.apply_page_header()
