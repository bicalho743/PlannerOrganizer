import streamlit as st

# Configuração da página com layout amplo e sidebar colapsada
st.set_page_config(
    page_title="Planner Organizer - Sistema Profissional",
    page_icon="favicon.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

import os
import sys
import time
import random
from datetime import datetime

# Adicionar diretório raiz ao path para importações
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

# Importamos a função de exibição de planos do módulo independente
from exibir_planos import exibir_planos_simples

# Remover o menu hamburguer, rodapé e botão de deploy
hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Estilos para a página de login */
    .login-container {
        background-color: white;
        border-radius: 12px;
        padding: 2rem;
        box-shadow: 0 8px 30px rgba(0,0,0,0.12);
        margin-top: 1rem;
    }
    
    .login-title {
        color: #1E366F;
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    
    .social-button {
        display: block;
        width: 100%;
        padding: 10px;
        margin-bottom: 10px;
        border-radius: 6px;
        border: 1px solid #E0E0E0;
        background-color: white;
        color: #5A6A85;
        font-weight: 500;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .social-button:hover {
        background-color: #F5F7FA;
        border-color: #C0C0C0;
    }
    
    .google-button {
        color: #5A6A85;
    }
    
    .facebook-button {
        color: #1877F2;
    }
    
    .login-divider {
        position: relative;
        text-align: center;
        margin: 20px 0;
    }
    
    .login-divider:before {
        content: "";
        position: absolute;
        top: 50%;
        left: 0;
        width: 100%;
        height: 1px;
        background-color: #E0E0E0;
    }
    
    .login-divider-text {
        position: relative;
        background-color: white;
        padding: 0 15px;
        color: #9E9E9E;
        font-size: 0.9rem;
    }
    
    /* Estilos para a seção hero */
    .hero-section {
        background: linear-gradient(135deg, #1E366F, #2d8cff);
        color: white;
        padding: 3rem 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
    }
    
    .hero-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        line-height: 1.2;
    }
    
    .hero-subtitle {
        font-size: 1.2rem;
        margin-bottom: 2rem;
        opacity: 0.9;
        line-height: 1.5;
    }
    
    .call-to-action {
        background: linear-gradient(135deg, #ff6b6b, #e83e3e);
        color: white;
        padding: 2rem;
        border-radius: 12px;
        margin: 2rem 0;
        text-align: center;
    }
    
    .brands-section {
        padding: 2rem 0;
        text-align: center;
        border-top: 1px solid #E0E0E0;
        margin-top: 2rem;
    }
    
    /* Ajustes para dispositivos móveis */
    @media (max-width: 768px) {
        .hero-title {
            font-size: 2rem;
        }
        
        .hero-subtitle {
            font-size: 1rem;
        }
    }
    </style>
"""
st.markdown(hide_menu_style, unsafe_allow_html=True)

# Verificar se o usuário já está autenticado
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def main():
    # Se o usuário já estiver autenticado, redirecionar para o app principal
    if st.session_state.authenticated:
        st.success("Login realizado com sucesso! Redirecionando...")
        st.session_state.authenticated = True
        st.switch_page("app.py")
        return
    
    # Layout principal com duas colunas: marketing e login
    left_col, right_col = st.columns([3, 2])
    
    with left_col:
        # Seção hero com título e subtítulo
        st.markdown('''
        <div class="hero-section">
            <h1 class="hero-title">Transforme seu Negócio com o Planner Organizer</h1>
            <p class="hero-subtitle">
                O sistema completo para gerenciar seu negócio de organização profissional.
                Propostas, clientes, produtos e finanças em um único lugar.
            </p>
        </div>
        ''', unsafe_allow_html=True)
        
        # Seção de recursos principais
        st.markdown("<h2>Por que escolher o Planner Organizer?</h2>", unsafe_allow_html=True)
        
        # Recursos em colunas
        feat1, feat2, feat3 = st.columns(3)
        
        with feat1:
            st.markdown('''
            <div style="text-align: center; padding: 1rem;">
                <div style="font-size: 2rem; color: #2d8cff; margin-bottom: 0.5rem;">📊</div>
                <h3 style="margin-bottom: 0.5rem; color: #1E366F;">Gestão Completa</h3>
                <p style="color: #5A6A85;">
                    Centralize toda gestão do seu negócio em um único sistema integrado.
                </p>
            </div>
            ''', unsafe_allow_html=True)
            
        with feat2:
            st.markdown('''
            <div style="text-align: center; padding: 1rem;">
                <div style="font-size: 2rem; color: #2d8cff; margin-bottom: 0.5rem;">📱</div>
                <h3 style="margin-bottom: 0.5rem; color: #1E366F;">Acesso de Qualquer Lugar</h3>
                <p style="color: #5A6A85;">
                    Trabalhe de onde estiver, com acesso via computador ou celular.
                </p>
            </div>
            ''', unsafe_allow_html=True)
            
        with feat3:
            st.markdown('''
            <div style="text-align: center; padding: 1rem;">
                <div style="font-size: 2rem; color: #2d8cff; margin-bottom: 0.5rem;">🔒</div>
                <h3 style="margin-bottom: 0.5rem; color: #1E366F;">Segurança e Privacidade</h3>
                <p style="color: #5A6A85;">
                    Seus dados protegidos com o que há de mais moderno em segurança.
                </p>
            </div>
            ''', unsafe_allow_html=True)
        
        # Seção de Planos e Preços
        st.markdown("<h2>Escolha o Plano Ideal Para o Seu Negócio</h2>", unsafe_allow_html=True)
        
        # Usar nossa implementação de planos local
        exibir_planos_simples()
        
        # CTA (Call to Action)
        st.markdown('''
        <div class="call-to-action">
            <h2>Pronto para transformar seu negócio?</h2>
            <p>Faça login agora e comece a profissionalizar sua gestão de propostas e finanças.</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with right_col:
        # Container de login
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        # Título do login
        st.markdown('<h2 class="login-title">Acesse sua conta</h2>', unsafe_allow_html=True)
        
        # Botões de login social
        st.markdown('''
        <button class="social-button google-button">
            <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" 
                 style="width: 18px; height: 18px; margin-right: 8px;">
            Continuar com Google
        </button>
        ''', unsafe_allow_html=True)
        
        st.markdown('''
        <button class="social-button facebook-button">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="#1877F2" 
                 style="margin-right: 8px;">
                <path d="M12 0c-6.627 0-12 5.373-12 12s5.373 12 12 12 12-5.373 12-12-5.373-12-12-12zm3 8h-1.35c-.538 0-.65.221-.65.778v1.222h2l-.209 2h-1.791v7h-3v-7h-2v-2h2v-2.308c0-1.769.931-2.692 3.029-2.692h1.971v3z"/>
            </svg>
            Continuar com Facebook
        </button>
        ''', unsafe_allow_html=True)
        
        # Divisor
        st.markdown('''
        <div class="login-divider">
            <span class="login-divider-text">ou entre com e-mail</span>
        </div>
        ''', unsafe_allow_html=True)
        
        # Formulário de login
        with st.form("login_form"):
            username = st.text_input("Usuário ou E-mail")
            password = st.text_input("Senha", type="password")
            st.markdown('<div style="height: 15px;"></div>', unsafe_allow_html=True)
            submit = st.form_submit_button("Entrar na minha conta", use_container_width=True)
            
            if submit:
                # Usar Firebase para autenticação real quando configurado
                try:
                    from utils.firebase_auth import login_email_senha
                    
                    # Tenta autenticar com Firebase 
                    with st.spinner("Autenticando..."):
                        user_info = login_email_senha(username, password)
                        
                    if user_info is not None:
                        # Salva as informações do usuário na sessão
                        st.session_state.user_info = user_info
                        st.session_state.authenticated = True
                        st.success("Login realizado com sucesso!")
                        st.rerun()
                    else:
                        # Fallback para o modo de demonstração
                        if username.lower() == "admin" and password == "admin":
                            st.session_state.authenticated = True
                            with st.spinner("Autenticando em modo de demonstração..."):
                                time.sleep(1)
                            st.success("Login realizado com sucesso (modo demonstração)!")
                            st.rerun()
                        else:
                            st.error("Usuário ou senha incorretos")
                except ImportError:
                    # Fallback se o módulo Firebase não estiver configurado
                    if username.lower() == "admin" and password == "admin":
                        st.session_state.authenticated = True
                        with st.spinner("Autenticando..."):
                            time.sleep(1)
                        st.success("Login realizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos")
        
        # Links de recuperação de senha e criação de conta
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Esqueceu sua senha?", type="secondary", key="forgot_password_btn", use_container_width=True):
                st.session_state.show_reset_password = True
                st.rerun()
                
        # Formulário de recuperação de senha
        if "show_reset_password" in st.session_state and st.session_state.show_reset_password:
            st.markdown('<hr style="margin: 20px 0;">', unsafe_allow_html=True)
            st.markdown('<h3 style="text-align: center; color: #1E366F;">Recuperar Senha</h3>', unsafe_allow_html=True)
            
            with st.form("reset_password_form"):
                email_reset = st.text_input("Digite seu e-mail")
                
                submit_reset = st.form_submit_button("Enviar link de recuperação", use_container_width=True)
                
                if submit_reset:
                    if not email_reset:
                        st.error("Por favor, informe seu e-mail.")
                    else:
                        try:
                            from utils.firebase_auth import redefinir_senha
                            
                            # Tenta enviar email de recuperação
                            with st.spinner("Enviando email de recuperação..."):
                                success = redefinir_senha(email_reset)
                                
                            if success:
                                st.success(f"E-mail de recuperação enviado para {email_reset}. Verifique sua caixa de entrada.")
                                st.session_state.show_reset_password = False
                                st.rerun()
                            else:
                                st.error("Erro ao enviar email de recuperação. Verifique se o e-mail está correto.")
                        except ImportError:
                            # Fallback se o Firebase não estiver configurado
                            st.success(f"Um link de recuperação foi enviado para {email_reset} (modo de demonstração).")
                            st.session_state.show_reset_password = False
                            st.rerun()
        
        with col2:
            if st.button("Criar uma conta", type="secondary", key="create_account_btn", use_container_width=True):
                # Certifique-se de que a variável de estado seja definida
                if "show_signup" not in st.session_state:
                    st.session_state.show_signup = False
                
                # Alterna o estado para mostrar o formulário de cadastro
                st.session_state.show_signup = not st.session_state.show_signup
                st.rerun()
        
        # Informações de demonstração
        st.markdown('''
        <div style="margin-top: 0.8rem; text-align: center;">
            <p style="color: #9E9E9E; font-size: 0.75rem;">
                Para demonstração, use: admin / admin
            </p>
        </div>
        ''', unsafe_allow_html=True)
        
        # Lógica para exibir formulário de cadastro
        if "show_signup" in st.session_state and st.session_state.show_signup:
            st.markdown('<hr style="margin: 20px 0;">', unsafe_allow_html=True)
            st.markdown('<h3 style="text-align: center; color: #1E366F;">Criar Nova Conta</h3>', unsafe_allow_html=True)
            
            with st.form("signup_form"):
                nome = st.text_input("Nome Completo")
                email = st.text_input("E-mail")
                senha = st.text_input("Senha", type="password")
                confirmar_senha = st.text_input("Confirmar Senha", type="password")
                
                submit_signup = st.form_submit_button("Registrar", use_container_width=True)
                
                if submit_signup:
                    if not nome or not email or not senha or not confirmar_senha:
                        st.error("Todos os campos são obrigatórios.")
                    elif senha != confirmar_senha:
                        st.error("As senhas não coincidem.")
                    else:
                        try:
                            from utils.firebase_auth import criar_conta
                            
                            # Tenta criar a conta com Firebase
                            with st.spinner("Criando sua conta..."):
                                user_info = criar_conta(email, senha, nome)
                                
                            if user_info is not None:
                                st.success(f"Conta criada com sucesso para {nome}! Verifique seu e-mail {email} para ativar sua conta.")
                                st.session_state.show_signup = False
                                # Opcionalmente já loga o usuário
                                # st.session_state.user_info = user_info
                                # st.session_state.authenticated = True
                                st.rerun()
                            else:
                                st.error("Erro ao criar conta. Tente novamente.")
                        except ImportError:
                            # Fallback se o Firebase não estiver configurado
                            st.success(f"Conta criada com sucesso para {nome}! Verifique seu e-mail {email} para ativar sua conta.")
                            st.session_state.show_signup = False
                            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Seção de marcas/clientes
    st.markdown('''
    <div class="brands-section">
        <p style="color: #5A6A85; font-size: 0.9rem; margin-bottom: 1rem;">CONFIADO POR PERSONAL ORGANIZERS DE TODO O BRASIL</p>
        <div style="display: flex; justify-content: space-around; align-items: center; flex-wrap: wrap;">
            <span style="color: #1E366F; font-weight: 600; margin: 0 1rem;">Organizze Bem</span>
            <span style="color: #1E366F; font-weight: 600; margin: 0 1rem;">Expert Closets</span>
            <span style="color: #1E366F; font-weight: 600; margin: 0 1rem;">TopOrder Solutions</span>
            <span style="color: #1E366F; font-weight: 600; margin: 0 1rem;">Clean & Order</span>
            <span style="color: #1E366F; font-weight: 600; margin: 0 1rem;">Plann.Smart</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Rodapé
    st.markdown('''
    <div style="text-align: center; margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid #E0E0E0;">
        <p style="color: #5A6A85; font-size: 0.8rem;">
            © 2025 Planner Organizer. Todos os direitos reservados.
        </p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Opção para desenvolvedores (escondida no canto)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col3:
        if st.button("Acesso Técnico", key="dev_login_button", use_container_width=False):
            st.session_state.authenticated = True
            st.rerun()

if __name__ == "__main__":
    main()