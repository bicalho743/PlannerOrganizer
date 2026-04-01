"""
Página de recuperação de senha
"""
import streamlit as st
import time
from utils.firebase_auth import firebase_auth

def show():
    """
    Exibe o formulário de recuperação de senha
    """
    st.markdown('<h1 style="font-size: 2rem; font-weight: 600; margin-top: 0; padding-top: 0; margin-bottom: 1rem;">Recuperar Senha</h1>', unsafe_allow_html=True)
    
    # Inicializar variáveis de estado
    if 'email_enviado' not in st.session_state:
        st.session_state.email_enviado = False
    
    # Container para o formulário
    with st.container():
        # Usar colunas para centralizar o formulário
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            <div style="text-align: center; margin-bottom: 1.5rem;">
                <h3 style="color: #0D1B2A; margin-bottom: 0.5rem;">Esqueceu sua senha?</h3>
                <p style="color: #5A6A85; font-size: 0.9rem;">
                    Informe seu email para receber um link de redefinição de senha
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Formulário de recuperação
            with st.form("password_recovery_form", clear_on_submit=False):
                email = st.text_input("Email cadastrado")
                
                # Botão de envio
                submitted = st.form_submit_button("Recuperar Senha", use_container_width=True)
                
                if submitted:
                    if not email:
                        st.error("Por favor, informe seu email.")
                    else:
                        # Exibir spinner durante o envio
                        with st.spinner("Enviando email de recuperação..."):
                            # Tentar enviar email de recuperação
                            result = firebase_auth.reset_password(email)
                            
                            if result['success']:
                                # Marcar que o email foi enviado
                                st.session_state.email_enviado = True
                                
                                # Exibir mensagem de sucesso
                                st.success("Um email de recuperação foi enviado. Verifique sua caixa de entrada e também a pasta de spam.")
                                
                                # Adicionar informações adicionais
                                st.info("""
                                **Importante:** 
                                - O link de redefinição é válido por 1 hora
                                - Se não receber o email em alguns minutos, verifique sua pasta de spam
                                - Às vezes, os emails podem levar até 10 minutos para chegar
                                """)
                            else:
                                # Exibir mensagem de erro
                                st.error(f"Erro: {result['error']}")
                                
                                # Adicionar sugestões para resolver problemas comuns
                                if "não cadastrado" in result['error'].lower():
                                    st.info("Verifique se o email foi digitado corretamente ou [crie uma nova conta](/?page=cadastro).")
                                elif "inválido" in result['error'].lower():
                                    st.info("Certifique-se de digitar um endereço de email válido no formato usuario@dominio.com")
                                elif "muitas tentativas" in result['error'].lower():
                                    st.info("Por segurança, aguarde alguns minutos antes de tentar novamente.")
            
            # Se o email foi enviado com sucesso, mostrar botão para voltar ao login
            if st.session_state.email_enviado:
                if st.button("Voltar ao Login", use_container_width=True):
                    # Resetar o estado
                    st.session_state.email_enviado = False
                    st.session_state.login_page = "login"
                    st.rerun()
            
            if not st.session_state.email_enviado:
                if st.button("Voltar ao login", key="link_voltar_login", use_container_width=True):
                    st.session_state.login_page = "login"
                    st.rerun()

if __name__ == "__main__":
    show()