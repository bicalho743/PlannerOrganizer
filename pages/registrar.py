"""
Página de registro de novos usuários
"""
import streamlit as st
import time
from utils.firebase_auth import firebase_auth

def show():
    """
    Exibe o formulário de registro de usuário
    """
    st.markdown('<h1 style="font-size: 2rem; font-weight: 600; margin-top: 0; padding-top: 0; margin-bottom: 1rem; color: #C9A84C;">Criar Nova Conta</h1>', unsafe_allow_html=True)
    
    with st.container():
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col2:
            st.markdown("""
            <div style="text-align: center; margin-bottom: 1.5rem;">
                <h3 style="color: rgba(245,240,232,0.9); margin-bottom: 0.5rem;">Registre-se no Planner Organizer</h3>
                <p style="color: rgba(245,240,232,0.55); font-size: 0.9rem;">
                    Crie sua conta para começar a gerenciar propostas e finanças
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Formulário de cadastro
            with st.form("registration_form", clear_on_submit=False):
                name = st.text_input("Nome completo")
                email = st.text_input("Email", help="Será usado para login")
                password = st.text_input("Senha", type="password", 
                                        help="Mínimo de 6 caracteres")
                password_confirm = st.text_input("Confirme a senha", type="password")
                
                st.markdown(
                    '<p style="color: rgba(245,240,232,0.7); font-size: 0.85rem; margin-bottom: 0.25rem;">'
                    'Ao criar sua conta, você concorda com nossos '
                    '<a href="?show_termos=true" target="_blank" style="color: #C9A84C; text-decoration: underline;">Termos de Uso</a>'
                    ' e '
                    '<a href="?show_politica=true" target="_blank" style="color: #C9A84C; text-decoration: underline;">Política de Privacidade</a>.'
                    '</p>',
                    unsafe_allow_html=True
                )
                terms_accepted = st.checkbox("Li e aceito os termos de uso e política de privacidade")
                
                # Botão de registro com estilo
                submitted = st.form_submit_button("Criar Conta", use_container_width=True)
                
                if submitted:
                    # Validar os campos
                    if not name or not email or not password:
                        st.error("Todos os campos são obrigatórios.")
                    elif password != password_confirm:
                        st.error("As senhas não coincidem.")
                    elif len(password) < 6:
                        st.error("A senha deve ter pelo menos 6 caracteres.")
                    elif not terms_accepted:
                        st.error("Você precisa aceitar os termos de uso para criar uma conta.")
                    else:
                        # Exibir spinner durante o registro
                        with st.spinner("Criando sua conta..."):
                            # Tentar registrar no Firebase
                            result = firebase_auth.register(email, password, name)
                            
                            if result['success']:
                                # Exibir mensagem de sucesso
                                st.success("Conta criada com sucesso! Redirecionando...")
                                # Esperar um pouco antes de redirecionar
                                # Redirecionar para a página principal
                                st.session_state.show_welcome = True
                                st.session_state.current_page = "Dashboard"
                                st.rerun()
                            else:
                                # Exibir mensagem de erro
                                st.error(f"Erro ao criar conta: {result['error']}")
            
            # Texto centralizado
            st.markdown("""
            <div style="text-align: center; margin-top: 1rem;">
                <p style="color: rgba(245,240,232,0.45); font-size: 0.9rem;">
                    Já tem uma conta?
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Botão Streamlit para voltar ao login
            if st.button("Voltar ao login", use_container_width=True):
                # Definir a página de login como "login" para voltar à tela inicial
                st.session_state.login_page = "login"
                # Garantir que não há outras flags ativas
                if 'show_welcome' in st.session_state:
                    st.session_state.show_welcome = False
                st.rerun()

if __name__ == "__main__":
    show()