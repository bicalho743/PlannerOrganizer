import streamlit as st
import os
import sys
from PIL import Image

# Adicionar diretório raiz ao path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from utils.brevo_helper import adicionar_contato_brevo, enviar_manual_email

def main():
    # Configuração da página
    st.set_page_config(
        page_title="Enviar Manual - Planner Organizer",
        page_icon="favicon.png",
        layout="centered"
    )
    
    # CSS para esconder completamente a barra lateral
    st.markdown("""
    <style>
    [data-testid="collapsedControl"] {display: none !important;}
    section[data-testid="stSidebar"] {display: none !important;}
    header {display: none !important;}
    footer {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}
    .block-container {padding-top: 1rem !important; max-width: 100% !important;}
    </style>
    """, unsafe_allow_html=True)

    # Título e descrição
    st.title("Manual do Sistema Planner Organizer")
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <p style="font-size: 1.2rem; color: #5A6A85;">
            Receba gratuitamente o manual completo do sistema por e-mail.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Separar em colunas
    col1, col2 = st.columns([1, 1])
    
    with col1:
        try:
            # Tenta carregar a imagem
            img_path = os.path.join(root_dir, "professional_woman.png")
            if os.path.exists(img_path):
                image = Image.open(img_path)
                st.image(image, width=150)
            else:
                st.info("Imagem ilustrativa não encontrada.")
        except Exception as e:
            st.error(f"Erro ao carregar imagem: {e}")
    
    with col2:
        # Formulário de cadastro
        with st.form("manual_form"):
            nome = st.text_input("Nome completo:")
            email = st.text_input("E-mail:")
            empresa = st.text_input("Empresa (opcional):", "")
            
            enviar = st.form_submit_button("Receber Manual", use_container_width=True)
            
            if enviar:
                if not nome:
                    st.error("Por favor, informe seu nome.")
                elif not email:
                    st.error("Por favor, informe seu email.")
                elif "@" not in email:
                    st.error("Por favor, informe um email válido.")
                else:
                    with st.spinner("Processando solicitação..."):
                        # 1. Adicionar contato ao Brevo
                        result_contato = adicionar_contato_brevo(
                            email=email,
                            nome_completo=nome
                        )
                        
                        if result_contato.get("success", False):
                            # 2. Enviar o manual por e-mail
                            result_email = enviar_manual_email(
                                destinatario_email=email,
                                destinatario_nome=nome
                            )
                            
                            if result_email.get("success", False):
                                st.success(f"✅ Obrigado! O Manual do Sistema foi enviado para {email}. Verifique sua caixa de entrada em alguns minutos.")
                                
                                # Esconder o formulário após envio bem-sucedido
                                st.session_state.form_submitted = True
                            else:
                                st.warning(f"⚠️ Seu e-mail foi registrado, mas não conseguimos enviar o manual agora: {result_email.get('message', 'Erro no envio')}. Tentaremos novamente mais tarde.")
                        else:
                            st.error(f"❌ Não foi possível processar sua solicitação: {result_contato.get('message', 'Erro desconhecido')}.")
    
    # Informações adicionais
    st.markdown("""
    <div style="margin-top: 2rem; padding: 1.5rem; background-color: #f8f9fa; border-radius: 10px;">
        <h3 style="color: #444;">Sobre o Manual</h3>
        <p>O Manual do Sistema Planner Organizer contém:</p>
        <ul>
            <li>Instruções detalhadas de todas as funcionalidades</li>
            <li>Guia completo para gerenciamento de propostas</li>
            <li>Tutorial do sistema financeiro integrado</li>
            <li>Melhores práticas para organização de clientes</li>
            <li>Dicas para maximizar sua produtividade</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Rodapé
    st.markdown("""
    <div style="margin-top: 2rem; text-align: center; color: #777;">
        <p>© 2025 Planner Organizer. Todos os direitos reservados.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()