"""
Página de recuperação de senha
"""
import streamlit as st
import os
from firebase_admin import auth
from utils.firebase_config import initialize_firebase

def show():
    """
    Exibe a página de recuperação de senha
    """
    # Configuração da página
    st.markdown('<h1 style="text-align: center; color: #1E366F;">Recuperar Senha</h1>', unsafe_allow_html=True)
    
    # Formulário de recuperação de senha
    with st.container():
        st.markdown('<p style="text-align: center;">Informe seu e-mail para receber um link de redefinição de senha.</p>', unsafe_allow_html=True)
        
        email = st.text_input("E-mail", key="email_reset")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("Enviar link de recuperação", use_container_width=True):
                if not email:
                    st.error("Por favor, informe seu e-mail.")
                else:
                    try:
                        # Inicializar Firebase
                        app, _ = initialize_firebase()
                        
                        if not app:
                            st.error("Erro ao conectar com o serviço de autenticação.")
                            return
                        
                        # Enviar e-mail de recuperação
                        with st.spinner("Enviando link de recuperação..."):
                            # Determinar a URL de callback dinâmica baseada no ambiente
                            base_url = "https://plannerorganiza.com.br"
                            if os.environ.get("REPLIT_DOMAIN"):
                                base_url = f"https://{os.environ.get('REPLIT_DOMAIN')}"
                            callback_url = f"{base_url}/login"
                            
                            # Gera o link de redefinição com configurações adicionais
                            action_code_settings = {
                                'url': callback_url,  # URL para redirecionar após redefinir senha
                                'handleCodeInApp': False  # Define que o código será tratado por e-mail, não por app
                            }
                            
                            st.write(f"URL de callback configurada: {callback_url}")  # Debug info
                            
                            # Tentar gerar o link de redefinição
                            reset_link = auth.generate_password_reset_link(
                                email, 
                                action_code_settings
                            )
                            
                            st.success(f"Link de redefinição enviado para {email}. Verifique sua caixa de entrada e pasta de spam.")
                            st.info("Após redefinir sua senha, você poderá fazer login com a nova senha.")
                    
                    except Exception as e:
                        if "USER_NOT_FOUND" in str(e):
                            # Por segurança, não informamos se o e-mail existe ou não
                            st.success(f"Se {email} estiver registrado, você receberá um e-mail com instruções para redefinir sua senha.")
                        else:
                            st.error(f"Ocorreu um erro: {str(e)}")
        
        with col2:
            if st.button("Voltar para o login", use_container_width=True):
                st.session_state.login_page = "login"
                st.rerun()
    
    # Adicionar informações de ajuda
    st.markdown("""
    <div style="margin-top: 30px; padding: 15px; border-radius: 5px; background-color: #f8f9fa;">
        <h3 style="color: #1E366F; font-size: 1.2rem;">Não recebeu o e-mail?</h3>
        <ul>
            <li>Verifique sua pasta de spam ou lixo eletrônico</li>
            <li>Certifique-se de que o e-mail informado está correto</li>
            <li>Aguarde alguns minutos e tente novamente</li>
        </ul>
        <p>Se continuar com problemas, entre em contato com o suporte.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Adicionar um rodapé
    st.markdown("""
    <div style="position: fixed; bottom: 0; left: 0; right: 0; background-color: #f5f5f5; padding: 10px; text-align: center; font-size: 0.8rem; color: #666;">
        © 2025 Planner Organizer | Todos os direitos reservados
    </div>
    """, unsafe_allow_html=True)