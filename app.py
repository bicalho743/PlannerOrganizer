import streamlit as st
import os
import sys

# Adicionar diretório atual ao path para importações relativas
sys.path.append('.')

# Importar Database
try:
    from utils.database import Database
except ImportError:
    # Fallback para quando a Database não estiver disponível
    class Database:
        def __init__(self):
            st.warning("Usando Database em modo mock. Para funcionalidade completa, verifique a importação real.")

# Definição de URLs globais
planos_url = "/planos_sem_stripe"  # URL para redirecionamento aos planos

# Configuração inicial da página - DEVE ser o primeiro comando Streamlit
st.set_page_config(
    page_title="Planner Organizer - Sistema Profissional",
    page_icon="favicon.png",
    layout="wide",
    initial_sidebar_state="auto"
)

import os
import sys
import json
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adicionar diretório raiz ao path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)
    logger.info(f"Adicionado {project_root} ao sys.path")

# Verificar se o usuário está autenticado
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Adicionar o Firebase SDK para autenticação na página
st.markdown("""
<script src="https://www.gstatic.com/firebasejs/8.10.0/firebase-app.js"></script>
<script src="https://www.gstatic.com/firebasejs/8.10.0/firebase-auth.js"></script>
<script src="https://www.gstatic.com/firebasejs/8.10.0/firebase-firestore.js"></script>
<script src="/public/js/firebase-auth.js"></script>
""", unsafe_allow_html=True)

# Configuração do Firebase
firebase_config = {
    "apiKey": st.secrets.get("FIREBASE_API_KEY", "AIzaSyA8xzYgZXCkZ-97RWQZXtMpvLVf1Jx8wjk"),
    "authDomain": st.secrets.get("FIREBASE_AUTH_DOMAIN", "planner-organizer.firebaseapp.com"),
    "projectId": st.secrets.get("FIREBASE_PROJECT_ID", "planner-organizer"),
    "storageBucket": st.secrets.get("FIREBASE_STORAGE_BUCKET", "planner-organizer.appspot.com"),
    "messagingSenderId": st.secrets.get("FIREBASE_MESSAGING_SENDER_ID", "695046724018"),
    "appId": st.secrets.get("FIREBASE_APP_ID", "1:695046724018:web:98d8feec0c6b6c937d57fd"),
    "databaseURL": st.secrets.get("FIREBASE_DATABASE_URL", "https://planner-organizer-default-rtdb.firebaseio.com")
}

# JavaScript para inicializar o Firebase
st.markdown(f"""
<script>
    // Configuração do Firebase
    const firebaseConfig = {json.dumps(firebase_config)};
    
    // Inicializar Firebase quando a página carregar
    document.addEventListener('DOMContentLoaded', function() {{
        // Inicializar Firebase
        if (window.firebaseAuth) {{
            window.firebaseAuth.init(firebaseConfig);
            console.log("Firebase inicializado via script");
        }}
    }});
</script>
""", unsafe_allow_html=True)

