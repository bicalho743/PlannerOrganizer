import os
import sys
import streamlit as st
import logging
import pandas as pd
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Corrigir o problema de adaptação de tipos numpy.int64 para PostgreSQL
try:
    from utils.type_conversion_fix import fix_numpy_int64_bug
    success = fix_numpy_int64_bug()
    if success:
        logger.info("Adaptadores para numpy.int* registrados com sucesso")
    else:
        logger.warning("Não foi possível registrar adaptadores para numpy.int*")
except Exception as e:
    logger.error(f"Erro ao importar/executar fix_numpy_int64_bug: {str(e)}")

# Adicionar diretório raiz ao path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)
    logger.info(f"Adicionado {project_root} ao sys.path")

from utils.database import Database
from utils.planos import mostrar_planos  # Importando o módulo de planos

# Importar módulo de autenticação Firebase (pode ser comentado para desabilitar temporariamente)
try:
    from utils.firebase_auth import firebase_auth
except ImportError:
    # Fallback para sistemas sem autenticação Firebase
    firebase_auth = None
    st.warning("Módulo Firebase Auth não encontrado. Usando autenticação padrão.")

# Inicialização dos estados da sessão
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Estado para controlar a página de login
if 'login_page' not in st.session_state:
    st.session_state.login_page = "login"  # Valores possíveis: login, registrar, recuperar_senha

# Verificar estado para mostrar termos de uso
if "show_termos" not in st.session_state:
    st.session_state.show_termos = False

# Verificar estado para mostrar política de privacidade
if "show_politica" not in st.session_state:
    st.session_state.show_politica = False

# Configuração inicial da página
st.set_page_config(
    page_title="Planner Organizer - Sistema Profissional",
    page_icon="favicon.png",
    layout="wide",
    initial_sidebar_state="auto"
)

# Importar e aplicar correção para problemas de carregamento de módulos JavaScript
try:
    from utils.render_fix import inject_render_compatibility_fix
    inject_render_compatibility_fix()
    logger.info("Injetado script de compatibilidade para Render")
except Exception as e:
    logger.error(f"Erro ao injetar script de compatibilidade: {e}")

# Função para mostrar termos de uso
def show_termos():
    """Mostra a página de termos de uso"""
    st.session_state.show_termos = True
    st.rerun()

# Função para mostrar política de privacidade
def show_politica():
    """Mostra a página de política de privacidade"""
    st.session_state.show_politica = True
    st.rerun()

# Mostrar termos de uso se solicitado
if st.session_state.show_termos:
    try:
        from pages.termos_de_uso import show
        show()
        st.stop()
    except ImportError as e:
        st.error(f"Não foi possível carregar os termos de uso: {e}")
        st.session_state.show_termos = False

# Mostrar política de privacidade se solicitado
if st.session_state.show_politica:
    try:
        from pages.politica_privacidade import show
        show()
        st.stop()
    except ImportError as e:
        st.error(f"Não foi possível carregar a política de privacidade: {e}")
        st.session_state.show_politica = False

