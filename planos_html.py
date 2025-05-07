import streamlit as st
import os

# Configuração da página
st.set_page_config(
    page_title="Planner Organizer - Planos", 
    page_icon="🏆",
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# Título e descrição
st.title("Planner Organizer")
st.markdown("### Escolha o plano ideal para sua organização")

# URLs dos planos (definidas estaticamente para teste)
MENSAL_URL = "https://buy.stripe.com/test_28og2t34LeLJ6mQ144" 
ANUAL_URL = "https://buy.stripe.com/test_7sI7vRcJ56T29z8dQQ"
VITALICIO_URL = "https://buy.stripe.com/test_eVa2bv34L1Aw29yfYZ"

# Injetar CSS
st.markdown("""
<style>
    /* Remove a barra lateral */
    [data-testid="collapsedControl"] {display: none;}
    section[data-testid="stSidebar"] {display: none;}
    
    /* Estilo dos cards de preços */
    .pricing-container {
        display: flex;
        flex-wrap: wrap;
        justify-content: space-around;
        gap: 20px;
        margin: 30px 0;
    }
    
    .price-card {
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        padding: 25px;
        width: 290px;
        text-align: center;
        position: relative;
        overflow: hidden;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .price-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 12px rgba(0,0,0,0.2);
    }
    
    .price-card h3 {
        color: #1E366F;
        font-size: 1.5rem;
        margin-bottom: 15px;
    }
    
    .price {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2196F3;
        margin: 15px 0 5px;
    }
    
    .period {
        color: #757575;
        font-size: 0.9rem;
        margin-bottom: 20px;
    }
    
    .feature-list {
        text-align: left;
        list-style-type: none;
        padding: 0;
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
    
    .recommended {
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
    
    .savings {
        background-color: #E8F5E9;
        color: #2E7D32;
        padding: 5px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin-top: 5px;
    }
    
    /* Estilo dos botões/links de checkout */
    .checkout-link {
        display: inline-block;
        width: 100%;
        background-color: #2196F3;
        color: white;
        text-align: center;
        padding: 12px 0;
        text-decoration: none;
        border-radius: 5px;
        font-weight: bold;
        margin-top: 15px;
        transition: background-color 0.3s;
    }
    
    .checkout-link:hover {
        background-color: #1976D2;
    }
    
    .checkout-link.mensal {
        background-color: #2196F3;
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
</style>
""", unsafe_allow_html=True)

# Conteúdo dos planos usando HTML puro (sem React)
st.markdown(f"""
<div class="pricing-container">
    <!-- Plano Mensal -->
    <div class="price-card">
        <h3>Plano Mensal</h3>
        <div class="price">R$9,70</div>
        <div class="period">por mês</div>
        
        <ul class="feature-list">
            <li>Acesso a todos os recursos</li>
            <li>Suporte por e-mail</li>
            <li>Cancelamento a qualquer momento</li>
        </ul>
        
        <a href="{MENSAL_URL}" target="_blank" class="checkout-link mensal">
            ASSINAR MENSAL
        </a>
    </div>
    
    <!-- Plano Anual -->
    <div class="price-card">
        <div class="recommended">RECOMENDADO</div>
        <h3>Plano Anual</h3>
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
        <h3>Acesso Vitalício</h3>
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

# Rodapé
st.markdown("""
<div style="text-align: center; margin-top: 3rem; padding: 1rem; color: #757575; font-size: 0.9rem;">
    <p>Planner Organizer &copy; 2025 - Todos os direitos reservados</p>
    <p>
        <a href="/termos" style="color: #1E366F; text-decoration: none;">Termos de Uso</a> • 
        <a href="/privacidade" style="color: #1E366F; text-decoration: none;">Política de Privacidade</a> • 
        <a href="mailto:contato@plannerorganizer.com.br" style="color: #1E366F; text-decoration: none;">Contato</a>
    </p>
</div>
""", unsafe_allow_html=True)

# Teste gratuito
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### Não está pronto para assinar?")
st.markdown("Experimente grátis por 7 dias sem necessidade de cartão de crédito.")

if st.button("INICIAR TESTE GRATUITO", type="primary", use_container_width=False):
    st.page_link("/pages/iniciar_teste.py", label="Iniciar teste gratuito", icon="🔄")