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
    st.title("Criar Nova Conta")
    
    # Container para o formulário de registro
    with st.container():
        # Usar colunas para centralizar o formulário
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            <div style="text-align: center; margin-bottom: 1.5rem;">
                <h3 style="color: #1E366F; margin-bottom: 0.5rem;">Registre-se no Planner Organizer</h3>
                <p style="color: #5A6A85; font-size: 0.9rem;">
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
                
                # Checkbox de termos
                terms_accepted = st.checkbox("Aceito os termos de uso e política de privacidade")
                
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
                                time.sleep(2)
                                # Redirecionar para a página principal
                                st.session_state.show_welcome = True
                                st.session_state.current_page = "Dashboard"
                                st.rerun()
                            else:
                                # Exibir mensagem de erro
                                st.error(f"Erro ao criar conta: {result['error']}")
            
            # Link para voltar ao login
            st.markdown("""
            <div style="text-align: center; margin-top: 1rem;">
                <p style="color: #5A6A85; font-size: 0.9rem;">
                    Já tem uma conta? 
                    <a href="#" id="back-to-login" style="color: #1E88E5; text-decoration: none;">
                        Voltar ao login
                    </a>
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Adicionar JavaScript para voltar ao login
            st.markdown("""
            <script>
                document.getElementById('back-to-login').addEventListener('click', function(e) {
                    e.preventDefault();
                    window.history.back();
                });
            </script>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    show()