# Inicialização da autenticação in-app
if not st.session_state.authenticated:
    # Ocultar completamente a barra lateral na página de login
    st.markdown("""
    <style>
    [data-testid="collapsedControl"] {display: none;}
    section[data-testid="stSidebar"] {display: none;}
    </style>
    """, unsafe_allow_html=True)
    
    # Verificar se estamos mostrando termos de uso ou política de privacidade
    query_params = st.query_params
    
    # Verificar os parâmetros de consulta para os documentos legais
    if "show_termos" in query_params and query_params["show_termos"] == "true":
        try:
            from pages.termos_de_uso import show
            show()
            st.stop()  # Parar o fluxo após mostrar a página
        except ImportError as e:
            st.error(f"Não foi possível carregar os termos de uso: {e}")
    
    elif "show_politica" in query_params and query_params["show_politica"] == "true":
        try:
            from pages.politica_privacidade import show
            show()
            st.stop()  # Parar o fluxo após mostrar a página
        except ImportError as e:
            st.error(f"Não foi possível carregar a política de privacidade: {e}")
    
    # Verificar se o usuário está tentando registrar ou recuperar senha
    if st.session_state.login_page == "registrar":
        try:
            # Tentar importar e mostrar a página de registro
            from pages.registrar import show
            show()
            st.stop()  # Parar o fluxo após mostrar a página
        except ImportError as e:
            st.error(f"Não foi possível carregar o módulo de registro: {e}")
            # Resetar para página de login
            st.session_state.login_page = "login"
            st.rerun()
    
    elif st.session_state.login_page == "recuperar_senha":
        try:
            # Tentar importar e mostrar a página de recuperação de senha
            from pages.recuperar_senha import show
            show()
            st.stop()  # Parar o fluxo após mostrar a página
        except ImportError as e:
            st.error(f"Não foi possível carregar o módulo de recuperação de senha: {e}")
            # Resetar para página de login
            st.session_state.login_page = "login"
            st.rerun()
    
    # CSS personalizado para a landing page
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    
    body {
        font-family: 'Poppins', sans-serif;
        background: linear-gradient(135deg, #f9fafc, #eef5ff);
        color: #333;
    }
    
    h1, h2, h3, h4 {
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        color: #2d8cff;
    }
    
    .main-header {
        color: #2d8cff;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        line-height: 1.2;
        margin-top: 0 !important;
        padding-top: 0 !important;
        text-shadow: 0px 2px 3px rgba(0,0,0,0.1);
    }
    
    .subheader {
        color: #5A6A85;
        font-size: 1.2rem;
        font-weight: 400;
        margin-bottom: 1rem;
    }
    
    /* Reduzir espaçamento no topo da página - mais agressivamente */
    .block-container {
        padding-top: 0 !important;
        max-width: 100% !important;
    }
    
    /* Remove espaços em branco no topo da aplicação */
    .st-emotion-cache-z5fcl4, .st-emotion-cache-ue6h4q, .st-emotion-cache-1kyxreq {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Remove cabeçalho do Streamlit completamente */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    
    /* Container de contexto principal sem padding */
    .st-emotion-cache-1wmy9hl {
        padding-top: 0 !important;
    }
    
    .feature-card {
        background-color: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 8px 16px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
        border-top: 4px solid #2d8cff;
        transition: all 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.12);
        border-top: 4px solid #ff6b6b;
    }
    
    .feature-icon {
        font-size: 2.5rem;
        color: #2d8cff;
        margin-bottom: 1rem;
    }
    
    .feature-title {
        font-weight: 600;
        color: #2d8cff;
        margin-bottom: 0.5rem;
        font-size: 1.1rem;
    }
    
    .feature-description {
        color: #5A6A85;
        font-size: 0.95rem;
        line-height: 1.5;
    }
    
    .testimonial-card {
        background: linear-gradient(135deg, #E3F2FD, #bbdefb);
        padding: 1.8rem;
        border-radius: 12px;
        position: relative;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 16px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
    }
    
    .testimonial-card:hover {
        transform: scale(1.02);
        box-shadow: 0 12px 24px rgba(0,0,0,0.12);
    }
    
    .testimonial-text {
        font-style: italic;
        color: #1E366F;
        margin-bottom: 1rem;
        font-size: 1.05rem;
        line-height: 1.6;
    }
    
    .testimonial-author {
        font-weight: 600;
        color: #1976D2;
        font-size: 1.05rem;
    }
    
    .login-container {
        background: linear-gradient(135deg, white, #f5f9ff);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.8);
        margin-top: 0;
    }
    
    .login-header {
        text-align: center;
        margin-bottom: 1rem;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    .social-button {
        width: 100%;
        margin-bottom: 1rem;
        border-radius: 12px;
        padding: 0.7rem 1.2rem;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        font-weight: 500;
        transition: all 0.3s ease;
        font-size: 1rem;
    }
    
    .google-button {
        background-color: white;
        border: 1px solid #E0E0E0;
        color: #5A6A85;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05);
    }
    
    .google-button:hover {
        background-color: #f5f5f5;
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.08);
    }
    
    .facebook-button {
        background-color: #3b5998;
        border: none;
        color: white;
        box-shadow: 0 4px 8px rgba(59,89,152,0.3);
    }
    
    .facebook-button:hover {
        background-color: #344e86;
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(59,89,152,0.4);
    }
    
    .login-divider {
        text-align: center;
        position: relative;
        margin: 1.8rem 0;
    }
    
    .login-divider:before {
        content: "";
        position: absolute;
        top: 50%;
        left: 0;
        right: 0;
        height: 1px;
        background-color: #E0E0E0;
        z-index: -1;
    }
    
    .login-divider-text {
        background: linear-gradient(135deg, white, #f5f9ff);
        padding: 0 15px;
        color: #5A6A85;
        font-size: 0.95rem;
    }
    
    .benefits-list li {
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
    }
    
    .benefits-list .check-icon {
        color: #4CAF50;
        margin-right: 0.8rem;
        font-weight: bold;
        font-size: 1.2rem;
    }
    
    .call-to-action {
        background: linear-gradient(135deg, #2d8cff, #0063cc);
        padding: 2.5rem;
        border-radius: 16px;
        color: white;
        text-align: center;
        margin-top: 2.5rem;
        box-shadow: 0 12px 30px rgba(45,140,255,0.3);
        transform: rotate(0);
        transition: all 0.3s ease;
    }
    
    .call-to-action:hover {
        transform: scale(1.02);
        box-shadow: 0 15px 35px rgba(45,140,255,0.4);
    }
    
    .brands-section {
        text-align: center;
        margin-top: 3.5rem;
        padding: 2rem;
        background: linear-gradient(135deg, #f5f7fa, #e9f2ff);
        border-radius: 16px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.05);
    }
    
    .stat-card {
        background: linear-gradient(135deg, white, #f5f9ff);
        border-radius: 12px;
        padding: 1.8rem;
        box-shadow: 0 8px 16px rgba(0,0,0,0.08);
        text-align: center;
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
        border-bottom: 4px solid transparent;
    }
    
    .stat-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.12);
    }
    
    .stat-card:nth-child(1) {
        border-bottom-color: #4CAF50;
    }
    
    .stat-card:nth-child(2) {
        border-bottom-color: #ff6b6b;
    }
    
    .stat-card:nth-child(3) {
        border-bottom-color: #ffbb33;
    }
    
    .stat-number {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #2d8cff, #0063cc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.8rem;
    }
    
    .stat-label {
        color: #5A6A85;
        font-size: 1rem;
        font-weight: 500;
    }
    
    /* Estilo para os campos de formulário */
    .stTextInput > div > div > input {
        border-radius: 10px !important;
        padding: 0.7rem 1rem !important;
        font-size: 1rem !important;
        border: 1px solid #E0E0E0 !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #2d8cff !important;
        box-shadow: 0 0 0 3px rgba(45,140,255,0.2) !important;
    }
    
    /* Estilo para o botão de enviar */
    .stButton > button {
        background: linear-gradient(135deg, #2d8cff, #0063cc) !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 0.7rem 1.2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        border: none !important;
        box-shadow: 0 4px 10px rgba(45,140,255,0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #0063cc, #004a99) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 15px rgba(45,140,255,0.4) !important;
    }
    
    /* Removendo elementos da interface Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)
    
    # Layout principal com duas colunas
    left_col, right_col = st.columns([3, 2])
    
    with left_col:
        # Cabeçalho principal
        st.markdown('<h1 class="main-header">Planner Organizer</h1>', unsafe_allow_html=True)
        st.markdown('<p class="subheader">Sistema Profissional para Personal Organizers</p>', unsafe_allow_html=True)
        
        # Banner com estatísticas
        stats_col1, stats_col2, stats_col3 = st.columns(3)
        
        with stats_col1:
            st.markdown('''
            <div class="stat-card">
                <div class="stat-number">+300%</div>
                <div class="stat-label">Aumento na produtividade</div>
            </div>
            ''', unsafe_allow_html=True)
            
        with stats_col2:
            st.markdown('''
            <div class="stat-card">
                <div class="stat-number">-25%</div>
                <div class="stat-label">Redução de retrabalho</div>
            </div>
            ''', unsafe_allow_html=True)
            
        with stats_col3:
            st.markdown('''
            <div class="stat-card">
                <div class="stat-number">+45%</div>
                <div class="stat-label">Aumento no faturamento</div>
            </div>
            ''', unsafe_allow_html=True)
        
        # Benefícios principais
        st.markdown("<h3>Por que escolher o Planner Organizer?</h3>", unsafe_allow_html=True)
        
        benefits_col1, benefits_col2 = st.columns(2)
        
        with benefits_col1:
            st.markdown('''
            <div class="feature-card">
                <div class="feature-title">📊 Gestão Completa de Propostas</div>
                <div class="feature-description">
                    Controle todo o ciclo de vida das suas propostas em um único local, desde a elaboração até a finalização.
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            st.markdown('''
            <div class="feature-card">
                <div class="feature-title">📱 Acesso de Qualquer Lugar</div>
                <div class="feature-description">
                    Sistema web responsivo que pode ser acessado de qualquer dispositivo, a qualquer momento.
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
        with benefits_col2:
            st.markdown('''
            <div class="feature-card">
                <div class="feature-title">💰 Controle Financeiro</div>
                <div class="feature-description">
                    Gerencie receitas, despesas e comissões de forma automatizada e integrada com suas propostas.
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            st.markdown('''
            <div class="feature-card">
                <div class="feature-title">📄 Relatórios Profissionais</div>
                <div class="feature-description">
                    Gere relatórios personalizados para clientes e para controle interno da sua operação.
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        # Depoimentos de clientes
        st.markdown("<h3>O que nossos clientes dizem</h3>", unsafe_allow_html=True)
        
        testimonial_col1, testimonial_col2 = st.columns(2)
        
        with testimonial_col1:
            st.markdown('''
            <div class="testimonial-card">
                <div class="testimonial-text">
                    "O Planner Organizer transformou meu negócio! Consigo gerenciar todas as minhas propostas, 
                    clientes e finanças em um só lugar com facilidade e profissionalismo."
                </div>
                <div class="testimonial-author">
                    — Ana Paula, Personal Organizer
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
        with testimonial_col2:
            st.markdown('''
            <div class="testimonial-card">
                <div class="testimonial-text">
                    "Meu faturamento aumentou 45% depois que comecei a usar o sistema. A gestão de propostas 
                    e o controle financeiro me ajudaram a profissionalizar meu negócio."
                </div>
                <div class="testimonial-author">
                    — Carlos Eduardo, Organizador Profissional
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
        # Seção de Planos e Preços
        st.markdown("<h2>Escolha o Plano Ideal Para o Seu Negócio</h2>", unsafe_allow_html=True)
        
        # Mostrar os planos com os parâmetros otimizados para landing page
        # Usando formato com espaço reduzido e sem a seção de benefícios duplicada
        mostrar_planos(
            com_titulo=False,  # False porque já temos um título acima
            com_prova_social=False,  # False para layout mais compacto
            com_teste_gratis=False,  # False para não duplicar com o CTA abaixo
            com_destaque_plano_medio=True,  # True para destacar o plano anual
            stripe_ready=True,  # True para botões prontos para Stripe
            espacamento_reduzido=True  # True para reduzir o espaçamento
        )
        
        # CTA (Call to Action)
        st.markdown('''
        <div class="call-to-action">
            <h2>Pronto para transformar seu negócio?</h2>
            <p>Faça login agora e comece a profissionalizar sua gestão de propostas e finanças.</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with right_col:
        # Container de login sem espaçamento
        st.markdown('<div class="login-container" style="margin-top: -10px;">', unsafe_allow_html=True)
        
        # Título da seção de login
        st.markdown('''
        <h2 style="text-align: center; color: #1E366F; margin-top: 0; margin-bottom: 25px;">Acesse sua conta</h2>
        ''', unsafe_allow_html=True)
        
        # Login apenas com e-mail (botões sociais removidos conforme solicitado)
        
        # Formulário simples
        st.markdown('''
        <div style="text-align: center; margin-bottom: 20px; color: #5A6A85;">
            Entre com seu e-mail e senha para acessar o sistema
        </div>
        ''', unsafe_allow_html=True)
        
        # Formulário de login
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Senha", type="password")
            st.markdown('<div style="height: 15px;"></div>', unsafe_allow_html=True)
            submit = st.form_submit_button("Entrar na minha conta", use_container_width=True)
            
            if submit:
                # Tentar login pelo Firebase se disponível
                if firebase_auth is not None:
                    with st.spinner("Autenticando..."):
                        result = firebase_auth.login(email, password)
                        if result['success']:
                            st.session_state.authenticated = True
                            st.success("Login realizado com sucesso!")
                            st.rerun()
                        else:
                            # Se falhou no Firebase, tentar com a conta de demo
                            if email.lower() == "admin" and password == "admin":
                                st.session_state.authenticated = True
                                
                                # Criar objeto de usuário para modo de demonstração
                                st.session_state.usuario = {
                                    'email': 'admin@plannerorganizer.com.br',
                                    'nome': 'Administrador',
                                    'telefone': '(11) 98765-4321',
                                    'empresa': 'Planner Organizer',
                                    'role': 'admin'
                                }
                                
                                st.success("Login realizado com sucesso (modo demonstração)!")
                                st.rerun()
                            else:
                                st.error(f"Erro de autenticação: {result['error']}")
                # Fallback para login de demo se o Firebase não estiver disponível
                elif email.lower() == "admin" and password == "admin":
                    st.session_state.authenticated = True
                    
                    # Criar objeto de usuário para modo de demonstração
                    st.session_state.usuario = {
                        'email': 'admin@plannerorganizer.com.br',
                        'nome': 'Administrador',
                        'telefone': '(11) 98765-4321',
                        'empresa': 'Planner Organizer',
                        'role': 'admin'
                    }
                    
                    with st.spinner("Autenticando..."):
                        import time
                        time.sleep(1)
                    st.success("Login realizado com sucesso (modo demonstração)!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos")
        
        # Informação de demonstração
        st.markdown('''
        <div style="margin-top: 0.8rem; text-align: center;">
            <p style="color: #9E9E9E; font-size: 0.75rem;">
                Para demonstração, use: admin / admin
            </p>
        </div>
        ''', unsafe_allow_html=True)
        
        # Botões para navegação
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Esqueceu sua senha?", key="btn_recuperar_senha", use_container_width=True):
                st.session_state.login_page = "recuperar_senha"
                st.rerun()
        with col2:
            if st.button("Criar uma conta", key="btn_criar_conta", use_container_width=True):
                st.session_state.login_page = "registrar"
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Opção para pular login em ambiente de desenvolvimento (apenas para devs)
        footer_container = st.container()
        with footer_container:
            st.markdown('''
            <div style="position: fixed; bottom: 10px; right: 10px; z-index: 999;">
                <details style="background: transparent; border: none; color: #BDBDBD; font-size: 0.7rem;">
                    <summary style="cursor: pointer; outline: none;">Dev</summary>
                    <div style="padding: 10px; background: white; border-radius: 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-top: 5px;">
                        <p style="margin: 0 0 10px 0; font-size: 0.8rem;">Acesso para desenvolvedores</p>
                        <button id="dev-login-button" style="background: #E0E0E0; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-size: 0.8rem;">Pular login</button>
                    </div>
                </details>
            </div>
            ''', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col3:
                if st.button("Acesso Dev", key="dev_login_access", use_container_width=True):
                    st.session_state.authenticated = True
                    
                    # Criar objeto de usuário para modo de desenvolvedor
                    st.session_state.usuario = {
                        'email': 'dev@plannerorganizer.com.br',
                        'nome': 'Desenvolvedor',
                        'telefone': '(11) 99999-9999',
                        'empresa': 'Planner Organizer',
                        'role': 'dev'
                    }
                    
                    st.rerun()
    
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
        
    # Impede a renderização do resto da aplicação
    st.stop()

# A configuração da página já foi definida no início do arquivo
# Não é permitido chamar st.set_page_config() mais de uma vez por app

# Inicialização do banco de dados
if 'db' not in st.session_state:
    try:
        st.session_state.db = Database()
        # Removemos a mensagem de sucesso para manter o visual limpo
    except Exception as e:
        st.error("Erro ao conectar com o banco de dados. O endpoint pode estar desabilitado.")
        st.warning("Se você estiver usando Neon PostgreSQL ou outro banco de dados serverless, você precisa reativar o endpoint.")
        
        # Mostrar informação sobre o DATABASE_URL (sem mostrar credenciais)
        db_url = os.getenv('DATABASE_URL', 'Não definido')
        if db_url:
            # Esconder credenciais na mensagem
            safe_url = db_url.split('@')
            if len(safe_url) > 1:
                host_part = safe_url[1]
                st.info(f"Sua conexão de banco de dados aponta para: ...@{host_part}")
            else:
                st.info("DATABASE_URL está definido, mas não está no formato esperado.")
        else:
            st.info("A variável de ambiente DATABASE_URL não está definida.")
        
        st.error(f"Detalhes do erro: {str(e)}")
        st.stop()

# Carregar CSS customizado do arquivo style.css
with open('.streamlit/style.css', 'r') as f:
    custom_css = f.read()

# Adicionar estilo CSS personalizado para tema profissional
st.markdown(f"""
    <style>
    {custom_css}
    
    /* Estilo específico para a barra lateral */
    section[data-testid="stSidebar"] {{
        background-color: #F9FAFB;
        border-right: 1px solid #E0E0E0;
    }}

    div.block-container {{
        padding-top: 2rem !important;
    }}

    /* Estilo para botões do menu */
    div.stButton > button {{
        width: 100%;
        background-color: #1E88E5 !important;
        color: white !important;
        font-weight: 500;
        text-align: left;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        border-radius: 4px;
        border: none;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        transition: all 0.2s ease;
    }}

    div.stButton > button:hover {{
        background-color: #1976D2 !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        transform: translateY(-1px);
    }}

    /* Container para os botões */
    div.nav-buttons {{
        padding: 1rem;
        margin: 0 -1rem;
    }}
    
    /* Esconde os links nativos do Streamlit na barra lateral */
    section[data-testid="stSidebar"] .element-container:has(svg[xmlns="http://www.w3.org/2000/svg"]) {{
        display: none;
    }}
    
    /* Esconde o seletor de páginas nativo do Streamlit */
    [data-testid="stSidebarNav"] {{
        display: none !important;
    }}
    
    /* Estilos para os links de navegação personalizados */
    .navigation-links a {{
        display: block;
        padding: 8px 12px;
        margin: 4px 0;
        text-decoration: none;
        color: #1E366F;
        border-radius: 4px;
        transition: all 0.2s ease;
    }}
    
    .navigation-links a:hover {{
        background-color: #E3F2FD;
        color: #1976D2 !important;
    }}
    
    /* Esconde o botão de hamburger do Streamlit */
    button[kind="header"] {{
        display: none !important;
    }}
    
    /* Remove excesso de padding na barra lateral */
    .st-emotion-cache-16txtl3 {{
        padding-top: 1rem !important;
    }}
    
    /* Título no topo */
    h1 {{
        margin-top: 2rem !important;
        margin-bottom: 1.5rem;
        color: #1E366F;
        font-weight: 600;
        padding-top: 1rem;
    }}
    
    /* Expanders na sidebar */
    .sidebar .st-expander {{
        border: 1px solid #E0E0E0;
        border-radius: 4px;
        margin-bottom: 1rem;
    }}
    
    /* Cabeçalho do expander */
    .sidebar .st-expander > div:first-child {{
        background-color: #F5F7FA;
        padding: 0.75rem;
    }}
    
    /* Estilização dos botões do menu principal para padronização */
    .sidebar button[data-testid="baseButton-secondary"] {{
        margin-top: 3px !important;
        margin-bottom: 3px !important;
        padding: 10px 15px !important;
        background-color: #f5f7fa !important;
        border: 1px solid #e0e4e8 !important;
        border-radius: 8px !important;
        font-size: 0.92rem !important;
        font-weight: 500 !important;
        color: #1E366F !important;
        transition: all 0.2s ease !important;
        font-family: "Poppins", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        text-align: left !important;
        height: 42px !important;
        line-height: 1.2 !important;
        letter-spacing: normal !important;
    }}
    
    /* Botão selecionado/ativo */
    .sidebar button[data-testid="baseButton-secondary"].menu-active {{
        background-color: #E3F2FD !important;
        border-color: #1E366F !important;
        box-shadow: 0 2px 5px rgba(30, 54, 111, 0.15) !important;
    }}
    
    /* Hover dos botões do menu */
    .sidebar button[data-testid="baseButton-secondary"]:hover {{
        background-color: #E3F2FD !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 8px rgba(30, 54, 111, 0.15) !important;
    }}
    
    /* Container dos botões com padding reduzido */
    .nav-buttons {{
        padding-top: 0.2rem !important;
        padding-bottom: 0.2rem !important;
        margin-top: 0 !important;
    }}
    
    /* Aplicar tamanho fixo para os ícones e alinhamento consistente */
    .sidebar button[data-testid="baseButton-secondary"] div {{
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
    }}
    
    /* Garantir que todos os ícones tenham espaço e alinhamento uniforme */
    .sidebar button[data-testid="baseButton-secondary"] div::before {{
        content: "" !important;
        width: 24px !important;
        display: inline-block !important;
        text-align: center !important;
        margin-right: 8px !important;
    }}
    
    /* Ajustar espaço entre a barra lateral e o conteúdo principal */
    [data-testid="stSidebar"] {{
        padding-top: 0 !important;
        margin-top: 0 !important;
    }}
    
    /* Reduzir espaço entre os itens da barra lateral */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {{
        padding-top: 0 !important;
        margin-top: 0 !important;
        gap: 0.5rem !important;
    }}
    </style>
""", unsafe_allow_html=True)

# Sem título na barra lateral - removido conforme solicitação

# CSS para ajustar a barra lateral mais próxima do topo e padronizar menus
st.sidebar.markdown("""
<style>
section[data-testid="stSidebar"] > div {
    padding-top: 0 !important;
    margin-top: 0 !important;
}
</style>
""", unsafe_allow_html=True)

# Container dos botões com fundo escuro
st.sidebar.markdown('<div class="nav-buttons">', unsafe_allow_html=True)

# Botões de navegação
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"

# Definição do menu principal
MENU_PRINCIPAL = {
    "📊 Dashboard": "Dashboard",
    "👥 Cadastros": "Cadastros",
    "📝 Propostas": "Propostas",
    "🛒 Vendas": "Vendas",
    "💰 Financeiro": "Financeiro",
    "📈 Relatórios": "Relatórios",
    "🧑‍💼 Meu Perfil": "Perfil"
}

# Criação dos botões do menu principal com estilização personalizada
for label, page in MENU_PRINCIPAL.items():
    # Verificar se este é o botão da página atual para destacá-lo
    is_active = st.session_state.current_page == page
    
    # Aplicar classe personalizada para o botão ativo usando JavaScript
    if is_active:
        # Adicionar código JavaScript para adicionar classe ao botão após ele ser renderizado
        button_id = f"main_menu_{page.lower()}"
        st.sidebar.markdown(f"""
        <script>
            document.addEventListener('DOMContentLoaded', function() {{
                // Aguardar até que o elemento seja renderizado
                setTimeout(function() {{
                    const button = document.querySelector('[data-testid="stButton"] button[kind="secondary"][data-baseweb="button"][aria-keyshortcuts="{button_id}"]');
                    if (button) {{
                        button.classList.add('menu-active');
                    }}
                }}, 100);
            }});
        </script>
        """, unsafe_allow_html=True)
    
    # Renderizar o botão normalmente
    if st.sidebar.button(label, key=f"main_menu_{page.lower()}", use_container_width=True):
        st.session_state.current_page = page
        st.rerun()

# Adicionar botão de logout
if st.sidebar.button("🚪 Sair do Sistema", 
                     key="btn_logout", 
                     type="secondary", 
                     use_container_width=True,
                     help="Clique para sair do sistema e retornar à tela de login"):
    # Limpar o estado de autenticação
    st.session_state.authenticated = False
    # Exibir mensagem
    st.sidebar.success("Logout realizado com sucesso!")
    # Redirecionar para a página de login (recarregando a página)
    st.rerun()

st.sidebar.markdown('</div>', unsafe_allow_html=True)

# Já não mostramos a página de boas-vindas separada, 
# pois agora o Dashboard é a página inicial por padrão
if st.session_state.authenticated:
    # Verificar se o usuário está fazendo login pela primeira vez
    if st.session_state.get('show_welcome', True):
        # Definir Dashboard como a página inicial
        st.session_state.current_page = "Dashboard"
        # Marcar que a página de boas-vindas já foi mostrada para esta sessão
        st.session_state.show_welcome = False

# Importar o cabeçalho e rodapé padrão
from utils.page_config import apply_page_header, apply_page_footer

# Aplicar o cabeçalho e rodapé em todas as páginas 
apply_page_header()
apply_page_footer()

# Roteamento de páginas
try:
    if st.session_state.current_page == "Dashboard":
        from pages.dashboard import show
        show()
    elif st.session_state.current_page == "Cadastros":
        from pages.cadastros import show
        show()
    elif st.session_state.current_page == "Propostas":
        from pages.propostas import show
        show()
    elif st.session_state.current_page == "Vendas":
        from pages.vendas import show
        show()
    elif st.session_state.current_page == "Financeiro":
        from pages.financeiro import show
        show()
    elif st.session_state.current_page == "Relatórios":
        from pages.relatorios import show
        show()
    elif st.session_state.current_page == "Perfil":
        from pages.perfil import show
        show()
except Exception as e:
    st.error(f"Erro ao carregar página: {str(e)}")

# Divisor antes das informações do sistema
st.sidebar.markdown('<div style="margin: 1.5rem 0;"><hr style="border: none; height: 1px; background-color: #E0E0E0;"></div>', unsafe_allow_html=True)

# Usando um expander para as informações do sistema
with st.sidebar.expander("ℹ️ Informações do Sistema"):
    st.markdown("### Planner Organizer")
    st.markdown("**Versão:** 1.0.4")
    
    st.markdown("### Módulos do Sistema:")
    st.markdown("""
    - **Dashboard** - Métricas e alertas
    - **Cadastros** - Clientes, parceiros e fornecedores
    - **Propostas** - Gestão completa de propostas
    - **Vendas** - Controle de produtos vendidos
    - **Financeiro** - Receitas e despesas
    - **Relatórios** - Análises e visualizações
    """)
    
    st.markdown("### Funcionalidades Principais:")
    st.markdown("""
    - ✅ Fluxo completo de propostas
    - ✅ Integração entre módulos
    - ✅ Sistema de alertas de prazos
    - ✅ Geração de lançamentos financeiros
    - ✅ Cálculo de comissões
    - ✅ Importação em lote
    - ✅ Backup e restauração
    """)
    
    # Botão para gerar o manual do sistema
    if st.button("📘 Gerar Manual do Sistema", use_container_width=True):
        with st.spinner("Gerando manual em PDF..."):
            try:
                from gerar_manual import gerar_manual_sistema
                pdf_path = gerar_manual_sistema()
                
                # Ler o arquivo PDF para download
                with open(pdf_path, "rb") as pdf_file:
                    pdf_bytes = pdf_file.read()
                
                st.success("Manual gerado com sucesso!")
                st.download_button(
                    label="📥 Baixar Manual do Sistema",
                    data=pdf_bytes,
                    file_name="Manual_Planner_Organizer.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Erro ao gerar o manual: {str(e)}")
    
    # Gerenciar o estado para os modais de termos e política
    if "mostrar_termos" not in st.session_state:
        st.session_state.mostrar_termos = False
        
    if "mostrar_politica" not in st.session_state:
        st.session_state.mostrar_politica = False
    
    # Funções para gerenciar os estados dos modais
    def exibir_termos():
        st.session_state.mostrar_termos = True
        
    def ocultar_termos():
        st.session_state.mostrar_termos = False
        
    def exibir_politica():
        st.session_state.mostrar_politica = True
        
    def ocultar_politica():
        st.session_state.mostrar_politica = False
    
    # Sem rodapé aqui - movido para o footer global
    
    # Exibir modais conforme o estado
    if st.session_state.mostrar_termos:
        # Criar um modal/dialog para os termos de uso
        with st.container():
            st.markdown("#### Termos de Uso")
            st.markdown("---")
            
            # Importamos a função do módulo
            from pages.termos_de_uso import get_termos_conteudo
            
            # Exibimos o conteúdo
            st.markdown(get_termos_conteudo(), unsafe_allow_html=True)
            
            # Botão para fechar
            if st.button("Fechar", key="fechar_termos", use_container_width=True):
                st.session_state.mostrar_termos = False
                st.experimental_rerun()
    
    if st.session_state.mostrar_politica:
        # Criar um modal/dialog para a política de privacidade
        with st.container():
            st.markdown("#### Política de Privacidade")
            st.markdown("---")
            
            # Importamos a função do módulo
            from pages.politica_privacidade import get_politica_conteudo
            
            # Exibimos o conteúdo
            st.markdown(get_politica_conteudo(), unsafe_allow_html=True)
            
            # Botão para fechar
            if st.button("Fechar", key="fechar_politica", use_container_width=True):
                st.session_state.mostrar_politica = False
                st.experimental_rerun()
    
    # Botão para download dos ícones do sistema
    try:
        with open("downloads/planner-icons.zip", "rb") as f:
            icones_bytes = f.read()
        
        st.download_button(
            label="🎨 Baixar Ícones do Sistema",
            data=icones_bytes,
            file_name="planner-icons.zip",
            mime="application/zip",
            use_container_width=True,
            help="Baixe todos os ícones do sistema em diferentes formatos (SVG, PNG, Favicon)"
        )
    except Exception as e:
        st.warning(f"Pacote de ícones não disponível")

# Links de navegação ocultos em um expander para desenvolvedores
with st.sidebar.expander("🔧 Acesso Desenvolvedor", expanded=False):
    st.markdown("""
    <div style="padding: 0.5rem; background-color: white; border-radius: 4px;">
        <h4 style="color: #1E366F; font-size: 1rem; margin-bottom: 0.8rem;">Navegação Rápida</h4>
        
        <div class="navigation-links">
            <a href="/" style="display: block; padding: 8px 12px; margin: 4px 0; border-radius: 4px; background-color: #F5F7FA; color: #1E366F; text-decoration: none; font-size: 0.85rem;">Home (App)</a>
            <a href="/cadastros" style="display: block; padding: 8px 12px; margin: 4px 0; border-radius: 4px; background-color: #F5F7FA; color: #1E366F; text-decoration: none; font-size: 0.85rem;">Cadastros</a>
            <a href="/dashboard" style="display: block; padding: 8px 12px; margin: 4px 0; border-radius: 4px; background-color: #F5F7FA; color: #1E366F; text-decoration: none; font-size: 0.85rem;">Dashboard</a>
            <a href="/dashboard_fixed" style="display: block; padding: 8px 12px; margin: 4px 0; border-radius: 4px; background-color: #F5F7FA; color: #1E366F; text-decoration: none; font-size: 0.85rem;">Dashboard (Fixed)</a>
            <a href="/financeiro" style="display: block; padding: 8px 12px; margin: 4px 0; border-radius: 4px; background-color: #F5F7FA; color: #1E366F; text-decoration: none; font-size: 0.85rem;">Financeiro</a>
            <a href="/propostas" style="display: block; padding: 8px 12px; margin: 4px 0; border-radius: 4px; background-color: #F5F7FA; color: #1E366F; text-decoration: none; font-size: 0.85rem;">Propostas</a>
            <a href="/relatorios" style="display: block; padding: 8px 12px; margin: 4px 0; border-radius: 4px; background-color: #F5F7FA; color: #1E366F; text-decoration: none; font-size: 0.85rem;">Relatórios</a>
            <a href="/vendas" style="display: block; padding: 8px 12px; margin: 4px 0; border-radius: 4px; background-color: #F5F7FA; color: #1E366F; text-decoration: none; font-size: 0.85rem;">Vendas</a>
        </div>
        
        <h4 style="color: #1E366F; font-size: 1rem; margin-top: 1.2rem; margin-bottom: 0.8rem;">Ferramentas</h4>
        <div class="tools-links">
            <a href="/manual_sistema" target="_blank" style="display: block; padding: 8px 12px; margin: 4px 0; border-radius: 4px; background-color: #E3F2FD; color: #1976D2; text-decoration: none; font-size: 0.85rem;">📘 Manual do Sistema</a>
            <a href="http://localhost:8530" target="_blank" style="display: block; padding: 8px 12px; margin: 4px 0; border-radius: 4px; background-color: #E8F5E9; color: #388E3C; text-decoration: none; font-size: 0.85rem;">💾 Sistema de Backup</a>
        </div>
        
        <p style="margin-top: 1rem; font-size: 0.8rem; color: #5A6A85; text-align: center;">
            Acesso exclusivo para desenvolvedores
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sem botão de importação conforme solicitado

# A navegação é controlada pelos botões do menu principal
# Os botões já atualizam st.session_state.current_page

# O conteúdo principal já é exibido acima através da importação dos módulos
# Não precisamos processar novamente os módulos
if False:
    module_name = st.session_state.current_page.lower()
    try:
        module = __import__(f"pages.{module_name}", fromlist=["show"])
        module.show()
    except ImportError as e:
        st.error(f"Erro ao carregar módulo {module_name}: {str(e)}")
# Não temos mais a opção de importação no menu