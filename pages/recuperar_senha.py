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
    st.title("Recuperar Senha")
    
    # Container para o formulário
    with st.container():
        # Usar colunas para centralizar o formulário
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            <div style="text-align: center; margin-bottom: 1.5rem;">
                <h3 style="color: #1E366F; margin-bottom: 0.5rem;">Esqueceu sua senha?</h3>
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
                                # Exibir mensagem de sucesso
                                st.success("Um email de recuperação foi enviado. Verifique sua caixa de entrada.")
                                # Redirecionar será feito com botão fora do formulário
                            else:
                                # Exibir mensagem de erro
                                st.error(f"Erro: {result['error']}")
            
            # Botão para voltar ao login (fora do formulário)
            if st.button("Voltar ao Login", key="btn_voltar_login", use_container_width=True):
                # Resetar o estado de login_page para "login"
                st.session_state.login_page = "login"
                st.rerun()

if __name__ == "__main__":
    show()