# Inicialização da autenticação in-app
if not st.session_state.authenticated:
    # Ocultar completamente a barra lateral na página de login
    st.markdown("""
    <style>
    [data-testid="collapsedControl"] {display: none;}
    section[data-testid="stSidebar"] {display: none;}
    </style>
    """, unsafe_allow_html=True)
    
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
        
        # TABELA DE PLANOS SIMPLIFICADA (com links para página de checkout separada)
        col1, col2, col3 = st.columns([1, 1.2, 1])  # o do meio ganha mais espaço
        
        # Exibir informações de contato para vendas
        contato_email = "contato@plannerorganizer.com.br"
        contato_whatsapp = "+55 (11) 99999-9999"
        
        # URLs para páginas específicas do produto (sem Stripe)
        # No Streamlit, a navegação é diferente do HTML normal
        # Vamos usar uma solução baseada em estado para navegar

        # Plano Mensal
        with col1:
            st.markdown("""
            <div class="plano-card">
                <div class="plano-titulo">💳 Plano Mensal</div>
                <div class="plano-preco">R$9,70</div>
                <div class="plano-periodo">por mês</div>
                <div style="background-color: #e6fff0; color: #00a651; padding: 5px; border-radius: 5px; text-align: center; margin-bottom: 15px; font-size: 12px; font-weight: bold;">✨ 7 DIAS DE TESTE GRÁTIS</div>
                <div class="plano-beneficios">
                    <ul>
                        <li>Acesso a todos os recursos</li>
                        <li>Suporte por e-mail</li>
                        <li>Cancelamento a qualquer momento</li>
                        <li>Ideal para testar o sistema</li>
                    </ul>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Botão nativo para a página de planos
            if st.button("Assinar Plano Mensal", key="btn_mensal", use_container_width=True):
                # Adicionar ao estado para navegar
                st.session_state.redirect_to_planos = True
                st.session_state.plano_selecionado = "mensal"
                st.rerun()

        # Plano Anual
        with col2:
            st.markdown("""
            <div class="plano-card plano-destaque">
                <div class="plano-titulo">📆 Plano Anual</div>
                <div class="plano-preco">R$97,00</div>
                <div class="plano-periodo">por ano</div>
                <div class="plano-economia">ECONOMIZE 17%</div>
                <div style="background-color: #e6fff0; color: #00a651; padding: 5px; border-radius: 5px; text-align: center; margin-bottom: 15px; font-size: 12px; font-weight: bold;">✨ 7 DIAS DE TESTE GRÁTIS</div>
                <div class="plano-beneficios">
                    <ul>
                        <li>Acesso a todos os recursos</li>
                        <li>Suporte prioritário</li>
                        <li>Atualizações gratuitas</li>
                        <li>Treinamento personalizado</li>
                        <li>Melhor custo-benefício</li>
                    </ul>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Botão nativo para a página de planos
            if st.button("Assinar Plano Anual", key="btn_anual", use_container_width=True):
                # Adicionar ao estado para navegar
                st.session_state.redirect_to_planos = True
                st.session_state.plano_selecionado = "anual"
                st.rerun()

        # Plano Vitalício
        with col3:
            st.markdown("""
            <div class="plano-card">
                <div class="plano-titulo">💎 Acesso Vitalício</div>
                <div class="plano-preco">R$247,00</div>
                <div class="plano-periodo">pagamento único</div>
                <div class="plano-economia">MELHOR VALOR A LONGO PRAZO</div>
                <div class="plano-beneficios">
                    <ul>
                        <li>Acesso permanente ao sistema</li>
                        <li>Suporte prioritário</li>
                        <li>Sem mensalidades futuras</li>
                        <li>Todas as atualizações inclusas</li>
                        <li>Melhor para longo prazo</li>
                    </ul>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Botão nativo para a página de planos
            if st.button("Adquirir Acesso Vitalício", key="btn_vitalicio", use_container_width=True):
                # Adicionar ao estado para navegar
                st.session_state.redirect_to_planos = True
                st.session_state.plano_selecionado = "vitalicio"
                st.rerun()
        
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
        
        # Título direto sem cabeçalho separado para evitar barra branca
        st.markdown('''
        <h2 style="text-align: center; color: #1E366F; margin-top: 0; margin-bottom: 20px;">Acesse sua conta</h2>
        ''', unsafe_allow_html=True)
        
        # Removi os botões de login social conforme solicitado
        
        # Formulário de login sem divisor (já que não temos mais os botões sociais)
        st.markdown('''
        <div style="height: 10px;"></div>
        ''', unsafe_allow_html=True)
        
        # Formulário de login
        with st.form("login_form"):
            username = st.text_input("Usuário ou E-mail")
            password = st.text_input("Senha", type="password")
            st.markdown('<div style="height: 15px;"></div>', unsafe_allow_html=True)
            submit = st.form_submit_button("Entrar na minha conta", use_container_width=True)
            
            if submit:
                from utils.firebase_auth import fazer_login
                from utils.subscription_manager import subscription_manager
                
                with st.spinner("Autenticando..."):
                    # Login de demonstração
                    if username.lower() == "admin" and password == "admin":
                        # Definir estado de autenticação
                        st.session_state.authenticated = True
                        st.session_state.user = {
                            'user_id': 'admin-demo',
                            'email': 'admin@example.com',
                            'demo_mode': True
                        }
                        st.session_state.current_page = "Dashboard"
                        
                        # Mensagem de sucesso
                        st.success("Login realizado com sucesso (modo de demonstração)!")
                        
                        # Redirecionamento simples com apenas meta refresh
                        st.markdown('<meta http-equiv="refresh" content="2; url=/" />', unsafe_allow_html=True)
                        st.stop()
                    
                    # Tentativa de login real com Firebase    
                    result = fazer_login(username, password)
                    
                    if result:
                        # Login bem-sucedido
                        st.session_state.authenticated = True
                        st.session_state.user = result
                        
                        # Verificar status da assinatura
                        user_id = result.get('user_id')
                        subscription_details = subscription_manager.get_subscription_details(user_id)
                        
                        # Armazenar detalhes da assinatura na sessão
                        st.session_state.subscription = subscription_details
                        
                        # Verificar se o usuário tem uma assinatura ativa
                        if subscription_details["is_active"]:
                            st.success(f"Login realizado com sucesso! Bem-vindo ao {subscription_details['plan_name']}.")
                        else:
                            # Usuário sem assinatura ativa
                            st.warning("Sua assinatura não está ativa. Você será redirecionado para a seleção de planos.")
                            st.session_state.show_plans = True
                        
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos")
        
        # Botões para recuperação de senha e cadastro
        col1, col2 = st.columns(2)
        
        # Definir as variáveis de estado se não existirem
        if "show_reset_password" not in st.session_state:
            st.session_state.show_reset_password = False
        if "show_signup" not in st.session_state:
            st.session_state.show_signup = False
            
        # Botão de esqueceu senha - o original que estava funcionando
        with col1:
            if st.button("Esqueceu sua senha?", key="forgot_password_btn", use_container_width=True):
                st.session_state.show_reset_password = True
                st.session_state.show_signup = False
                st.rerun()
                
        # Botão de criar conta - voltando para a versão original que funcionava
        with col2:
            if st.button("Criar uma conta", key="create_account_btn", use_container_width=True):
                st.session_state.show_signup = True
                st.session_state.show_reset_password = False 
                st.rerun()
                
        # Informações de demo
        st.markdown('''
        <div style="margin-top: 0.8rem; text-align: center;">
            <p style="color: #9E9E9E; font-size: 0.75rem;">
                Para demonstração, use: admin / admin
            </p>
        </div>
        ''', unsafe_allow_html=True)
        
        # Formulário de redefinição de senha
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
                            # Importar a função de redefinição de senha do Firebase
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
                        except ImportError as e:
                            # Fallback se o módulo Firebase não estiver configurado
                            st.warning(f"Módulo Firebase indisponível: {str(e)}")
                            # Simulação de envio de e-mail para modo de demonstração
                            with st.spinner("Enviando email de recuperação (demonstração)..."):
                                import time
                                time.sleep(1.5)
                            st.success(f"Um link de recuperação foi enviado para {email_reset} (modo de demonstração).")
                            st.session_state.show_reset_password = False
                            st.rerun()
                        
        # Formulário de cadastro
        if "show_signup" in st.session_state and st.session_state.show_signup:
            st.markdown('<hr style="margin: 20px 0;">', unsafe_allow_html=True)
            st.markdown('<h3 style="text-align: center; color: #1E366F;">Escolha seu plano</h3>', unsafe_allow_html=True)
            
            # Definir as variáveis de estado para o plano selecionado
            if "selected_plan" not in st.session_state:
                st.session_state.selected_plan = None
            
            # Seleção de plano antes de mostrar o formulário
            plan_options = {
                "mensal": "Plano Mensal - R$9,70/mês (7 dias grátis)",
                "anual": "Plano Anual - R$97,00/ano (7 dias grátis)",
                "vitalicio": "Acesso Vitalício - R$247,00 (pagamento único)"
            }
            
            selected_plan = st.selectbox(
                "Selecione seu plano",
                options=list(plan_options.keys()),
                format_func=lambda x: plan_options.get(x),
                key="plan_selection"
            )
            
            # Verificar se já existe um formulário de registro aberto
            if "signup_form_open" not in st.session_state:
                st.session_state.signup_form_open = False
            
            # Botão para confirmar a seleção de plano
            if not st.session_state.signup_form_open:
                if st.button("Continuar com este plano", key="confirm_plan", use_container_width=True):
                    st.session_state.selected_plan = selected_plan
                    st.session_state.signup_form_open = True
                    st.rerun()
            
            # Mostrar formulário se o plano foi selecionado
            if st.session_state.signup_form_open and st.session_state.selected_plan:
                st.markdown('<hr style="margin: 20px 0;">', unsafe_allow_html=True)
                st.markdown('<h3 style="text-align: center; color: #1E366F;">Informações pessoais</h3>', unsafe_allow_html=True)
                
                with st.form("signup_form"):
                    nome = st.text_input("Nome Completo")
                    email = st.text_input("E-mail", key="signup_email")
                    senha = st.text_input("Senha", type="password", key="signup_password", 
                                         help="Mínimo de 6 caracteres")
                    confirmar_senha = st.text_input("Confirmar Senha", type="password")
                    
                    # Mostrar termos e condições
                    st.markdown("""
                    <div style="font-size: 0.8rem; color: #666;">
                        Ao clicar em "Criar conta e prosseguir para pagamento", você concorda com nossos 
                        <a href="#" target="_blank">Termos de Serviço</a> e 
                        <a href="#" target="_blank">Política de Privacidade</a>.
                    </div>
                    """, unsafe_allow_html=True)
                    
                    submit_signup = st.form_submit_button("Criar conta e prosseguir para pagamento", use_container_width=True)
                    
                    if submit_signup:
                        import requests
                        
                        if not nome or not email or not senha or not confirmar_senha:
                            st.error("Todos os campos são obrigatórios.")
                        elif len(senha) < 6:
                            st.error("A senha deve ter no mínimo 6 caracteres.")
                        elif senha != confirmar_senha:
                            st.error("As senhas não coincidem.")
                        else:
                            # Usar nossa API de integração para criar o usuário e sessão de checkout
                            with st.spinner("Criando sua conta e preparando o checkout..."):
                                try:
                                    # URL da API de integração Firebase-Stripe
                                    api_url = "http://localhost:8001/api/create-user-and-checkout"
                                    if os.environ.get("REPLIT_DOMAIN"):
                                        # Em produção, usar a URL do domínio
                                        api_url = f"https://{os.environ.get('REPLIT_DOMAIN')}/api/create-user-and-checkout"
                                    
                                    # Mapeamento dos planos para os IDs corretos na API
                                    plan_mapping = {
                                        "mensal": "monthly",
                                        "anual": "yearly",
                                        "vitalicio": "lifetime"
                                    }
                                    
                                    # Converter para o formato aceito pela API
                                    api_plan_id = plan_mapping.get(st.session_state.selected_plan)
                                    
                                    # Dados para enviar
                                    user_data = {
                                        "email": email,
                                        "name": nome,
                                        "plan_id": api_plan_id
                                    }
                                    
                                    # Tentativa real de API
                                    try:
                                        response = requests.post(
                                            api_url,
                                            json=user_data,
                                            timeout=10
                                        )
                                        
                                        if response.status_code == 200:
                                            user_data = response.json()
                                            
                                            # Salvar UID para uso futuro
                                            st.session_state.firebase_uid = user_data.get("firebase_uid")
                                            
                                            # Redirecionar para a página de planos sem Stripe
                                            st.success("Conta criada com sucesso! Você será redirecionado para a página de planos.")
                                            
                                            # Redirecionamento para a página de planos
                                            st.markdown(f"""
                                            <script>
                                                setTimeout(function() {{
                                                    window.location.href = "{planos_url}";
                                                }}, 3000);
                                            </script>
                                            """, unsafe_allow_html=True)
                                            
                                            # Mostrar link manual
                                            st.markdown(f"""
                                            Se não for redirecionado automaticamente, [clique aqui para ver os planos disponíveis]({planos_url})
                                            """)
                                        else:
                                            st.error(f"Erro: {response.status_code} - {response.text}")
                                    
                                    except requests.RequestException as e:
                                        # Modo de demonstração para caso a API não esteja disponível
                                        st.warning("API de integração não disponível, usando modo de demonstração")
                                        
                                        # Simular criação de conta com Firebase diretamente
                                        from utils.firebase_auth import criar_conta
                                        
                                        # Criar conta no Firebase
                                        result = criar_conta(email, senha, nome)
                                        
                                        if result:
                                            # Salvar UID para uso futuro
                                            firebase_uid = result.get('user_id')
                                            st.session_state.firebase_uid = firebase_uid
                                            
                                            # Redirecionar para a página de planos sem Stripe
                                            st.success("Conta criada com sucesso! Você será redirecionado para a página de planos.")
                                            
                                            # Redirecionamento para a página de planos
                                            st.markdown(f"""
                                            <script>
                                                setTimeout(function() {{
                                                    window.location.href = "{planos_url}";
                                                }}, 3000);
                                            </script>
                                            """, unsafe_allow_html=True)
                                            
                                            # Mostrar link manual
                                            st.markdown(f"""
                                            Se não for redirecionado automaticamente, [clique aqui para ver os planos disponíveis]({planos_url})
                                            """)
                                        else:
                                            st.error("Erro ao criar conta. Verifique se o e-mail já está em uso.")
                                
                                except Exception as e:
                                    st.error(f"Erro inesperado: {str(e)}")
                
                # Voltar para seleção de plano
                if st.button("Voltar para seleção de plano", key="back_to_plan"):
                    st.session_state.signup_form_open = False
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
                    # Definir estado de autenticação
                    st.session_state.authenticated = True
                    st.session_state.current_page = "Dashboard"
                    
                    # Mensagem de sucesso
                    st.success("Acesso de desenvolvedor ativado!")
                    
                    # Redirecionamento simples
                    st.markdown('<meta http-equiv="refresh" content="2; url=/" />', unsafe_allow_html=True)
                    st.stop()
    
    # Seção de marcas/clientes
    st.markdown('''
    <div class="brands-section">
        <p style="color: #5A6A85; font-size: 0.9rem; margin-bottom: 1rem;">CONFIADO POR PERSONAL ORGANIZERS DE TODO O BRASIL</p>
        <div style="display: flex; justify-content: space-around; align-items: center; flex-wrap: wrap;">
            <span style="color: #1E366F; font-weight: 600; margin: 0 1rem;">Organizze Bem</span>
            <span style="color: #1E366F; font-weight: 600; margin: 0 1rem;">Organize Fácil</span>
            <span style="color: #1E366F; font-weight: 600; margin: 0 1rem;">Espaço Leve</span>
            <span style="color: #1E366F; font-weight: 600; margin: 0 1rem;">Ju Organizer</span>
            <span style="color: #1E366F; font-weight: 600; margin: 0 1rem;">Daniela Siqueira</span>
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
        st.success("Conexão com o banco de dados estabelecida com sucesso!")
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
    </style>
""", unsafe_allow_html=True)

# Título principal do menu
# Adicionar frase motivacional acima do menu principal
st.sidebar.markdown("""
<div style="font-size: 0.9rem; color: #1E366F; margin-bottom: 1.5rem; text-align: center; font-style: italic; padding: 15px; background-color: #E3F2FD; border-radius: 6px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
    "Transforme sua organização em resultados: gerencie propostas, clientes e finanças com precisão profissional."
</div>
""", unsafe_allow_html=True)

# Título do menu
st.sidebar.markdown("""
<h1 style="font-size: 1.6rem; color: #1E366F; margin-bottom: 1.5rem; text-align: center; font-weight: 600;">
    Planner Organizer<br>
    <span style="font-size: 0.9rem; color: #5A6A85; font-weight: 400;">Sistema Profissional de Gestão Personal Organizer</span>
</h1>
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
    "📈 Relatórios": "Relatórios"
}

# Criação dos botões do menu principal
for label, page in MENU_PRINCIPAL.items():
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

# Página de boas-vindas ao fazer login
if st.session_state.get('show_welcome', True) and st.session_state.authenticated:
    try:
        from pages.boas_vindas import show
        show()
        # Marcar que a página de boas-vindas já foi mostrada para esta sessão
        st.session_state.show_welcome = False
    except Exception as e:
        st.error(f"Erro ao carregar página de boas-vindas: {str(e)}")
        # Em caso de erro, desativar a página de boas-vindas
        st.session_state.show_welcome = False

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
    
    st.markdown("© 2025 Planner Organizer")
    
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