import streamlit as st
import os
import requests
import json

# Configurações da página
st.set_page_config(
    page_title="Planner Organizer - Planos e Assinaturas",
    page_icon="💼",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Configurações de preços do Stripe
STRIPE_PRICE_ID_MENSAL = os.environ.get('STRIPE_PRICE_ID_MENSAL')
STRIPE_PRICE_ID_ANUAL = os.environ.get('STRIPE_PRICE_ID_ANUAL')
STRIPE_PRICE_ID_VITALICIO = os.environ.get('STRIPE_PRICE_ID_VITALICIO')

# URL base para API
API_HOST = os.environ.get('API_HOST', 'http://localhost:8000')

# Função para criar sessão de checkout para usuários não logados
def criar_checkout_anonimo(plano):
    """
    Cria uma sessão de checkout para usuários não logados
    """
    endpoint = ""
    
    if plano == "mensal":
        endpoint = f"{API_HOST}/api/checkout/mensal"
    elif plano == "anual":
        endpoint = f"{API_HOST}/api/checkout/anual"
    elif plano == "vitalicio":
        endpoint = f"{API_HOST}/api/checkout/vitalicio"
    
    try:
        response = requests.get(endpoint)
        data = response.json()
        
        if response.status_code == 200 and data.get('success'):
            return data.get('checkout_url')
        else:
            return None
    except Exception as e:
        st.error(f"Erro ao criar sessão de checkout: {str(e)}")
        return None

# Remover a barra lateral
st.markdown("""
<style>
    [data-testid="collapsedControl"] {display: none;}
    section[data-testid="stSidebar"] {display: none;}
    
    /* Estilo para cabeçalho */
    .header-container {
        background-color: #1E366F;
        padding: 2rem 2rem 1.5rem 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    /* Estilos para cards de planos */
    .pricing-container {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 20px;
        margin: 20px 0;
    }
    
    .pricing-card {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 25px;
        width: 280px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .pricing-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 12px rgba(0,0,0,0.2);
    }
    
    .highlight-badge {
        position: absolute;
        top: 0;
        right: 0;
        background-color: #FF5722;
        color: white;
        padding: 5px 15px;
        transform: rotate(45deg) translate(15px, -15px);
        width: 150px;
        text-align: center;
        font-size: 0.8rem;
        font-weight: bold;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    .pricing-header {
        text-align: center;
        margin-bottom: 20px;
    }
    
    .pricing-title {
        font-size: 1.5rem;
        color: #1E366F;
        font-weight: 600;
        margin-bottom: 10px;
    }
    
    .pricing-price {
        font-size: 2.5rem;
        color: #2196F3;
        font-weight: 700;
        margin: 15px 0 5px 0;
    }
    
    .pricing-period {
        color: #757575;
        font-size: 0.9rem;
        margin-bottom: 20px;
    }
    
    .pricing-features {
        margin-bottom: 25px;
    }
    
    .pricing-feature {
        display: flex;
        align-items: flex-start;
        margin: 10px 0;
        font-size: 0.95rem;
        color: #333;
    }
    
    .pricing-feature svg {
        flex-shrink: 0;
        margin-right: 10px;
        color: #4CAF50;
        font-size: 1.1rem;
    }
    
    .pricing-button {
        display: block;
        background-color: #2196F3;
        color: white;
        text-align: center;
        padding: 12px;
        border-radius: 5px;
        font-weight: 600;
        margin-top: 20px;
        transition: background-color 0.3s ease;
        text-decoration: none;
        cursor: pointer;
        border: none;
        width: 100%;
    }
    
    .pricing-button:hover {
        background-color: #1976D2;
    }
    
    .pricing-button.anual {
        background-color: #FF5722;
    }
    
    .pricing-button.anual:hover {
        background-color: #E64A19;
    }
    
    .pricing-button.vitalicio {
        background-color: #FFC107;
        color: #333;
    }
    
    .pricing-button.vitalicio:hover {
        background-color: #FFA000;
    }
    
    .savings-badge {
        background-color: #E8F5E9;
        color: #2E7D32;
        padding: 5px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin-top: 5px;
    }
    
    .footer-container {
        text-align: center;
        margin-top: 3rem;
        padding: 1rem;
        color: #757575;
        font-size: 0.9rem;
    }
    
    .footer-link {
        color: #1E366F;
        text-decoration: none;
    }
    
    .footer-link:hover {
        text-decoration: underline;
    }
</style>
""", unsafe_allow_html=True)

# Cabeçalho
st.markdown("""
<div class="header-container">
    <h1>Planner Organizer</h1>
    <p style="font-size: 1.2rem; margin-top: 0.5rem;">Escolha o plano ideal para sua empresa</p>
</div>
""", unsafe_allow_html=True)

# Animação de balões
st.balloons()

# Descrição
st.markdown("""
<div style="text-align: center; margin-bottom: 2rem;">
    <h2>Transforme sua organização em sucesso</h2>
    <p style="font-size: 1.1rem; color: #555; max-width: 800px; margin: 1rem auto;">
        Gerencie propostas, clientes e finanças com precisão profissional. Nossa plataforma foi desenvolvida para 
        profissionais de organização que buscam excelência e resultados.
    </p>
</div>
""", unsafe_allow_html=True)

# Cards de preços usando HTML
st.markdown("""
<div class="pricing-container">
    <!-- Plano Mensal -->
    <div class="pricing-card">
        <div class="pricing-header">
            <div class="pricing-title">
                💡 Plano Mensal
            </div>
            <div class="pricing-price">
                R$9,70
            </div>
            <div class="pricing-period">
                por mês
            </div>
        </div>
        <div class="pricing-features">
            <div class="pricing-feature">
                <span style="color: #4CAF50; margin-right: 8px;">✓</span>
                Acesso a todos os recursos
            </div>
            <div class="pricing-feature">
                <span style="color: #4CAF50; margin-right: 8px;">✓</span>
                Suporte por e-mail
            </div>
            <div class="pricing-feature">
                <span style="color: #4CAF50; margin-right: 8px;">✓</span>
                Cancelamento a qualquer momento
            </div>
            <div class="pricing-feature">
                <span style="color: #4CAF50; margin-right: 8px;">✓</span>
                Ideal para testar o sistema
            </div>
        </div>
        <button class="pricing-button" id="btn-mensal" type="button">ASSINAR MENSAL</button>
    </div>
    
    <!-- Plano Anual -->
    <div class="pricing-card">
        <div class="highlight-badge">RECOMENDADO</div>
        <div class="pricing-header">
            <div class="pricing-title">
                🔥 Plano Anual
            </div>
            <div class="pricing-price">
                R$97,00
            </div>
            <div class="pricing-period">
                por ano
            </div>
            <div class="savings-badge">
                ECONOMIZE 17%
            </div>
        </div>
        <div class="pricing-features">
            <div class="pricing-feature">
                <span style="color: #4CAF50; margin-right: 8px;">✓</span>
                Acesso a todos os recursos
            </div>
            <div class="pricing-feature">
                <span style="color: #4CAF50; margin-right: 8px;">✓</span>
                Suporte prioritário
            </div>
            <div class="pricing-feature">
                <span style="color: #4CAF50; margin-right: 8px;">✓</span>
                Atualizações gratuitas
            </div>
            <div class="pricing-feature">
                <span style="color: #4CAF50; margin-right: 8px;">✓</span>
                Treinamento personalizado
            </div>
            <div class="pricing-feature">
                <span style="color: #4CAF50; margin-right: 8px;">✓</span>
                Melhor custo-benefício
            </div>
        </div>
        <button class="pricing-button anual" id="btn-anual" type="button">ASSINAR ANUAL</button>
    </div>
    
    <!-- Plano Vitalício -->
    <div class="pricing-card">
        <div class="pricing-header">
            <div class="pricing-title">
                🏆 Acesso Vitalício
            </div>
            <div class="pricing-price">
                R$247,00
            </div>
            <div class="pricing-period">
                pagamento único
            </div>
        </div>
        <div class="pricing-features">
            <div class="pricing-feature">
                <span style="color: #4CAF50; margin-right: 8px;">✓</span>
                Acesso permanente ao sistema
            </div>
            <div class="pricing-feature">
                <span style="color: #4CAF50; margin-right: 8px;">✓</span>
                Suporte prioritário
            </div>
            <div class="pricing-feature">
                <span style="color: #4CAF50; margin-right: 8px;">✓</span>
                Sem mensalidades futuras
            </div>
            <div class="pricing-feature">
                <span style="color: #4CAF50; margin-right: 8px;">✓</span>
                Todas as atualizações inclusas
            </div>
            <div class="pricing-feature">
                <span style="color: #4CAF50; margin-right: 8px;">✓</span>
                Melhor para longo prazo
            </div>
        </div>
        <button class="pricing-button vitalicio" id="btn-vitalicio" type="button">COMPRAR VITALÍCIO</button>
    </div>
</div>
""", unsafe_allow_html=True)

# Rodapé
st.markdown("""
<div class="footer-container">
    <p>Planner Organizer &copy; 2025 - Todos os direitos reservados</p>
    <p>
        <a href="?show_termos=true" class="footer-link">Termos de Uso</a> • 
        <a href="?show_politica=true" class="footer-link">Política de Privacidade</a> • 
        <a href="mailto:contato@plannerorganizer.com.br" class="footer-link">Contato</a>
    </p>
</div>
""", unsafe_allow_html=True)

# Adicionar JavaScript para os botões
st.markdown("""
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Botão Mensal
    document.getElementById('btn-mensal').addEventListener('click', function() {
        window.location.href = '/planos_novo';
    });
    
    // Botão Anual
    document.getElementById('btn-anual').addEventListener('click', function() {
        window.location.href = '/planos_novo';
    });
    
    // Botão Vitalício
    document.getElementById('btn-vitalicio').addEventListener('click', function() {
        window.location.href = '/planos_novo';
    });
});
</script>
""", unsafe_allow_html=True)

# Botões streamlit para os planos
st.markdown("<h3 style='text-align: center;'>Escolha um plano abaixo para começar agora:</h3>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("ASSINAR MENSAL", type="primary", key="py-mensal"):
        st.markdown('<meta http-equiv="refresh" content="0;URL=\'/planos_novo\'">', unsafe_allow_html=True)
        st.info("✅ Redirecionando para página de planos...")

with col2:
    if st.button("ASSINAR ANUAL", type="primary", key="py-anual"):
        st.markdown('<meta http-equiv="refresh" content="0;URL=\'/planos_novo\'">', unsafe_allow_html=True)
        st.success("✅ Redirecionando para página de planos...")

with col3:
    if st.button("COMPRAR VITALÍCIO", type="primary", key="py-vitalicio"):
        st.markdown('<meta http-equiv="refresh" content="0;URL=\'/planos_novo\'">', unsafe_allow_html=True)
        st.info("✅ Redirecionando para página de planos...")

# Testar período gratuito
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### Não está pronto para assinar?")
st.markdown("Experimente grátis por 7 dias sem necessidade de cartão de crédito.")

if st.button("INICIAR TESTE GRATUITO", type="secondary"):
    st.markdown('<meta http-equiv="refresh" content="0;URL=\'/planos_novo\'">', unsafe_allow_html=True)
    st.info("✅ Redirecionando para página de planos...")