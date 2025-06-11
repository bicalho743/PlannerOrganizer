"""
Módulo para geração de manual do sistema
"""
import streamlit as st
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime

def gerar_manual_sistema():
    """
    Gera um manual do sistema em PDF
    """
    try:
        # Criar diretório pdfs se não existir
        os.makedirs("pdfs", exist_ok=True)
        
        # Caminho do arquivo
        filename = os.path.join("pdfs", "manual_sistema.pdf")
        
        # Criar documento PDF
        doc = SimpleDocTemplate(filename, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Título
        title = Paragraph("Manual do Sistema Planner Organizer", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Conteúdo do manual
        content = [
            "Bem-vindo ao Planner Organizer",
            "",
            "Este sistema foi desenvolvido para auxiliar personal organizers no gerenciamento de clientes e propostas.",
            "",
            "Funcionalidades principais:",
            "• Cadastro de clientes",
            "• Gestão de propostas",
            "• Controle financeiro",
            "• Relatórios de vendas",
            "",
            f"Manual gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        ]
        
        for line in content:
            if line:
                para = Paragraph(line, styles['Normal'])
            else:
                para = Spacer(1, 6)
            story.append(para)
        
        # Construir PDF
        doc.build(story)
        
        return filename
        
    except Exception as e:
        st.error(f"Erro ao gerar manual: {str(e)}")
        return None

def main():
    """Função principal da página de geração de manual"""
    st.title("Geração de Manual do Sistema")
    
    if st.button("Gerar Manual PDF"):
        with st.spinner("Gerando manual..."):
            filename = gerar_manual_sistema()
            
            if filename and os.path.exists(filename):
                st.success("Manual gerado com sucesso!")
                
                # Disponibilizar para download
                with open(filename, "rb") as f:
                    st.download_button(
                        label="Download Manual",
                        data=f.read(),
                        file_name="manual_planner_organizer.pdf",
                        mime="application/pdf"
                    )
            else:
                st.error("Erro ao gerar manual.")

if __name__ == "__main__":
    main()