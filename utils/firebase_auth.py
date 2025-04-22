"""
Módulo para autenticação com Firebase
"""
import os
import json
import streamlit as st
import streamlit_authenticator as stauth
import logging
from utils.firebase_config import FIREBASE_CONFIG

# Configurar logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variável para indicar se o Firebase Admin SDK foi inicializado
firebase_initialized = False

class FirebaseAuthentication:
    """
    Classe para gerenciar autenticação com Firebase no Streamlit
    """
    def __init__(self):
        """Inicializa o Firebase Admin SDK"""
        self.firebase_initialized = firebase_initialized
        logger.info("Inicializando autenticação via Firebase")
    
    def criar_usuario(self, email, senha, nome):
        """
        Simula a criação de um novo usuário (em uma implementação real, usaria o Firebase SDK)
        
        Args:
            email (str): E-mail do usuário
            senha (str): Senha do usuário
            nome (str): Nome do usuário
            
        Returns:
            dict: Resposta contendo status e mensagem
        """
        # Versão simplificada e segura para demonstração
        # Em produção, usaria o Firebase Admin SDK para criar o usuário
        logger.info(f"Simulando criação de usuário: {email}")
        return {
            "status": True, 
            "mensagem": f"Usuário simulado criado com sucesso para {email}",
            "uid": "demo-user-id"
        }
    
    def autenticar_usuario(self, email, senha):
        """
        Autentica um usuário com email e senha
        
        Args:
            email (str): E-mail do usuário
            senha (str): Senha do usuário
            
        Returns:
            dict: Resposta contendo status e mensagem
        """
        # Esta função seria implementada com a API de autenticação do Firebase
        # Como o Firebase não possui API direta para verificar credenciais, isso seria feito via JavaScript
        # Aqui simulamos apenas para fins de demonstração
        return {"status": True, "mensagem": "Implementação de frontend pendente"}

def criar_componente_login():
    """
    Cria um componente de login usando streamlit_authenticator
    
    Returns:
        tuple: (authenticator, name, authentication_status, username)
    """
    # Configurações para o streamlit-authenticator
    credentials = {
        "usernames": {
            "admin": {
                "name": "Administrador",
                "password": stauth.Hasher(["admin"]).generate()[0]
            }
        }
    }
    
    cookie_name = "planner_organizer_auth"
    key = "planner_auth_key"
    cookie_expiry_days = 30
    
    authenticator = stauth.Authenticate(
        credentials,
        cookie_name,
        key,
        cookie_expiry_days
    )
    
    # Criar o widget de login
    name, authentication_status, username = authenticator.login('Login', 'main')
    
    # Verificar o status da autenticação
    if authentication_status:
        st.success(f'Bem-vindo *{name}*')
    elif authentication_status == False:
        st.error('Nome de usuário/senha incorreto')
    else:
        st.warning('Por favor, faça login')
    
    return authenticator, name, authentication_status, username

def criar_componente_registro():
    """
    Cria um componente para registro de novos usuários
    """
    st.subheader("Registrar nova conta")
    
    with st.form("formulario_registro"):
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Nome completo")
            email = st.text_input("E-mail")
        
        with col2:
            senha = st.text_input("Senha", type="password")
            confirmar_senha = st.text_input("Confirmar senha", type="password")
        
        aceito_termos = st.checkbox("Eu aceito os termos de uso")
        
        submit_button = st.form_submit_button("Criar conta")
        
        if submit_button:
            if not (nome and email and senha and confirmar_senha):
                st.error("Por favor, preencha todos os campos")
            elif senha != confirmar_senha:
                st.error("As senhas não coincidem")
            elif not aceito_termos:
                st.error("Você precisa aceitar os termos de uso")
            else:
                # Inicializar Firebase e criar usuário
                firebase_auth = FirebaseAuthentication()
                resultado = firebase_auth.criar_usuario(email, senha, nome)
                
                if resultado["status"]:
                    st.success(resultado["mensagem"])
                    st.info("Você pode fazer login agora")
                else:
                    st.error(resultado["mensagem"])

