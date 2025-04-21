import streamlit as st

# Configurações da página
st.set_page_config(
    page_title="Login - Planner Organizer", 
    page_icon="🔒",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS personalizado
st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    .login-container {
        background-color: white;
        padding: 30px;
        border-radius: 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        text-align: center;
        margin-bottom: 40px;
    }
    .login-title {
        font-size: 22px;
        font-weight: bold;
        margin-bottom: 20px;
        color: #333;
    }
    .login-subtitle {
        color: #666;
        margin-bottom: 30px;
        font-size: 16px;
    }
    .header {
        text-align: center;
        margin-bottom: 40px;
    }
    .header h1 {
        color: #2d8cff;
        font-size: 38px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .header p {
        font-size: 18px;
        color: #555;
    }
    .pricing-card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        height: 100%;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .pricing-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.1);
    }
    .pricing-card.highlight {
        border: 2px solid #2d8cff;
        position: relative;
    }
    .pricing-header {
        background-color: #2d8cff;
        color: white;
        padding: 10px;
        margin: -20px -20px 20px -20px;
        border-radius: 10px 10px 0 0;
        text-align: center;
        font-weight: bold;
    }
    .pricing-title {
        font-size: 22px;
        font-weight: bold;
        margin-bottom: 10px;
        text-align: center;
    }
    .pricing-price {
        font-size: 32px;
        font-weight: bold;
        color: #2d8cff;
        text-align: center;
        margin-bottom: 5px;
    }
    .pricing-period {
        color: #777;
        font-size: 14px;
        text-align: center;
        margin-bottom: 20px;
    }
    .pricing-button {
        background-color: #2d8cff;
        color: white;
        padding: 12px;
        border: none;
        border-radius: 5px;
        width: 100%;
        cursor: pointer;
        font-weight: bold;
        margin-top: 15px;
        text-align: center;
        display: block;
        transition: background-color 0.3s ease;
    }
    .pricing-button:hover {
        background-color: #1a6edf;
    }
    .footer {
        text-align: center;
        margin-top: 50px;
        color: #777;
        font-size: 14px;
        border-top: 1px solid #eee;
        padding-top: 20px;
    }
    /* Esconder elementos desnecessários */
    header {
        visibility: hidden;
    }
    .block-container {
        max-width: 900px;
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar variáveis de sessão
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user" not in st.session_state:
    st.session_state.user = None

# Título principal com design atraente
st.markdown('<div class="header"><h1>Planner Organizer</h1><p>Sistema de Gestão Profissional para o seu Negócio</p></div>', unsafe_allow_html=True)

# Verificar se o usuário já está autenticado
if not st.session_state.authenticated:
    # Área de login simplificada
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    # Texto explicativo
    st.markdown('<div class="login-title">Bem-vindo ao Planner Organizer</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-subtitle">Experimente gratuitamente o sistema completo de gestão de propostas comerciais</div>', unsafe_allow_html=True)
    
    # Login de demonstração direto (sem outros métodos)
    if st.button("Acessar o Sistema", key="demo_login", use_container_width=True, type="primary"):
        # Autenticar diretamente
        st.session_state.authenticated = True
        st.session_state.user = {
            "uid": "admin-demo",
            "email": "admin@example.com",
            "name": "Administrador",
            "role": "admin",
            "demo_mode": True
        }
        st.success("Login realizado com sucesso!")
        # Redirecionar ao app principal
        st.switch_page("app.py")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Seção de planos
    st.markdown('<h2 style="text-align: center; margin-top: 40px; margin-bottom: 30px;">Escolha o Plano Ideal para o Seu Negócio</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="pricing-card">
            <h3 class="pricing-title">Mensal</h3>
            <div class="pricing-price">R$ 9,70</div>
            <div class="pricing-period">por mês</div>
            <ul>
                <li>Acesso a todas as funcionalidades</li>
                <li>Suporte via email</li>
                <li>7 dias de teste grátis</li>
                <li>Cancele quando quiser</li>
            </ul>
            <button class="pricing-button">Assinar Plano</button>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="pricing-card highlight">
            <div class="pricing-header">Mais Popular</div>
            <h3 class="pricing-title">Anual</h3>
            <div class="pricing-price">R$ 97,00</div>
            <div class="pricing-period">por ano (economize 17%)</div>
            <ul>
                <li>Acesso a todas as funcionalidades</li>
                <li>Suporte prioritário</li>
                <li>7 dias de teste grátis</li>
                <li>Cancele quando quiser</li>
                <li>Economia de 2 meses no ano</li>
            </ul>
            <button class="pricing-button">Assinar Plano</button>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="pricing-card">
            <h3 class="pricing-title">Vitalício</h3>
            <div class="pricing-price">R$ 247,00</div>
            <div class="pricing-period">pagamento único</div>
            <ul>
                <li>Acesso a todas as funcionalidades</li>
                <li>Suporte premium</li>
                <li>Acesso vitalício sem mensalidades</li>
                <li>Acesso a novas funcionalidades</li>
                <li>Prioridade nas atualizações</li>
            </ul>
            <button class="pricing-button">Comprar Acesso</button>
        </div>
        """, unsafe_allow_html=True)
    
    # Rodapé
    st.markdown("""
    <div class="footer">
        <p>© 2025 Planner Organizer. Todos os direitos reservados.</p>
        <p>Dúvidas? Entre em contato: contato@plannerorganizer.com.br</p>
    </div>
    """, unsafe_allow_html=True)
    
else:
    # Se já estiver autenticado, redirecionar para o app principal
    st.switch_page("app.py")