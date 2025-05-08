import streamlit as st
import os
import sys
import time
import re
from datetime import datetime

# Adicionar diretório raiz ao path para poder importar os módulos de utils
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.render_fix import inject_render_compatibility_fix
from utils.brevo_helper import adicionar_contato_brevo

# Inicializar estados da sessão para controle do formulário
def initialize_session_state():
    if 'form_status' not in st.session_state:
        st.session_state.form_status = None
    
    if 'form_processed' not in st.session_state:
        st.session_state.form_processed = False
    
    if 'form_submit_time' not in st.session_state:
        st.session_state.form_submit_time = None

def clear_form():
    """
    Limpa o formulário alterando as chaves dos campos.
    No Streamlit, não podemos modificar diretamente valores de widgets,
    mas podemos usar diferentes chaves para que a próxima renderização mostre campos vazios.
    """
    # Gerar timestamp único para novas chaves
    timestamp = str(datetime.now().timestamp())
    st.session_state.nome_reset = timestamp
    st.session_state.email_reset = timestamp
    st.session_state.form_processed = True
    
    # Forçar nova renderização usando JavaScript
    st.markdown("""
    <script>
        window.location.href = window.location.href;
    </script>
    """, unsafe_allow_html=True)

def main(set_config=True):
    # Configuração da página apenas quando executando como script principal
    if set_config:
        try:
            st.set_page_config(
                page_title="Planos de Assinatura - Planner Organizer",
                page_icon="favicon.png",
                layout="wide",
                initial_sidebar_state="collapsed"
            )
        except Exception as e:
            pass  # Silenciosamente ignora erros de configuração quando importado
    
    # Ocultar a barra lateral completamente
    st.markdown("""
    <style>
    [data-testid="collapsedControl"] {display: none !important;}
    section[data-testid="stSidebar"] {display: none !important;}
    header[data-testid="stHeader"] {display: none !important;}
    </style>
    """, unsafe_allow_html=True)
    
    # Injetar script de compatibilidade para o Render (se necessário)
    inject_render_compatibility_fix()
    
    # Inicializar estado da sessão
    initialize_session_state()
    
    # Configuração da página
    st.title("Planos de Assinatura")
    
    # Mensagem de página em construção com estilos inline
    st.markdown("""
    <div style="background: linear-gradient(135deg, #f5f7fa, #e9eff6); padding: 3rem 2rem; border-radius: 16px; text-align: center; margin: 2rem auto; max-width: 800px; box-shadow: 0 8px 24px rgba(0,0,0,0.1);">
        <div style="font-size: 5rem; margin-bottom: 1.5rem; color: #4F4F52; animation: pulse 2s infinite ease-in-out; display: inline-block;">🏗️</div>
        <div style="font-size: 2.2rem; font-weight: 700; color: #4F4F52; margin-bottom: 1rem;">Página em Construção</div>
        <div style="font-size: 1.2rem; color: #5A6A85; margin-bottom: 2rem; line-height: 1.6;">
            Estamos trabalhando para trazer os melhores planos e preços para sua experiência com o Planner Organizer.
            Em breve, você poderá escolher o plano que melhor atende às necessidades do seu negócio.
        </div>
    </div>
    
    <style>
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    @keyframes bounceIn {
        0% { transform: scale(0.1); opacity: 0; }
        60% { transform: scale(1.2); opacity: 1; }
        100% { transform: scale(1); }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Adicionando cards de informação
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; margin-bottom: 2rem; border-left: 4px solid #4CAF50; text-align: left; height: 100%;">
            <div style="font-weight: 600; color: #4F4F52; margin-bottom: 0.5rem; font-size: 1.2rem;">Enquanto isso...</div>
            <div style="color: #5A6A85; font-size: 1rem; line-height: 1.5;">
                Você pode utilizar nossa versão de demonstração gratuitamente para conhecer todas as funcionalidades do sistema. 
                Basta fazer login com as credenciais de demonstração disponíveis na página inicial.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; margin-bottom: 2rem; border-left: 4px solid #4CAF50; text-align: left; height: 100%;">
            <div style="font-weight: 600; color: #4F4F52; margin-bottom: 0.5rem; font-size: 1.2rem;">Quer ser notificado quando os planos estiverem disponíveis?</div>
            <div style="color: #5A6A85; font-size: 1rem; line-height: 1.5; margin-bottom: 1rem;">
                Deixe seu e-mail conosco e informaremos assim que nossos planos de assinatura estiverem disponíveis,
                com condições especiais para os primeiros assinantes.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Adicionar formulário de captura de e-mail para integração com SendGrid
    st.markdown("""
    <div style="max-width: 800px; margin: 0 auto 2rem auto; background-color: #f7f7f8; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <h3 style="font-size: 1.3rem; color: #4F4F52; text-align: center; margin-bottom: 1rem;">Inscreva-se para receber notificações</h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    # Usar keys dinâmicas para permitir resetar os campos após sucesso
    nome_key = f"signup_name_{st.session_state.get('nome_reset', '')}"
    email_key = f"signup_email_{st.session_state.get('email_reset', '')}"
    
    with col1:
        nome = st.text_input("Nome", key=nome_key)
        
    with col2:
        email = st.text_input("Email", key=email_key)
    
    # Botão de envio centralizado
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Quero ser notificado", use_container_width=True):
            # Validar email
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            
            if not nome.strip():
                st.session_state.form_status = "error_nome"
            elif not email.strip():
                st.session_state.form_status = "error_email_vazio"
            elif not re.match(email_pattern, email):
                st.session_state.form_status = "error_email_invalido"
            else:
                try:
                    # Tentar capturar o e-mail usando o Brevo
                    result = adicionar_contato_brevo(
                        email=email, 
                        nome_completo=nome
                    )
                    
                    if result.get("success", False):
                        st.session_state.form_status = "success"
                        st.session_state.email_capturado = email
                        st.session_state.message = result.get("message", "")
                        
                        # Verificar se foi usado o modo de fallback
                        if result.get("fallback", False):
                            st.session_state.is_fallback = True
                        else:
                            st.session_state.is_fallback = False
                            
                        # Limpar os campos usando a técnica de chaves dinâmicas
                        clear_form()
                    else:
                        st.session_state.form_status = "error_brevo"
                        st.session_state.error_msg = result.get("message", "Erro ao processar seu e-mail.")
                        
                except Exception as e:
                    st.session_state.form_status = "error_exception"
                    st.session_state.error_msg = str(e)
    
    # Exibir mensagens com base no status do formulário
    if st.session_state.form_status == "success":
        if hasattr(st.session_state, 'is_fallback') and st.session_state.is_fallback:
            st.success(f"Obrigado! Seu e-mail **{st.session_state.email_capturado}** foi salvo em nossa lista local. Entraremos em contato assim que nossos planos estiverem disponíveis.")
        else:
            st.success(f"Obrigado! Seu e-mail **{st.session_state.email_capturado}** foi registrado com sucesso. Você receberá notificações sobre nossos planos assim que estiverem disponíveis.")
        
        # Animação de sucesso
        st.markdown("""
        <div style="text-align: center; margin: 2rem 0;">
            <div style="font-size: 64px; animation: bounceIn 1s;">✅</div>
        </div>
        """, unsafe_allow_html=True)
        
    elif st.session_state.form_status == "error_nome":
        st.error("Por favor, informe seu nome.")
    elif st.session_state.form_status == "error_email_vazio":
        st.error("Por favor, informe seu email.")
    elif st.session_state.form_status == "error_email_invalido":
        st.error("Por favor, informe um email válido.")
    elif st.session_state.form_status == "error_brevo":
        st.error("Desculpe, ocorreu um erro ao processar seu e-mail. Por favor, tente novamente mais tarde.")
        if hasattr(st.session_state, 'error_msg'):
            st.info(st.session_state.error_msg)
    elif st.session_state.form_status == "error_exception":
        st.error("Ocorreu um erro inesperado. Por favor, tente novamente mais tarde.")
        if hasattr(st.session_state, 'error_msg'):
            st.exception(st.session_state.error_msg)
    
    # Seção de informações adicionais
    st.markdown("""
    <div style="text-align: center; margin-top: 2rem; color: #5A6A85; font-size: 0.9rem;">
        <p>Para mais informações ou para solicitar um orçamento personalizado, entre em contato com nossa equipe.</p>
        <p>E-mail: contato@plannerorganizer.com.br | Telefone: (11) 4321-1234</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Botão para voltar à página inicial
    if st.button("Voltar para a página inicial"):
        # Redirecionar para a página inicial
        st.markdown("""
        <script>
            window.close();
            window.opener.location.href = "/";
        </script>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()