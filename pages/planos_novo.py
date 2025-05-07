import streamlit as st
import os

# URL base para API
API_HOST = os.environ.get('API_HOST', 'http://localhost:8000')

# Configurações da página
st.set_page_config(
    page_title="Planner Organizer - Planos e Assinaturas",
    page_icon="💼",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Remover marcas do Streamlit e adicionar estilos personalizados
hide_streamlit_style = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    
    /* Estilos personalizados para a página de planos */
    h1 {
        color: #1E366F;
        text-align: center;
        margin-bottom: 2rem;
        font-family: 'Poppins', sans-serif;
    }
    
    h3 {
        color: #1E366F;
        margin-top: 2rem;
        margin-bottom: 1.5rem;
        text-align: center;
        font-family: 'Poppins', sans-serif;
    }
    
    .stripe-buy-button {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 1rem;
    }
    
    /* Container de planos */
    .planos-container {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 1rem;
        margin-bottom: 2rem;
        border: 1px solid #e9ecef;
    }
    
    /* Descrição dos planos */
    .plano-descricao {
        text-align: center;
        font-size: 0.9rem;
        margin-bottom: 1.5rem;
        color: #555;
    }
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Header da página
st.markdown("""
<div style="text-align: center; margin-bottom: 3rem;">
    <h1>Planos e Assinaturas</h1>
    <p style="font-size: 1.1rem; color: #555; max-width: 600px; margin: 0 auto;">
        Escolha o plano ideal para seu negócio e comece a organizar seus projetos de forma profissional.
    </p>
</div>
""", unsafe_allow_html=True)

# Container para planos
st.markdown('<div class="planos-container">', unsafe_allow_html=True)

# Título da seção de planos
st.markdown('<h3>Escolha um plano para começar</h3>', unsafe_allow_html=True)

# Descrição geral dos planos
st.markdown("""
<div class="plano-descricao">
    Todos os planos incluem todas as funcionalidades do sistema. 
    Escolha apenas o período de pagamento que melhor se adapta ao seu negócio.
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    # Botão do Stripe para plano mensal
    stripe_button_mensal = """
    <script async src="https://js.stripe.com/v3/buy-button.js"></script>
    <stripe-buy-button
      buy-button-id="buy_btn_1RMAfFLWUPER7pUXfw1g2eae"
      publishable-key="pk_live_51RFB2dLWUPER7pUXim2VuVkCESsrjNcHkDQuMJeDCvvW0ZsyFfqM2exfCTwSSe5O4R2TXBxHJtIpYSGBTAx2gBXT00gpAVYK1f"
    >
    </stripe-buy-button>
    """
    st.markdown(stripe_button_mensal, unsafe_allow_html=True)
    
    # Botão de fallback caso o Stripe não carregue
    if st.button("ASSINAR MENSAL (método alternativo)", type="primary", key="btn_mensal"):
        api_url = f"{API_HOST}/api/checkout/mensal"
        st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'{api_url}\'">', unsafe_allow_html=True)
        st.success("✅ Redirecionando para checkout...")

with col2:
    # Botão do Stripe para plano anual (usando o mesmo botão por enquanto)
    stripe_button_anual = """
    <script async src="https://js.stripe.com/v3/buy-button.js"></script>
    <stripe-buy-button
      buy-button-id="buy_btn_1RMAfFLWUPER7pUXfw1g2eae"
      publishable-key="pk_live_51RFB2dLWUPER7pUXim2VuVkCESsrjNcHkDQuMJeDCvvW0ZsyFfqM2exfCTwSSe5O4R2TXBxHJtIpYSGBTAx2gBXT00gpAVYK1f"
    >
    </stripe-buy-button>
    """
    st.markdown(stripe_button_anual, unsafe_allow_html=True)
    
    # Botão de fallback
    if st.button("ASSINAR ANUAL (método alternativo)", type="primary", key="btn_anual"):
        api_url = f"{API_HOST}/api/checkout/anual"
        st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'{api_url}\'">', unsafe_allow_html=True)
        st.success("✅ Redirecionando para checkout...")

with col3:
    # Botão do Stripe para plano vitalício (usando o mesmo botão por enquanto)
    stripe_button_vitalicio = """
    <script async src="https://js.stripe.com/v3/buy-button.js"></script>
    <stripe-buy-button
      buy-button-id="buy_btn_1RMAfFLWUPER7pUXfw1g2eae"
      publishable-key="pk_live_51RFB2dLWUPER7pUXim2VuVkCESsrjNcHkDQuMJeDCvvW0ZsyFfqM2exfCTwSSe5O4R2TXBxHJtIpYSGBTAx2gBXT00gpAVYK1f"
    >
    </stripe-buy-button>
    """
    st.markdown(stripe_button_vitalicio, unsafe_allow_html=True)
    
    # Botão de fallback
    if st.button("PLANO VITALÍCIO (método alternativo)", type="primary", key="btn_vitalicio"):
        api_url = f"{API_HOST}/api/checkout/vitalicio"
        st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'{api_url}\'">', unsafe_allow_html=True)
        st.success("✅ Redirecionando para checkout...")

# Fechando o container de planos
st.markdown('</div>', unsafe_allow_html=True)

# Seção para período de teste gratuito
st.markdown("""
<div style="background-color: #e9f7fe; padding: 2rem; border-radius: 1rem; text-align: center; margin: 2rem 0; border: 1px solid #cce5ff;">
    <h3 style="color: #0366d6; margin-bottom: 1rem;">Não está pronto para assinar?</h3>
    <p style="margin-bottom: 1.5rem; color: #333;">
        Experimente todas as funcionalidades do sistema gratuitamente por 7 dias sem compromisso.
    </p>
</div>
""", unsafe_allow_html=True)

# Botão do período gratuito
if st.button("INICIAR PERÍODO GRATUITO", type="secondary", use_container_width=True):
    st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'/api/iniciar_teste\'">', unsafe_allow_html=True)
    st.info("✅ Iniciando período de teste gratuito...")

# Seção de FAQ
st.markdown("""
<div style="margin-top: 3rem;">
    <h3>Perguntas Frequentes</h3>
    
    <div style="margin-top: 1.5rem;">
        <p style="font-weight: bold; color: #1E366F;">O que está incluído em cada plano?</p>
        <p style="color: #555;">
            Todos os planos incluem acesso completo a todas as funcionalidades do sistema, incluindo:
            gerenciamento de clientes, propostas, finanças, relatórios e produtos. A diferença está apenas
            na forma de pagamento.
        </p>
    </div>
    
    <div style="margin-top: 1.5rem;">
        <p style="font-weight: bold; color: #1E366F;">Posso trocar de plano depois?</p>
        <p style="color: #555;">
            Sim, você pode fazer upgrade ou downgrade do seu plano a qualquer momento através
            da área "Minha Assinatura" no painel administrativo.
        </p>
    </div>
    
    <div style="margin-top: 1.5rem;">
        <p style="font-weight: bold; color: #1E366F;">Existe período de fidelidade?</p>
        <p style="color: #555;">
            Não, você pode cancelar sua assinatura a qualquer momento sem taxas adicionais.
            No plano mensal e anual, você continuará com acesso até o final do período pago.
        </p>
    </div>
    
    <div style="margin-top: 1.5rem;">
        <p style="font-weight: bold; color: #1E366F;">Como funciona o plano vitalício?</p>
        <p style="color: #555;">
            O plano vitalício é um pagamento único que lhe dá acesso ao sistema por tempo ilimitado.
            Você terá acesso às atualizações e novas funcionalidades lançadas durante o primeiro ano.
            Após esse período, atualizações maiores podem requerer uma taxa de upgrade.
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# Rodapé
st.markdown("""
<div style="text-align: center; margin-top: 4rem; padding-top: 2rem; border-top: 1px solid #eaeaea; color: #777; font-size: 0.9rem;">
    &copy; 2025 Planner Organizer - Todos os direitos reservados<br>
    Pagamentos processados com segurança pelo <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/stripe/stripe-original.svg" width="40" style="vertical-align: middle;"/>
</div>
""", unsafe_allow_html=True)