import streamlit as st
import os

# URL base para API
# Obter a URL base da API do ambiente, se não existir, construir a partir do REPL_SLUG
REPL_SLUG = os.environ.get('REPL_SLUG', '')
API_HOST = os.environ.get('API_HOST')

if not API_HOST:
    if REPL_SLUG:
        API_HOST = f"https://{REPL_SLUG}.replit.app"
    else:
        API_HOST = "http://localhost:8000"

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

# Cards de planos
col1, col2, col3 = st.columns(3)

with col1:
    # Cabeçalho do plano mensal
    st.markdown("""
    <div style="text-align: center; margin-bottom: 0.5rem;">
        <h4 style="margin-bottom: 0.2rem; color: #1E366F;">Plano Mensal</h4>
        <p style="font-size: 1.5rem; font-weight: bold; color: #FF9800; margin: 0;">R$ 49,90<span style="font-size: 0.9rem; font-weight: normal; color: #777;"> /mês</span></p>
        <p style="font-size: 0.8rem; color: #555; margin-top: 0;">Pagamento recorrente mensal</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Botão alternativo para plano mensal (substituindo o Stripe para evitar erros)
    st.markdown("""
    <a href="/api/checkout/mensal" class="st-emotion-cache-19rxjzo edgvbvh10" style="background-color: #FF9800; color: white; text-align: center; padding: 12px; border-radius: 5px; font-weight: 600; display: block; text-decoration: none; width: 100%;">
        ASSINAR PLANO MENSAL
    </a>
    """, unsafe_allow_html=True)
    
    # Botão de fallback caso o Stripe não carregue
    if st.button("ASSINAR MENSAL (método alternativo)", type="primary", key="btn_mensal"):
        api_url = f"{API_HOST}/api/checkout/mensal"
        st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'{api_url}\'">', unsafe_allow_html=True)
        st.success("✅ Redirecionando para checkout...")

with col2:
    # Cabeçalho do plano anual
    st.markdown("""
    <div style="text-align: center; margin-bottom: 0.5rem;">
        <h4 style="margin-bottom: 0.2rem; color: #1E366F;">Plano Anual</h4>
        <p style="font-size: 1.5rem; font-weight: bold; color: #FF9800; margin: 0;">R$ 399,90<span style="font-size: 0.9rem; font-weight: normal; color: #777;"> /ano</span></p>
        <p style="font-size: 0.8rem; color: #555; margin-top: 0;">Economize R$ 198,90 (33%)</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Botão alternativo para plano anual
    st.markdown("""
    <a href="/api/checkout/anual" class="st-emotion-cache-19rxjzo edgvbvh10" style="background-color: #FF5722; color: white; text-align: center; padding: 12px; border-radius: 5px; font-weight: 600; display: block; text-decoration: none; width: 100%;">
        ASSINAR PLANO ANUAL
    </a>
    """, unsafe_allow_html=True)
    
    # Botão de fallback
    if st.button("ASSINAR ANUAL (método alternativo)", type="primary", key="btn_anual"):
        api_url = f"{API_HOST}/api/checkout/anual"
        st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'{api_url}\'">', unsafe_allow_html=True)
        st.success("✅ Redirecionando para checkout...")

with col3:
    # Cabeçalho do plano vitalício
    st.markdown("""
    <div style="text-align: center; margin-bottom: 0.5rem;">
        <h4 style="margin-bottom: 0.2rem; color: #1E366F;">Plano Vitalício</h4>
        <p style="font-size: 1.5rem; font-weight: bold; color: #FF9800; margin: 0;">R$ 999,90</p>
        <p style="font-size: 0.8rem; color: #555; margin-top: 0;">Pagamento único, acesso permanente</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Botão alternativo para plano vitalício
    st.markdown("""
    <a href="/api/checkout/vitalicio" class="st-emotion-cache-19rxjzo edgvbvh10" style="background-color: #FFC107; color: black; text-align: center; padding: 12px; border-radius: 5px; font-weight: 600; display: block; text-decoration: none; width: 100%;">
        ADQUIRIR PLANO VITALÍCIO
    </a>
    """, unsafe_allow_html=True)
    
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
    # Usando a mesma API de iniciar teste, mas exibindo a mensagem de redirecionamento
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