import streamlit as st

st.set_page_config(
    page_title="Planos - PlannerOrganizer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Adicionar o script do Stripe
st.markdown("""
<script src="https://js.stripe.com/v3/"></script>
<script>
const stripe = Stripe("pk_live_51RFB2dLWUPER7pUXim2VuVkCESsrjNcHkDQuMJeDCvvW0ZsyFfqM2exfCTwSSe5O4R2TXBxHJtIpYSGBTAx2gBXT00gpAVYK1f");

async function checkoutPlan(planType) {
    // URL da API local Stripe Direct
    const apiUrl = "http://localhost:8002/checkout/" + planType;
    
    try {
        const response = await fetch(apiUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            }
        });
        
        if (!response.ok) {
            throw new Error("Erro na resposta: " + response.status);
        }
        
        const data = await response.json();
        console.log("Resposta:", data);
        
        if (data.url) {
            // Redirecionar diretamente para a URL da sessão
            window.location.href = data.url;
        } else if (data.id) {
            // Usar o Stripe.js para redirecionar
            stripe.redirectToCheckout({ sessionId: data.id });
        } else {
            throw new Error("Resposta inválida do servidor");
        }
    } catch (error) {
        console.error("Erro:", error);
        alert("Ocorreu um erro ao processar seu pagamento. Por favor, tente novamente.");
    }
}
</script>
""", unsafe_allow_html=True)

# Título e subtítulo
st.title("Escolha o Plano Ideal")
st.subheader("Invista no crescimento da sua organização com nossos planos acessíveis")

# CSS para os cards
st.markdown("""
<style>
.plan-card {
    background-color: white;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.12);
    height: 100%;
    display: flex;
    flex-direction: column;
    transition: all 0.3s ease;
    border: 1px solid #e0e0e0;
    text-align: center;
}

.plan-card:hover {
    transform: translateY(-10px);
    box-shadow: 0 15px 30px rgba(0,0,0,0.15);
}

.plan-destacado {
    background: linear-gradient(to bottom, #f9fdff, #eaf7ff);
    border: 2px solid #2d8cff !important;
    position: relative;
    overflow: hidden;
}

.plan-destacado:before {
    content: "RECOMENDADO";
    position: absolute;
    top: 10px;
    right: -30px;
    background: #ff6b6b;
    color: white;
    padding: 5px 40px;
    font-size: 10px;
    font-weight: bold;
    transform: rotate(45deg);
}

.plan-title {
    font-size: 24px;
    font-weight: 700;
    color: #1E366F;
    margin-bottom: 10px;
}

.plan-price {
    font-size: 36px;
    font-weight: 800;
    color: #2d8cff;
    margin-bottom: 5px;
}

.plan-period {
    color: #666;
    margin-bottom: 20px;
    font-size: 14px;
}

.plan-trial {
    background-color: #e6fff0;
    color: #00a651;
    padding: 5px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: bold;
    margin: 0 auto 20px auto;
    max-width: 80%;
}

.plan-benefits {
    text-align: left;
    margin-bottom: 20px;
}

.plan-benefits ul {
    list-style-type: none;
    padding-left: 0;
}

.plan-benefits li {
    margin-bottom: 12px;
    position: relative;
    padding-left: 28px;
}

.plan-benefits li:before {
    content: "✓";
    position: absolute;
    left: 0;
    color: #2d8cff;
    font-weight: bold;
}

.plan-button {
    background: linear-gradient(135deg, #2d8cff, #1e66b5);
    color: white;
    border: none;
    padding: 12px;
    border-radius: 8px;
    font-weight: bold;
    font-size: 16px;
    cursor: pointer;
    width: 100%;
    transition: all 0.3s ease;
    box-shadow: 0 4px 6px rgba(45,140,255,0.2);
    text-align: center;
    text-decoration: none;
    display: inline-block;
}

.plan-button:hover {
    background: linear-gradient(135deg, #1e66b5, #154c8c);
    box-shadow: 0 6px 10px rgba(45,140,255,0.3);
}

.plan-destacado .plan-button {
    background: linear-gradient(135deg, #ff6b6b, #e83e3e);
    box-shadow: 0 4px 6px rgba(255,107,107,0.2);
}

.plan-destacado .plan-button:hover {
    background: linear-gradient(135deg, #e83e3e, #cf2b2b);
    box-shadow: 0 6px 10px rgba(255,107,107,0.3);
}
</style>
""", unsafe_allow_html=True)

# Cards dos planos
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="plan-card">
        <div class="plan-title">💳 Plano Mensal</div>
        <div class="plan-price">R$9,70</div>
        <div class="plan-period">por mês</div>
        <div class="plan-trial">✨ 7 DIAS DE TESTE GRÁTIS</div>
        <div class="plan-benefits">
            <ul>
                <li>Acesso a todos os recursos</li>
                <li>Suporte por e-mail</li>
                <li>Cancelamento a qualquer momento</li>
                <li>Ideal para testar o sistema</li>
            </ul>
        </div>
        <div class="plan-button" onclick="checkoutPlan('mensal')">ASSINAR MENSAL</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Assinar Mensal", key="btn_mensal"):
        st.markdown("<script>checkoutPlan('mensal');</script>", unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="plan-card plan-destacado">
        <div class="plan-title">📆 Plano Anual</div>
        <div class="plan-price">R$97,00</div>
        <div class="plan-period">por ano</div>
        <div class="plan-trial">✨ 7 DIAS DE TESTE GRÁTIS</div>
        <div class="plan-benefits">
            <ul>
                <li>Economize 17% vs. plano mensal</li>
                <li>Acesso a todos os recursos</li>
                <li>Suporte por e-mail prioritário</li>
                <li>Ideal para uso contínuo</li>
            </ul>
        </div>
        <div class="plan-button" onclick="checkoutPlan('anual')">ASSINAR ANUAL</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Assinar Anual", key="btn_anual"):
        st.markdown("<script>checkoutPlan('anual');</script>", unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="plan-card">
        <div class="plan-title">💎 Plano Vitalício</div>
        <div class="plan-price">R$247,00</div>
        <div class="plan-period">pagamento único</div>
        <div class="plan-trial" style="background-color: #ffe9e9; color: #e83e3e;">🔥 MELHOR CUSTO-BENEFÍCIO</div>
        <div class="plan-benefits">
            <ul>
                <li>Pagamento único para sempre</li>
                <li>Acesso a todos os recursos</li>
                <li>Suporte por e-mail VIP</li>
                <li>Ideal para uso a longo prazo</li>
            </ul>
        </div>
        <div class="plan-button" onclick="checkoutPlan('vitalicio')">COMPRAR VITALÍCIO</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Comprar Vitalício", key="btn_vitalicio"):
        st.markdown("<script>checkoutPlan('vitalicio');</script>", unsafe_allow_html=True)

# Link alternativo para acessar a página HTML direta
st.markdown("---")
st.markdown("""
<div style="text-align: center; margin-top: 30px;">
    <p>Prefere uma página de checkout direta?</p>
    <a href="http://localhost:8002/static/checkout-direct.html" target="_blank" style="display: inline-block; margin-top: 10px; background-color: #f0f0f0; color: #333; padding: 10px 20px; border-radius: 4px; text-decoration: none; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">Abrir Página de Checkout</a>
</div>
""", unsafe_allow_html=True)