import streamlit as st
import time
import os
import sys

# Configuração da página com layout amplo
st.set_page_config(
    page_title="Planner Organizer - Sistema Profissional",
    page_icon="favicon.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Esconder o menu, rodapé e cabeçalho
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Inicialização da sessão
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if 'show_signup' not in st.session_state:
    st.session_state.show_signup = False

if 'show_reset_password' not in st.session_state:
    st.session_state.show_reset_password = False
    
# Redirecionamento se já estiver autenticado
if st.session_state.authenticated:
    st.success("Login já realizado. Redirecionando...")
    # Redirecionamento simples
    st.markdown('<meta http-equiv="refresh" content="2; URL=app.py">', unsafe_allow_html=True)
    st.stop()

# Carregamento de CSS para estilização
st.markdown("""
<style>
/* Estilos gerais */
body {
    font-family: 'Roboto', sans-serif;
    background-color: #f9fafb;
    color: #333;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
}

/* Estilos para as seções e cartões */
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

.feature-card {
    background-color: white;
    border-radius: 8px;
    padding: 1.5rem;
    text-align: center;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    height: 100%;
    transition: transform 0.3s ease;
}

.feature-card:hover {
    transform: translateY(-5px);
}

.feature-icon {
    font-size: 2rem;
    color: #2d8cff;
    margin-bottom: 1rem;
}

.feature-title {
    color: #1E366F;
    font-size: 1.2rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
}

.feature-description {
    color: #5A6A85;
    font-size: 0.95rem;
}

/* Estilos para formulários */
.login-container {
    background-color: white;
    border-radius: 12px;
    padding: 2rem;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.login-title {
    color: #1E366F;
    font-size: 1.8rem;
    font-weight: 700;
    margin-bottom: 1.5rem;
    text-align: center;
}

/* Estilos para os cartões de planos */
.plano-card {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    border: 1px solid #e0e0e0;
    height: 100%;
    display: flex;
    flex-direction: column;
    transition: all 0.3s ease;
}

.plano-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.12);
}

.plano-destaque {
    border: 2px solid #2d8cff;
    transform: scale(1.05);
    box-shadow: 0 8px 24px rgba(45,140,255,0.15);
    position: relative;
    z-index: 10;
}

.plano-destaque:hover {
    transform: translateY(-5px) scale(1.05);
    box-shadow: 0 12px 30px rgba(45,140,255,0.2);
}

.plano-titulo {
    font-size: 1.2rem;
    font-weight: 600;
    color: #1E366F;
    margin-bottom: 1rem;
    text-align: center;
}

.plano-preco {
    font-size: 2.2rem;
    font-weight: 700;
    color: #2d8cff;
    text-align: center;
    margin-bottom: 0.2rem;
}

.plano-periodo {
    font-size: 0.9rem;
    color: #5A6A85;
    text-align: center;
    margin-bottom: 1rem;
}

.plano-economia {
    background-color: #e6f7ff;
    color: #2d8cff;
    padding: 5px 10px;
    border-radius: 5px;
    font-size: 0.75rem;
    font-weight: 600;
    text-align: center;
    margin-bottom: 1rem;
}

.plano-beneficios {
    flex-grow: 1;
}

.plano-beneficios ul {
    padding-left: 1.2rem;
    margin-bottom: 1rem;
}

.plano-beneficios li {
    color: #5A6A85;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
}

/* Ajustes de espaçamento */
.custom-button {
    background-color: #1E88E5 !important;
    color: white !important;
    font-weight: 500 !important;
    padding: 0.5rem 1rem !important;
    border-radius: 4px !important;
    border: none !important;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important;
    transition: all 0.3s ease !important;
}

.custom-button:hover {
    background-color: #1976D2 !important;
    box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
    transform: translateY(-2px) !important;
}
</style>
""", unsafe_allow_html=True)

# Layout principal
col1, col2 = st.columns([3, 2])

with col1:
    # Seção de hero
    st.markdown("""
    <div class="hero-section">
        <h1 class="hero-title">Planner Organizer</h1>
        <p class="hero-subtitle">
            Sistema profissional para Personal Organizers
            gerenciarem propostas, produtos e finanças.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Seção de recursos
    st.markdown("<h2>Por que escolher o Planner Organizer?</h2>", unsafe_allow_html=True)
    
    # Grid de recursos
    feat_col1, feat_col2, feat_col3 = st.columns(3)
    
    with feat_col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <h3 class="feature-title">Gestão Completa</h3>
            <p class="feature-description">
                Gerencie propostas, clientes, produtos e finanças em um único sistema.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    with feat_col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">💰</div>
            <h3 class="feature-title">Controle Financeiro</h3>
            <p class="feature-description">
                Acompanhe receitas, despesas e comissões automaticamente.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    with feat_col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📱</div>
            <h3 class="feature-title">Acesso de Qualquer Lugar</h3>
            <p class="feature-description">
                Use em qualquer dispositivo, a qualquer momento.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Seção de planos
    st.markdown("<h2>Planos disponíveis</h2>", unsafe_allow_html=True)
    
    plan_col1, plan_col2, plan_col3 = st.columns([1, 1.2, 1])
    
    with plan_col1:
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
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Assinar Plano Mensal", key="mensal_btn", use_container_width=True):
            st.success("Preparando a página de pagamento...")
            st.markdown("""
            <a href='https://checkout.stripe.com/c/pay/cs_test_a1hc4n3' target='_blank'>
                <button style='width: 100%; padding: 10px; background-color: #1E88E5; color: white; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px;'>
                    Ir para o checkout seguro
                </button>
            </a>
            """, unsafe_allow_html=True)
    
    with plan_col2:
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
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Assinar Plano Anual", key="anual_btn", use_container_width=True):
            st.success("Preparando a página de pagamento...")
            st.markdown("""
            <a href='https://checkout.stripe.com/c/pay/cs_test_b2hd5o4' target='_blank'>
                <button style='width: 100%; padding: 10px; background-color: #1E88E5; color: white; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px;'>
                    Ir para o checkout seguro
                </button>
            </a>
            """, unsafe_allow_html=True)
    
    with plan_col3:
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
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Adquirir Acesso Vitalício", key="vitalicio_btn", use_container_width=True):
            st.success("Preparando a página de pagamento...")
            st.markdown("""
            <a href='https://checkout.stripe.com/c/pay/cs_test_c3ie6p5' target='_blank'>
                <button style='width: 100%; padding: 10px; background-color: #1E88E5; color: white; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px;'>
                    Ir para o checkout seguro
                </button>
            </a>
            """, unsafe_allow_html=True)

with col2:
    # Container de login
    st.markdown("""
    <div class="login-container">
        <h2 class="login-title">Acesse sua conta</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Formulário de login (nativo do Streamlit)
    with st.form("login_form"):
        email = st.text_input("Email ou usuário")
        password = st.text_input("Senha", type="password")
        
        submitted = st.form_submit_button("Entrar", use_container_width=True)
        
        if submitted:
            if email.lower() == "admin" and password == "admin":
                with st.spinner("Autenticando..."):
                    time.sleep(1)
                st.success("Login realizado com sucesso!")
                st.session_state.authenticated = True
                st.markdown('<meta http-equiv="refresh" content="2; URL=app.py">', unsafe_allow_html=True)
            else:
                st.error("Usuário ou senha incorretos.")
    
    # Botões de ação adicionais
    col1, col2 = st.columns(2)
    
    with col1:
        # Uso de on_click para o botão "Esqueceu a senha"
        if st.button("Esqueceu sua senha?", key="forgot_pwd", use_container_width=True):
            st.session_state.show_reset_password = True
            st.rerun()
    
    with col2:
        # Uso de on_click para o botão "Criar conta"
        if st.button("Criar uma conta", key="create_acc", use_container_width=True):
            st.session_state.show_signup = True
            st.rerun()
    
    # Mensagem de demonstração
    st.info("Para demonstração, use: admin / admin")
    
    # Formulário de recuperação de senha
    if st.session_state.show_reset_password:
        st.markdown("""
        <hr style="margin: 20px 0;">
        <h3 style="text-align: center; color: #1E366F;">Recuperar Senha</h3>
        """, unsafe_allow_html=True)
        
        with st.form("reset_password_form"):
            reset_email = st.text_input("Digite seu e-mail")
            reset_submitted = st.form_submit_button("Enviar link de recuperação", use_container_width=True)
            
            if reset_submitted:
                if not reset_email:
                    st.error("Por favor, informe seu e-mail.")
                else:
                    with st.spinner("Enviando email de recuperação..."):
                        time.sleep(1.5)
                    st.success(f"Um link de recuperação foi enviado para {reset_email}")
                    st.session_state.show_reset_password = False
                    st.rerun()
    
    # Formulário de criação de conta
    if st.session_state.show_signup:
        st.markdown("""
        <hr style="margin: 20px 0;">
        <h3 style="text-align: center; color: #1E366F;">Criar Nova Conta</h3>
        """, unsafe_allow_html=True)
        
        with st.form("signup_form"):
            signup_name = st.text_input("Nome completo")
            signup_email = st.text_input("E-mail")
            signup_password = st.text_input("Senha", type="password")
            signup_confirm_password = st.text_input("Confirmar senha", type="password")
            
            signup_submitted = st.form_submit_button("Registrar", use_container_width=True)
            
            if signup_submitted:
                if not signup_name or not signup_email or not signup_password or not signup_confirm_password:
                    st.error("Todos os campos são obrigatórios.")
                elif signup_password != signup_confirm_password:
                    st.error("As senhas não coincidem.")
                else:
                    with st.spinner("Criando sua conta..."):
                        time.sleep(1.5)
                    st.success(f"Conta criada com sucesso para {signup_name}! Verifique seu e-mail {signup_email}.")
                    st.session_state.show_signup = False
                    st.rerun()

# Rodapé
st.markdown("""
<div style="text-align: center; margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid #E0E0E0;">
    <p style="color: #5A6A85; font-size: 0.8rem;">
        © 2025 Planner Organizer. Todos os direitos reservados.
    </p>
</div>
""", unsafe_allow_html=True)