"""
Módulo auxiliar para gerar rodapés padronizados em todos os PDFs do sistema.
"""
from datetime import datetime, timedelta

def obter_dados_rodape():
    """
    Obtém dados do perfil do usuário para usar no rodapé dos PDFs
    
    Returns:
        tuple: (nome_empresa, cargo_funcao, instagram)
    """
    try:
        import streamlit as st
        from utils.database import Database
        
        # Dados padrão como fallback
        nome_empresa = "Planner Organizer"
        cargo_funcao = "Personal Organizer"
        instagram = "@plannerorganizer"
        
        # Tentar obter dados do perfil do usuário
        if 'db' in st.session_state:
            db = st.session_state.db
            perfil = db.get_perfil_usuario()
            
            if perfil:
                nome_empresa = perfil.get('empresa') or perfil.get('nome', nome_empresa)
                instagram = perfil.get('instagram') or instagram.replace('@', '')
                cargo_funcao = perfil.get('cargo') or cargo_funcao
        
        return nome_empresa, cargo_funcao, instagram
        
    except Exception as e:
        print(f"Erro ao obter dados do perfil para rodapé: {str(e)}")
        return "Planner Organizer", "Personal Organizer", "@plannerorganizer"

def aplicar_rodape_padronizado(c, width, height=40, ajuste_brasilia=True):
    """
    Aplica rodapé padronizado centralizado em PDFs
    
    Args:
        c: Canvas do ReportLab
        width: Largura da página
        height: Altura do rodapé (padrão 40)
        ajuste_brasilia: Se deve ajustar horário para UTC-3 (padrão True)
    """
    from reportlab.lib import colors
    
    # Configurar fundo azul escuro
    azul_escuro = colors.HexColor("#1E366F")
    c.setFillColor(azul_escuro)
    c.rect(0, 0, width, height, fill=True, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica", 10)
    
    # Obter dados do perfil
    nome_empresa, cargo_funcao, instagram = obter_dados_rodape()
    
    # Primeira linha: informações da empresa (centralizada)
    footer_text = f"{nome_empresa} | {cargo_funcao} | {instagram}"
    text_width = c.stringWidth(footer_text, "Helvetica", 10)
    center_x = width / 2 - text_width / 2
    c.drawString(center_x, 25, footer_text)
    
    # Tornar Instagram clicável se contém dados válidos
    if instagram and instagram != "@plannerorganizer":
        # Calcular posição do Instagram no texto
        prefix = f"{nome_empresa} | {cargo_funcao} | "
        prefix_width = c.stringWidth(prefix, "Helvetica", 10)
        instagram_width = c.stringWidth(instagram, "Helvetica", 10)
        
        # Criar link clicável para Instagram
        instagram_url = f"https://instagram.com/{instagram.replace('@', '')}"
        c.linkURL(instagram_url, 
                 (center_x + prefix_width, 20, 
                  center_x + prefix_width + instagram_width, 30))
    
    # Segunda linha: data de geração (centralizada)
    if ajuste_brasilia:
        agora = datetime.now() - timedelta(hours=3)  # Ajustando para UTC-3 (Brasília)
    else:
        agora = datetime.now()
        
    date_text = f"Gerado em {agora.strftime('%d/%m/%Y às %H:%M')}"
    date_width = c.stringWidth(date_text, "Helvetica", 10)
    date_center_x = width / 2 - date_width / 2
    c.drawString(date_center_x, 10, date_text)