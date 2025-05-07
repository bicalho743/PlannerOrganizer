import streamlit as st
import os

# Configuração da página
st.set_page_config(
    page_title="Planos Simplificados",
    page_icon="🏆",
    layout="centered"
)

# URLs dos planos (definidas estaticamente para teste)
MENSAL_URL = "https://buy.stripe.com/test_28og2t34LeLJ6mQ144" 
ANUAL_URL = "https://buy.stripe.com/test_7sI7vRcJ56T29z8dQQ"
VITALICIO_URL = "https://buy.stripe.com/test_eVa2bv34L1Aw29yfYZ"

# Injetar CSS
st.markdown("""
<style>
    /* Remover a barra lateral */
    [data-testid="collapsedControl"] {display: none;}
    section[data-testid="stSidebar"] {display: none;}
    
    /* Cabeçalho */
    .header {
        text-align: center;
        margin: 20px 0 40px 0;
    }
    
    /* Container de cartões */
    .card-container {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 20px;
        margin: 30px 0;
    }
    
    /* Cartão de preço */
    .price-card {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 20px;
        width: 280px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
        background-color: white;
        position: relative;
        overflow: hidden;
    }
    
    .price-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.2);
    }
    
    /* Badge de destaque */
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
    
    /* Título do plano */
    .plan-title {
        text-align: center;
        color: #333;
        font-size: 1.5rem;
        margin-bottom: 15px;
    }
    
    /* Preço */
    .price {
        text-align: center;
        font-size: 2.2rem;
        font-weight: bold;
        color: #2196F3;
        margin: 10px 0 5px 0;
    }
    
    /* Período do plano */
    .period {
        text-align: center;
        color: #757575;
        font-size: 0.9rem;
        margin-bottom: 20px;
    }
    
    /* Economia badge */
    .savings {
        background-color: #E8F5E9;
        color: #2E7D32;
        padding: 5px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin: 5px auto;
        text-align: center;
        width: 100%;
    }
    
    /* Lista de recursos */
    .feature-list {
        list-style-type: none;
        padding-left: 0;
        margin: 20px 0;
    }
    
    .feature-list li {
        margin: 10px 0;
        padding-left: 25px;
        position: relative;
    }
    
    .feature-list li:before {
        content: "✓";
        color: #4CAF50;
        position: absolute;
        left: 0;
    }
    
    /* Link de compra */
    .checkout-link {
        display: block;
        width: 100%;
        background-color: #2196F3;
        color: white;
        text-align: center;
        padding: 12px 0;
        border-radius: 5px;
        text-decoration: none;
        font-weight: bold;
        margin-top: 15px;
        transition: background-color 0.3s;
    }
    
    .checkout-link:hover {
        background-color: #1976D2;
    }
    
    .checkout-link.anual {
        background-color: #FF5722;
    }
    
    .checkout-link.anual:hover {
        background-color: #E64A19;
    }
    
    .checkout-link.vitalicio {
        background-color: #FFC107;
        color: #333;
    }
    
    .checkout-link.vitalicio:hover {
        background-color: #FFA000;
    }
    
    /* Rodapé */
    .footer {
        text-align: center;
        margin-top: 50px;
        padding: 20px;
        color: #757575;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# Cabeçalho 
st.markdown("""
<div class="header">
    <h1>Planner Organizer</h1>
    <p>Escolha o plano ideal para sua organização</p>
</div>
""", unsafe_allow_html=True)

# Cartões de preços usando links HTML puros (sem JavaScript)
st.markdown(f"""
<div class="card-container">
    <!-- Plano Mensal -->
    <div class="price-card">
        <h3 class="plan-title">Plano Mensal</h3>
        <div class="price">R$9,70</div>
        <div class="period">por mês</div>
        
        <ul class="feature-list">
            <li>Acesso a todos os recursos</li>
            <li>Suporte por e-mail</li>
            <li>Cancelamento a qualquer momento</li>
        </ul>
        
        <a href="{MENSAL_URL}" target="_blank" class="checkout-link">
            ASSINAR MENSAL
        </a>
    </div>
    
    <!-- Plano Anual -->
    <div class="price-card">
        <div class="highlight-badge">RECOMENDADO</div>
        <h3 class="plan-title">Plano Anual</h3>
        <div class="price">R$97,00</div>
        <div class="period">por ano</div>
        <div class="savings">ECONOMIZE 17%</div>
        
        <ul class="feature-list">
            <li>Acesso a todos os recursos</li>
            <li>Suporte prioritário</li>
            <li>Atualizações gratuitas</li>
            <li>Treinamento personalizado</li>
        </ul>
        
        <a href="{ANUAL_URL}" target="_blank" class="checkout-link anual">
            ASSINAR ANUAL
        </a>
    </div>
    
    <!-- Plano Vitalício -->
    <div class="price-card">
        <h3 class="plan-title">Acesso Vitalício</h3>
        <div class="price">R$247,00</div>
        <div class="period">pagamento único</div>
        
        <ul class="feature-list">
            <li>Acesso permanente ao sistema</li>
            <li>Suporte prioritário</li>
            <li>Sem mensalidades futuras</li>
            <li>Acesso a todas as atualizações</li>
        </ul>
        
        <a href="{VITALICIO_URL}" target="_blank" class="checkout-link vitalicio">
            COMPRAR VITALÍCIO
        </a>
    </div>
</div>
""", unsafe_allow_html=True)

# Seção de teste gratuito
st.markdown("""
<div style="text-align: center; margin: 50px 0;">
    <h2>Não está pronto para assinar?</h2>
    <p>Experimente grátis por 7 dias sem necessidade de cartão de crédito.</p>
</div>
""", unsafe_allow_html=True)

# Botão de teste gratuito com Streamlit (sem JavaScript)
if st.button("INICIAR TESTE GRATUITO", type="primary", use_container_width=False):
    st.page_link("/pages/iniciar_teste.py", label="Iniciar teste gratuito", icon="🔄")

# Rodapé
st.markdown("""
<div class="footer">
    <p>Planner Organizer &copy; 2025 - Todos os direitos reservados</p>
    <p>
        <a href="/termos" style="color: #1E366F; text-decoration: none;">Termos de Uso</a> • 
        <a href="/privacidade" style="color: #1E366F; text-decoration: none;">Política de Privacidade</a> • 
        <a href="mailto:contato@plannerorganizer.com.br" style="color: #1E366F; text-decoration: none;">Contato</a>
    </p>
</div>
""", unsafe_allow_html=True)