import streamlit as st
import os
import json
import requests
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Login - Planner Organizer",
    page_icon="🔒",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Inicializar sessão
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user" not in st.session_state:
    st.session_state.user = None

# Título principal
st.title("Login - Planner Organizer")

# Se não estiver autenticado, mostrar tela de login
if not st.session_state.authenticated:
    # Adicionar CSS para melhorar a aparência
    st.markdown("""
    <style>
        .login-box {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .login-button {
            background-color: #4285F4;
            color: white;
            padding: 10px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            width: 100%;
            font-size: 16px;
            margin-top: 10px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Formulário de login padrão (sempre funciona)
    with st.form("login_form"):
        st.subheader("Login com email e senha")
        email = st.text_input("Email")
        password = st.text_input("Senha", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("Entrar", use_container_width=True)
        with col2:
            demo = st.form_submit_button("Modo Demo", use_container_width=True)
        
        if submit:
            # Modo simplificado: aceitar qualquer senha não vazia para qualquer email
            if email and password:
                st.session_state.authenticated = True
                st.session_state.user = {
                    "email": email,
                    "auth_method": "email",
                    "login_time": datetime.now().isoformat()
                }
                st.success(f"Login bem-sucedido com {email}")
                st.rerun()
            else:
                st.error("Por favor preencha email e senha")
        
        if demo:
            # Modo demo para testes
            st.session_state.authenticated = True
            st.session_state.user = {
                "email": "demo@example.com",
                "name": "Usuário Demo",
                "auth_method": "demo",
                "demo": True,
                "login_time": datetime.now().isoformat()
            }
            st.success("Modo demonstração ativado!")
            st.rerun()
    
    # Separador
    st.markdown("<p style='text-align:center; margin: 20px 0;'>ou</p>", unsafe_allow_html=True)
    
    # Login com Google (mockup funcional sem pop-up)
    if st.button("Continuar com Google", key="google_btn", use_container_width=True):
        st.session_state.authenticated = True
        st.session_state.user = {
            "email": "usuario@gmail.com",
            "name": "Usuário Google",
            "auth_method": "google",
            "profile_pic": "https://lh3.googleusercontent.com/a/default-user",
            "login_time": datetime.now().isoformat()
        }
        st.success("Login com Google bem-sucedido!")
        st.rerun()
    
    # Login com Facebook (mockup funcional sem pop-up)
    if st.button("Continuar com Facebook", key="facebook_btn", type="primary", use_container_width=True):
        st.session_state.authenticated = True
        st.session_state.user = {
            "email": "usuario@facebook.com",
            "name": "Usuário Facebook",
            "auth_method": "facebook",
            "profile_pic": "https://graph.facebook.com/default-user/picture",
            "login_time": datetime.now().isoformat()
        }
        st.success("Login com Facebook bem-sucedido!")
        st.rerun()
    
    # Informação de uso
    st.markdown("""
    <div style="margin-top: 30px; text-align: center; color: #666;">
        <p>Este é um ambiente de demonstração para fins de desenvolvimento. Não utilize senhas reais.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Seção de planos
    st.markdown("""
    <div style="margin-top: 50px;">
        <h2 style="text-align: center; margin-bottom: 30px;">Planos e Preços</h2>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="padding: 20px; border: 1px solid #ddd; border-radius: 10px; height: 100%;">
            <h3 style="text-align: center; color: #333;">Mensal</h3>
            <h2 style="text-align: center; color: #007bff; margin: 10px 0;">R$ 9,70</h2>
            <p style="text-align: center; color: #666; margin-bottom: 20px;">por mês</p>
            <ul>
                <li>Acesso a todas as funcionalidades</li>
                <li>Suporte via email</li>
                <li>7 dias de teste grátis</li>
                <li>Cancele quando quiser</li>
            </ul>
            <div style="text-align: center; margin-top: 20px;">
                <button style="background-color: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">Assinar Plano</button>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="padding: 20px; border: 2px solid #007bff; border-radius: 10px; height: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <div style="background-color: #007bff; color: white; margin: -20px -20px 20px -20px; padding: 10px; text-align: center; border-radius: 8px 8px 0 0;">
                <span>Mais Popular</span>
            </div>
            <h3 style="text-align: center; color: #333;">Anual</h3>
            <h2 style="text-align: center; color: #007bff; margin: 10px 0;">R$ 97,00</h2>
            <p style="text-align: center; color: #666; margin-bottom: 20px;">por ano (economize 17%)</p>
            <ul>
                <li>Acesso a todas as funcionalidades</li>
                <li>Suporte prioritário</li>
                <li>7 dias de teste grátis</li>
                <li>Cancele quando quiser</li>
                <li>Economia de 2 meses no ano</li>
            </ul>
            <div style="text-align: center; margin-top: 20px;">
                <button style="background-color: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-weight: bold;">Assinar Plano</button>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="padding: 20px; border: 1px solid #ddd; border-radius: 10px; height: 100%;">
            <h3 style="text-align: center; color: #333;">Vitalício</h3>
            <h2 style="text-align: center; color: #007bff; margin: 10px 0;">R$ 247,00</h2>
            <p style="text-align: center; color: #666; margin-bottom: 20px;">pagamento único</p>
            <ul>
                <li>Acesso a todas as funcionalidades</li>
                <li>Suporte premium</li>
                <li>Acesso vitalício sem mensalidades</li>
                <li>Acesso a novas funcionalidades</li>
                <li>Prioridade nas atualizações</li>
            </ul>
            <div style="text-align: center; margin-top: 20px;">
                <button style="background-color: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">Comprar Acesso</button>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Rodapé
    st.markdown("""
    <div style="margin-top: 50px; text-align: center; color: #666; font-size: 0.8rem;">
        <p>© 2025 Planner Organizer. Todos os direitos reservados.</p>
        <p>Dúvidas? Entre em contato: contato@plannerorganizer.com.br</p>
    </div>
    """, unsafe_allow_html=True)

# Se estiver autenticado, mostrar área de usuário
else:
    # Exibir mensagem de boas-vindas
    st.success(f"Login realizado com sucesso como {st.session_state.user.get('email')}")
    
    # Exibir informações do usuário
    st.write("### Dados do usuário")
    st.json(st.session_state.user)
    
    # Botão para entrar no sistema
    if st.button("Acessar o Sistema", key="btn_access_system"):
        st.switch_page("app.py")
    
    # Botão para sair
    if st.button("Sair", key="btn_logout"):
        st.session_state.authenticated = False
        st.session_state.user = None
        st.rerun()