import streamlit as st
import os
import re
from utils.brevo_helper import adicionar_contato_brevo, enviar_email_brevo

# Configuração da página
st.set_page_config(
    page_title="Manual Planner Organizer",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS personalizado
st.markdown("""
<style>
    .main {
        padding: 2rem;
        background-color: #f9f9f9;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        border: none;
        width: 100%;
    }
    .stTextInput>div>div>input {
        padding: 0.5rem;
        font-size: 16px;
        border-radius: 4px;
    }
    .main .block-container {
        max-width: 800px;
        padding: 2rem;
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    h1 {
        color: #333;
        margin-bottom: 2rem;
        text-align: center;
    }
    h3 {
        color: #555;
        margin-top: 1.5rem;
    }
    .success-icon {
        font-size: 72px;
        color: #4CAF50;
        text-align: center;
        margin: 2rem 0;
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Verificar se o manual existe
    manual_path = os.path.join("pdfs", "Manual_Planner_Organizer.pdf")
    if not os.path.exists(manual_path):
        st.error("⚠️ Manual Planner Organizer não encontrado. Por favor, verifique a pasta pdfs.")
        st.stop()
    
    # Inicializar session_state
    if 'manual_form_status' not in st.session_state:
        st.session_state.manual_form_status = ""
    
    # Título da página
    st.title("Manual Planner Organizer")
    
    # Imagem ou logo (opcional)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("app-icon-192.png", use_column_width=True)
    
    st.markdown("""
    <p style="font-size: 18px; margin: 2rem 0; text-align: center;">
        Digite seu e-mail para receber automaticamente o Manual Planner Organizer.
        O manual será enviado para você imediatamente.
    </p>
    """, unsafe_allow_html=True)
    
    # Formulário simplificado
    with st.container():
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            nome = st.text_input("Seu Nome", placeholder="Digite seu nome completo", key="nome_simplificado")
            email = st.text_input("Seu E-mail", placeholder="Digite seu e-mail", key="email_simplificado")
            
            # Validação básica de e-mail
            email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
            
            # Botão de envio
            btn_enviar = st.button("Enviar Manual Automaticamente", use_container_width=True)
            
            if btn_enviar:
                # Validação simples dos campos
                if not nome.strip():
                    st.error("Por favor, informe seu nome.")
                elif not email or not re.match(email_pattern, email):
                    st.error("Por favor, informe um e-mail válido.")
                else:
                    # Informar ao usuário que o processo foi iniciado
                    with st.spinner("Enviando manual para seu e-mail..."):
                        # Adicionar o e-mail à lista no Brevo e enviar o manual automaticamente
                        resultado_adicao = adicionar_contato_brevo(email, nome)
                        
                        # Preparar e enviar o e-mail com o manual como anexo
                        mensagem_html = f"""
                        <h2>Manual Planner Organizer</h2>
                        <p>Olá <strong>{nome}</strong>,</p>
                        <p>Obrigado pelo seu interesse no Planner Organizer!</p>
                        <p>Segue o Manual Planner Organizer em anexo.
                        Este documento contém todas as informações necessárias para utilizar nossa plataforma
                        de forma eficiente e aproveitar ao máximo os recursos disponíveis.</p>
                        <p>Se você tiver qualquer dúvida após a leitura do manual, não hesite em nos contatar.</p>
                        <p>Atenciosamente,<br>Equipe Planner Organizer</p>
                        """
                        
                        resultado_email = enviar_email_brevo(
                            destinatario_email=email,
                            destinatario_nome=nome,
                            assunto="Manual Planner Organizer",
                            mensagem_html=mensagem_html,
                            anexo=manual_path
                        )
                        
                        # Registrar o sucesso ou fracasso independentemente do resultado da adição à lista
                        if resultado_email.get("success", False):
                            st.session_state.manual_form_status = "success"
                            st.session_state.nome_usuario = nome
                            st.session_state.email_usuario = email
                            st.rerun()  # Recarregar para mostrar a mensagem de sucesso
                        else:
                            st.error("Não foi possível enviar o manual. Por favor, tente novamente mais tarde.")
                            st.info(resultado_email.get("message", ""))
    
    # Exibir mensagem de sucesso
    if st.session_state.manual_form_status == "success":
        st.markdown("""
        <div style="text-align: center; padding: 2rem; background-color: #f1f9f1; border-radius: 10px; margin-top: 2rem;">
            <div class="success-icon">📚</div>
            <h2 style="color: #4CAF50;">Manual Enviado com Sucesso!</h2>
            <p style="font-size: 18px;">
                Olá <strong>{}</strong>, seu manual foi enviado para <strong>{}</strong>.
            </p>
            <p>Por favor, verifique também sua pasta de spam caso não encontre o e-mail em sua caixa de entrada.</p>
        </div>
        """.format(st.session_state.nome_usuario, st.session_state.email_usuario), unsafe_allow_html=True)
    
    # Benefícios do manual
    if st.session_state.manual_form_status != "success":
        st.markdown("""
        <div style="margin-top: 3rem; padding: 1.5rem; background-color: #f7f7f7; border-radius: 10px;">
            <h3 style="text-align: center; margin-bottom: 1rem;">O Manual Planner Organizer inclui:</h3>
            <ul style="list-style-type: none; padding-left: 0;">
                <li style="padding: 0.5rem 0;">✅ <strong>Guia completo</strong> de todas as funcionalidades do sistema</li>
                <li style="padding: 0.5rem 0;">✅ <strong>Passo a passo</strong> para criar e gerenciar propostas</li>
                <li style="padding: 0.5rem 0;">✅ <strong>Dicas de produtividade</strong> para otimizar seu fluxo de trabalho</li>
                <li style="padding: 0.5rem 0;">✅ <strong>Instruções detalhadas</strong> para importar e exportar dados</li>
                <li style="padding: 0.5rem 0;">✅ <strong>Exemplos práticos</strong> de uso em diferentes cenários</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Rodapé
    st.markdown("""
    <div style="margin-top: 3rem; text-align: center; color: #888; font-size: 14px;">
        <p>© 2025 Planner Organizer - Todos os direitos reservados</p>
        <p>Em caso de dúvidas, entre em contato: contato@plannerorganizer.com.br</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()