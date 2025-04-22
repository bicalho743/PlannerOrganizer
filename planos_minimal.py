import streamlit as st
import base64
from pathlib import Path

# Configuração da página
st.set_page_config(
    page_title="Planner Organizer | Planos",
    page_icon="favicon.png",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Função para carregar CSS
def load_css():
    css = """
    <style>
    .main {
        background: linear-gradient(135deg, #f9fafc, #eef5ff);
    }
    
    section[data-testid="stSidebar"] {
        display: none !important;
    }
    
    h1, h2, h3 {
        color: #1E366F;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #2D8CFF, #1E366F);
        color: white;
        font-weight: bold;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #1E66B5, #152A50);
        transform: translateY(-2px);
    }
    
    .featured-plan {
        border: 2px solid #2D8CFF;
        border-radius: 10px;
        padding: 20px;
        position: relative;
        background: linear-gradient(to bottom, #f9fdff, #eaf7ff);
    }
    
    .regular-plan {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 20px;
        background-color: white;
    }
    
    .plan-price {
        font-size: 2rem;
        font-weight: bold;
        color: #2D8CFF;
    }
    
    .container {
        max-width: 1200px;
        margin: 0 auto;
    }
    
    .ribbon {
        position: absolute;
        top: -10px;
        right: 10px;
        background: #ff6b6b;
        color: white;
        padding: 5px 15px;
        font-size: 0.8rem;
        font-weight: bold;
        border-radius: 3px;
        transform: rotate(2deg);
    }
    
    .savings {
        background-color: #e6fff0;
        color: #00a651;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 15px;
    }
    
    .feature-list li {
        margin-bottom: 8px;
    }
    
    .feature-check {
        color: #2D8CFF;
        font-weight: bold;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# Carregar CSS
load_css()

# Ativar JavaScript para redirecionamento
def add_script():
    script = """
    <script>
    const STRIPE_PUBLISHABLE_KEY = "pk_live_51RFB2dLWUPER7pUXim2VuVkCESsrjNcHkDQuMJeDCvvW0ZsyFfqM2exfCTwSSe5O4R2TXBxHJtIpYSGBTAx2gBXT00gpAVYK1f";
    const API_URL = "http://localhost:8001"; // Porta da Stripe Simple API

    function redirectToCheckout(planId) {
        fetch(`${API_URL}/create-checkout-session/${planId}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            }
        })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                alert("Erro: " + data.error);
                return;
            }
            
            // Usar o ID da sessão do Stripe para redirecionar
            const stripe = Stripe(STRIPE_PUBLISHABLE_KEY);
            stripe.redirectToCheckout({ sessionId: data.id })
            .then(function(result) {
                if (result.error) {
                    alert(result.error.message);
                }
            });
        })
        .catch(err => {
            alert("Erro: " + err.message);
        });
    }
    </script>
    <script src="https://js.stripe.com/v3/"></script>
    """
    st.markdown(script, unsafe_allow_html=True)

# Adicionar script
add_script()

# Cabeçalho
st.markdown("<div style='text-align: center; padding: 2rem 1rem; background: linear-gradient(135deg, #1E366F, #2D8CFF); border-radius: 15px; margin-bottom: 2rem; color: white;'><h1>Planner Organizer</h1><p>Transforme sua organização em resultados mensuráveis</p></div>", unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center; margin-bottom: 2rem;'>Escolha o Plano Ideal Para o Seu Negócio</h2>", unsafe_allow_html=True)

# Layout de 3 colunas
col1, col2, col3 = st.columns(3)

# Plano Mensal
with col1:
    st.markdown("<div class='regular-plan'>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>💡 Plano Mensal</h3>", unsafe_allow_html=True)
    st.markdown("<div style='text-align: center;'><div class='plan-price'>R$9,70</div><div style='color: #666; margin-bottom: 20px;'>por mês</div></div>", unsafe_allow_html=True)
    
    st.markdown("<ul class='feature-list'>", unsafe_allow_html=True)
    st.markdown("<li><span class='feature-check'>✓</span> Acesso a todos os recursos</li>", unsafe_allow_html=True)
    st.markdown("<li><span class='feature-check'>✓</span> Suporte por e-mail</li>", unsafe_allow_html=True)
    st.markdown("<li><span class='feature-check'>✓</span> Cancelamento a qualquer momento</li>", unsafe_allow_html=True)
    st.markdown("<li><span class='feature-check'>✓</span> Ideal para testar o sistema</li>", unsafe_allow_html=True)
    st.markdown("</ul>", unsafe_allow_html=True)
    
    if st.button("ASSINAR MENSAL", key="monthly"):
        st.markdown("<script>redirectToCheckout('monthly');</script>", unsafe_allow_html=True)
        st.info("Redirecionando para o checkout...")
    
    st.markdown("</div>", unsafe_allow_html=True)

# Plano Anual (Destacado)
with col2:
    st.markdown("<div class='featured-plan'>", unsafe_allow_html=True)
    st.markdown("<div class='ribbon'>RECOMENDADO</div>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>🔥 Plano Anual</h3>", unsafe_allow_html=True)
    st.markdown("<div style='text-align: center;'><div class='plan-price'>R$97,00</div><div style='color: #666; margin-bottom: 10px;'>por ano</div></div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align: center;'><div class='savings'>ECONOMIZE 17%</div></div>", unsafe_allow_html=True)
    
    st.markdown("<ul class='feature-list'>", unsafe_allow_html=True)
    st.markdown("<li><span class='feature-check'>✓</span> Acesso a todos os recursos</li>", unsafe_allow_html=True)
    st.markdown("<li><span class='feature-check'>✓</span> Suporte prioritário</li>", unsafe_allow_html=True)
    st.markdown("<li><span class='feature-check'>✓</span> Atualizações gratuitas</li>", unsafe_allow_html=True)
    st.markdown("<li><span class='feature-check'>✓</span> Treinamento personalizado</li>", unsafe_allow_html=True)
    st.markdown("<li><span class='feature-check'>✓</span> Melhor custo-benefício</li>", unsafe_allow_html=True)
    st.markdown("</ul>", unsafe_allow_html=True)
    
    if st.button("ASSINAR ANUAL", key="yearly"):
        st.markdown("<script>redirectToCheckout('yearly');</script>", unsafe_allow_html=True)
        st.info("Redirecionando para o checkout...")
    
    st.markdown("</div>", unsafe_allow_html=True)

# Plano Vitalício
with col3:
    st.markdown("<div class='regular-plan'>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>🏆 Acesso Vitalício</h3>", unsafe_allow_html=True)
    st.markdown("<div style='text-align: center;'><div class='plan-price'>R$247,00</div><div style='color: #666; margin-bottom: 20px;'>pagamento único</div></div>", unsafe_allow_html=True)
    
    st.markdown("<ul class='feature-list'>", unsafe_allow_html=True)
    st.markdown("<li><span class='feature-check'>✓</span> Acesso permanente ao sistema</li>", unsafe_allow_html=True)
    st.markdown("<li><span class='feature-check'>✓</span> Suporte prioritário</li>", unsafe_allow_html=True)
    st.markdown("<li><span class='feature-check'>✓</span> Sem mensalidades futuras</li>", unsafe_allow_html=True)
    st.markdown("<li><span class='feature-check'>✓</span> Todas as atualizações inclusas</li>", unsafe_allow_html=True)
    st.markdown("<li><span class='feature-check'>✓</span> Melhor para longo prazo</li>", unsafe_allow_html=True)
    st.markdown("</ul>", unsafe_allow_html=True)
    
    if st.button("COMPRAR VITALÍCIO", key="lifetime"):
        st.markdown("<script>redirectToCheckout('lifetime');</script>", unsafe_allow_html=True)
        st.info("Redirecionando para o checkout...")
    
    st.markdown("</div>", unsafe_allow_html=True)

# Rodapé
st.markdown("<div style='text-align: center; margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid #e0e0e0; color: #666;'>© 2025 Planner Organizer. Todos os direitos reservados.</div>", unsafe_allow_html=True)

# Nota sobre Stripe
st.markdown("""
<div style="text-align: center; font-size: 0.8rem; margin-top: 1rem; color: #999;">
Para testar essa funcionalidade completamente, é necessário configurar as chaves do Stripe.
</div>
""", unsafe_allow_html=True)