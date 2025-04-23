"""
Página de cadastro de novos usuários
"""
import streamlit as st
import os
from firebase_admin import auth
from utils.firebase_config import initialize_firebase, create_user

def show():
    """
    Exibe a página de cadastro de usuários
    """
    # Configuração da página
    st.markdown('<h1 style="text-align: center; color: #1E366F;">Criar Conta</h1>', unsafe_allow_html=True)
    
    # Formulário de cadastro
    with st.container():
        st.markdown('<p style="text-align: center;">Preencha os campos abaixo para criar sua conta.</p>', unsafe_allow_html=True)
        
        with st.form("cadastro_form"):
            nome = st.text_input("Nome", key="nome_cadastro")
            email = st.text_input("E-mail", key="email_cadastro")
            senha = st.text_input("Senha", type="password", key="senha_cadastro")
            confirmar_senha = st.text_input("Confirmar Senha", type="password", key="confirmar_senha_cadastro")
            
            submit = st.form_submit_button("Criar Conta", use_container_width=True)
            
            if submit:
                if not nome or not email or not senha or not confirmar_senha:
                    st.error("Por favor, preencha todos os campos.")
                elif senha != confirmar_senha:
                    st.error("As senhas não coincidem.")
                elif len(senha) < 6:
                    st.error("A senha deve ter pelo menos 6 caracteres.")
                else:
                    # Inicializar Firebase
                    app, _ = initialize_firebase()
                    
                    if not app:
                        st.error("Erro ao conectar com o serviço de autenticação.")
                    else:
                        # Criar usuário
                        with st.spinner("Criando sua conta..."):
                            result = create_user(email, senha, nome)
                            
                            if result.get("success"):
                                st.success("Conta criada com sucesso! Você já pode fazer login.")
                                # Adicionar botão para voltar ao login
                                if st.button("Ir para o login"):
                                    st.session_state.login_page = "login"
                                    st.rerun()
                            else:
                                error_msg = result.get("error", "Erro desconhecido.")
                                if "EMAIL_EXISTS" in error_msg:
                                    st.error("Este e-mail já está em uso. Por favor, use outro e-mail ou faça login.")
                                else:
                                    st.error(f"Erro ao criar conta: {error_msg}")
        
        # Botão para voltar ao login fora do formulário
        if st.button("Voltar para o login", use_container_width=True):
            st.session_state.login_page = "login"
            st.rerun()
    
    # Adicionar informações adicionais
    st.markdown("""
    <div style="margin-top: 30px; padding: 15px; border-radius: 5px; background-color: #f8f9fa;">
        <h3 style="color: #1E366F; font-size: 1.2rem;">Importante:</h3>
        <ul>
            <li>Use uma senha forte com pelo menos 6 caracteres</li>
            <li>Guarde suas credenciais em um local seguro</li>
            <li>Seu e-mail será usado para comunicações importantes do sistema</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Adicionar um rodapé
    st.markdown("""
    <div style="position: fixed; bottom: 0; left: 0; right: 0; background-color: #f5f5f5; padding: 10px; text-align: center; font-size: 0.8rem; color: #666;">
        © 2025 Planner Organizer | Todos os direitos reservados
    </div>
    """, unsafe_allow_html=True)