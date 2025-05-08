import streamlit as st
import os
from utils.brevo_helper import adicionar_contato_brevo, enviar_email_brevo
from utils.database import create_engine, get_connection

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
    # Título da página
    st.title("Receba o Manual Planner Organizer")
    
    st.markdown("""
    <p style="font-size: 18px; margin-bottom: 2rem; text-align: center;">
        Preencha o formulário abaixo para receber o manual completo do Planner Organizer em seu e-mail.
    </p>
    """, unsafe_allow_html=True)
    
    # Inicializar session_state
    if 'manual_form_status' not in st.session_state:
        st.session_state.manual_form_status = ""
    
    # Seção do formulário
    with st.container():
        st.subheader("Seus Dados")
        
        # Campos do formulário
        nome = st.text_input("Nome Completo", placeholder="Digite seu nome completo")
        email = st.text_input("E-mail", placeholder="Digite seu e-mail corporativo")
        empresa = st.text_input("Empresa", placeholder="Nome da sua empresa (opcional)")
        
        # Verificar se o manual existe
        manual_path = os.path.join("pdfs", "Manual_Planner_Organizer.pdf")
        if not os.path.exists(manual_path):
            st.warning("⚠️ Manual Planner Organizer não encontrado. Por favor, verifique a pasta pdfs.")
            manual_disponivel = False
        else:
            manual_disponivel = True
            st.success("✅ Manual Planner Organizer está disponível para envio.")
        
        # Botão de envio
        btn_enviar = st.button("Receber Manual por E-mail", disabled=not manual_disponivel)
        
        if btn_enviar:
            if not nome.strip():
                st.error("Por favor, informe seu nome.")
            elif not email or "@" not in email:
                st.error("Por favor, informe um e-mail válido.")
            else:
                # Adicionar o e-mail à lista no Brevo
                resultado_adicao = adicionar_contato_brevo(email, nome)
                
                if resultado_adicao.get("success", False):
                    # Preparar e enviar o e-mail com o manual como anexo
                    mensagem_html = f"""
                    <h2>Manual Planner Organizer</h2>
                    <p>Olá <strong>{nome}</strong>,</p>
                    <p>Obrigado pelo seu interesse no Planner Organizer!</p>
                    <p>Conforme solicitado, estamos enviando o Manual Planner Organizer em anexo.
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
                    
                    if resultado_email.get("success", False):
                        st.session_state.manual_form_status = "success"
                        st.session_state.nome_usuario = nome
                        st.session_state.email_usuario = email
                        st.rerun()  # Recarregar para mostrar a mensagem de sucesso
                    else:
                        # Se falhar o envio do e-mail, mostrar erro
                        st.error("Não foi possível enviar o manual. Por favor, tente novamente mais tarde.")
                        st.info(resultado_email.get("message", ""))
                else:
                    # Se falhar a adição ao Brevo, mostrar erro
                    st.error("Não foi possível processar sua solicitação. Por favor, tente novamente mais tarde.")
                    st.info(resultado_adicao.get("message", ""))
    
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
    
    # Rodapé
    st.markdown("""
    <div style="margin-top: 3rem; text-align: center; color: #888; font-size: 14px;">
        <p>© 2025 Planner Organizer - Todos os direitos reservados</p>
        <p>Em caso de dúvidas, entre em contato: contato@plannerorganizer.com.br</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()