def criar_pagina_login():
    """
    Cria uma página completa de login com opções de autenticação
    
    Returns:
        bool: True se o usuário estiver autenticado, False caso contrário
    """
    # Criar um layout com duas colunas
    col1, col2 = st.columns([6, 4])
    
    with col1:
        st.markdown("""
        <div style="padding: 2rem; background-color: #f8f9fa; border-radius: 10px;">
            <h1 style="color: #1E366F; font-size: 2rem;">Planner Organizer</h1>
            <h3 style="color: #5A6A85; margin-bottom: 2rem;">Sistema de Gestão para Personal Organizers</h3>
            
            <p style="margin-bottom: 1.5rem; color: #495057;">
                Acesse o sistema para gerenciar suas propostas, clientes, 
                produtos e finanças de maneira simples e eficiente.
            </p>
            
            <ul style="list-style-type: none; padding-left: 0; margin-bottom: 2rem;">
                <li style="margin-bottom: 0.5rem; color: #495057;">✅ Controle de propostas</li>
                <li style="margin-bottom: 0.5rem; color: #495057;">✅ Gestão de clientes</li>
                <li style="margin-bottom: 0.5rem; color: #495057;">✅ Finanças e receitas</li>
                <li style="margin-bottom: 0.5rem; color: #495057;">✅ Relatórios detalhados</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        tab1, tab2 = st.tabs(["Login", "Registrar"])
        
        with tab1:
            # Login tradicional com email/senha
            authenticator, name, authentication_status, username = criar_componente_login()
            
            # Divisor com "ou"
            st.markdown("""
            <div style="text-align: center; margin: 1.5rem 0; position: relative;">
                <hr style="margin: 0; border: none; height: 1px; background-color: #E0E0E0;">
                <span style="position: absolute; top: -10px; left: 50%; transform: translateX(-50%); 
                       background-color: white; padding: 0 10px; color: #5A6A85; font-size: 0.9rem;">
                    ou continuar com
                </span>
            </div>
            """, unsafe_allow_html=True)
            
            # Botões para login social
            col_google, col_facebook = st.columns(2)
            
            with col_google:
                st.markdown("""
                <button style="width: 100%; background-color: white; border: 1px solid #E0E0E0; 
                               border-radius: 4px; padding: 8px 0; display: flex; align-items: center; 
                               justify-content: center; cursor: pointer; transition: all 0.2s ease;">
                    <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" 
                         style="width: 18px; height: 18px; margin-right: 8px;">
                    Google
                </button>
                """, unsafe_allow_html=True)
            
            with col_facebook:
                st.markdown("""
                <button style="width: 100%; background-color: #3b5998; border: none; color: white;
                               border-radius: 4px; padding: 8px 0; display: flex; align-items: center; 
                               justify-content: center; cursor: pointer; transition: all 0.2s ease;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="white" 
                         style="margin-right: 8px;">
                        <path d="M12 0c-6.627 0-12 5.373-12 12s5.373 12 12 12 12-5.373 12-12-5.373-12-12-12zm3 8h-1.35c-.538 0-.65.221-.65.778v1.222h2l-.209 2h-1.791v7h-3v-7h-2v-2h2v-2.308c0-1.769.931-2.692 3.029-2.692h1.971v3z"/>
                    </svg>
                    Facebook
                </button>
                """, unsafe_allow_html=True)
            
            # Adicionar links para recuperação de senha
            st.markdown("""
            <div style="text-align: center; margin-top: 1rem;">
                <a href="#" style="color: #1E88E5; text-decoration: none; font-size: 0.9rem;">
                    Esqueceu sua senha?
                </a>
            </div>
            """, unsafe_allow_html=True)
            
            # Nota informativa sobre o login social
            st.info("Os botões de login social estão em implementação e serão ativados em breve.")
        
        with tab2:
            criar_componente_registro()
    
    return authentication_status

# Para usar este módulo, importe-o e use a função criar_pagina_login() 
# O resultado será True se o usuário estiver autenticado