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

# Configuração do Stripe
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY")
print(f"DEBUG: STRIPE_API_KEY presente: {'Sim' if STRIPE_API_KEY else 'Não'}")
print(f"DEBUG: STRIPE_PRICE_ID_MENSAL: {STRIPE_PRICE_ID_MENSAL}")
print(f"DEBUG: STRIPE_PRICE_ID_ANUAL: {STRIPE_PRICE_ID_ANUAL}")
print(f"DEBUG: STRIPE_PRICE_ID_VITALICIO: {STRIPE_PRICE_ID_VITALICIO}")

# Criamos URLs diretas de checkout do Stripe, sem precisar do nosso backend como intermediário
def criar_url_checkout_stripe(price_id):
    """
    Cria uma URL direta de checkout do Stripe sem passar pelo nosso backend
    Isso resolve o problema de sessão no FastAPI
    """
    import stripe
    
    if not STRIPE_API_KEY:
        print("ERRO: STRIPE_API_KEY não configurada!")
        return None  # Retorna None para tratamento adequado
    
    if not price_id:
        print("ERRO: price_id não fornecido!")
        return None  # Retorna None para tratamento adequado
    
    # Configurar a API do Stripe com a chave
    stripe.api_key = STRIPE_API_KEY
    
    # URLs de sucesso e cancelamento
    success_url = "http://localhost:5000/minha_assinatura?status=success"
    cancel_url = "http://localhost:5000/planos?status=cancel"
    
    try:
        print(f"Tentando criar sessão Stripe para price_id: {price_id}")
        # Criando a sessão diretamente com o Stripe
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1
            }],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
        )
        
        # Retornar a URL da sessão de checkout
        print(f"Sessão Stripe criada com sucesso: {checkout_session.url[:30]}...")
        return checkout_session.url
    except Exception as e:
        print(f"ERRO ao criar sessão de checkout Stripe: {str(e)}")
        return None

# Definir URL base para API (agora usando URLs relativas)
API_HOST = ""  # URLs relativas na mesma aplicação

# Não precisamos mais desta função, usaremos a função criar_url_checkout_stripe
# que cria URLs de checkout diretamente com a API Stripe

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

# Cards de planos com interface Streamlit nativa
st.markdown("### Conheça nossos planos", unsafe_allow_html=True)

# Layout com 3 colunas para os planos
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="border: 1px solid #e0e0e0; border-radius: 10px; padding: 20px; height: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <h3 style="color: #1E366F; text-align: center;">💡 Plano Mensal</h3>
        <div style="font-size: 2rem; color: #2196F3; text-align: center; font-weight: bold; margin: 15px 0 5px 0;">R$9,70</div>
        <div style="color: #757575; text-align: center; font-size: 0.9rem; margin-bottom: 20px;">por mês</div>
        <ul style="list-style-type: none; padding-left: 0;">
            <li style="margin: 10px 0;"><span style="color: #4CAF50; margin-right: 8px;">✓</span> Acesso a todos os recursos</li>
            <li style="margin: 10px 0;"><span style="color: #4CAF50; margin-right: 8px;">✓</span> Suporte por e-mail</li>
            <li style="margin: 10px 0;"><span style="color: #4CAF50; margin-right: 8px;">✓</span> Cancelamento a qualquer momento</li>
            <li style="margin: 10px 0;"><span style="color: #4CAF50; margin-right: 8px;">✓</span> Ideal para testar o sistema</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    # Tentar gerar URL direta do Stripe para o plano mensal
    url_checkout = None
    try:
        if STRIPE_PRICE_ID_MENSAL:
            url_checkout = criar_url_checkout_stripe(STRIPE_PRICE_ID_MENSAL)
        else:
            st.error("ID do plano mensal não configurado")
    except Exception as e:
        st.error(f"Erro ao gerar URL de checkout: {str(e)}")
        
    if url_checkout:
        # Abordagem com botão Streamlit nativo
        if st.button("ASSINAR MENSAL", key="mensal_btn", type="primary", use_container_width=True):
            # Abre o URL em uma nova aba - usando JavaScript
            js = f"""<script>window.open("{url_checkout}", "_blank");</script>"""
            st.markdown(js, unsafe_allow_html=True)
            st.success("✅ Redirecionando para página de pagamento...")
            
            # Solução alternativa caso o JavaScript não funcione
            st.markdown(f"**Se o navegador não abrir automaticamente, [clique aqui]({url_checkout})**")
    else:
        st.error("Não foi possível gerar o link de pagamento mensal")

with col2:
    st.markdown("""
    <div style="border: 1px solid #e0e0e0; border-radius: 10px; padding: 20px; height: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.1); position: relative; overflow: hidden;">
        <div style="position: absolute; top: 0; right: 0; background-color: #FF5722; color: white; padding: 5px 15px; transform: rotate(45deg) translate(15px, -15px); width: 150px; text-align: center; font-size: 0.8rem; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">RECOMENDADO</div>
        <h3 style="color: #1E366F; text-align: center;">🔥 Plano Anual</h3>
        <div style="font-size: 2rem; color: #2196F3; text-align: center; font-weight: bold; margin: 15px 0 5px 0;">R$97,00</div>
        <div style="color: #757575; text-align: center; font-size: 0.9rem; margin-bottom: 10px;">por ano</div>
        <div style="background-color: #E8F5E9; color: #2E7D32; padding: 5px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; display: block; text-align: center; margin: 10px auto;">ECONOMIZE 17%</div>
        <ul style="list-style-type: none; padding-left: 0;">
            <li style="margin: 10px 0;"><span style="color: #4CAF50; margin-right: 8px;">✓</span> Acesso a todos os recursos</li>
            <li style="margin: 10px 0;"><span style="color: #4CAF50; margin-right: 8px;">✓</span> Suporte prioritário</li>
            <li style="margin: 10px 0;"><span style="color: #4CAF50; margin-right: 8px;">✓</span> Atualizações gratuitas</li>
            <li style="margin: 10px 0;"><span style="color: #4CAF50; margin-right: 8px;">✓</span> Treinamento personalizado</li>
            <li style="margin: 10px 0;"><span style="color: #4CAF50; margin-right: 8px;">✓</span> Melhor custo-benefício</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    # Tentar gerar URL direta do Stripe para o plano anual
    url_checkout = None
    try:
        if STRIPE_PRICE_ID_ANUAL:
            url_checkout = criar_url_checkout_stripe(STRIPE_PRICE_ID_ANUAL)
        else:
            st.error("ID do plano anual não configurado")
    except Exception as e:
        st.error(f"Erro ao gerar URL de checkout: {str(e)}")
        
    if url_checkout:
        # Abordagem com botão Streamlit nativo
        if st.button("ASSINAR ANUAL", key="anual_btn", type="primary", use_container_width=True):
            # Abre o URL em uma nova aba - usando JavaScript
            js = f"""<script>window.open("{url_checkout}", "_blank");</script>"""
            st.markdown(js, unsafe_allow_html=True)
            st.success("✅ Redirecionando para página de pagamento...")
            
            # Solução alternativa caso o JavaScript não funcione
            st.markdown(f"**Se o navegador não abrir automaticamente, [clique aqui]({url_checkout})**")
    else:
        st.error("Não foi possível gerar o link de pagamento anual")

with col3:
    st.markdown("""
    <div style="border: 1px solid #e0e0e0; border-radius: 10px; padding: 20px; height: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <h3 style="color: #1E366F; text-align: center;">🏆 Acesso Vitalício</h3>
        <div style="font-size: 2rem; color: #2196F3; text-align: center; font-weight: bold; margin: 15px 0 5px 0;">R$247,00</div>
        <div style="color: #757575; text-align: center; font-size: 0.9rem; margin-bottom: 20px;">pagamento único</div>
        <ul style="list-style-type: none; padding-left: 0;">
            <li style="margin: 10px 0;"><span style="color: #4CAF50; margin-right: 8px;">✓</span> Acesso permanente ao sistema</li>
            <li style="margin: 10px 0;"><span style="color: #4CAF50; margin-right: 8px;">✓</span> Suporte prioritário</li>
            <li style="margin: 10px 0;"><span style="color: #4CAF50; margin-right: 8px;">✓</span> Sem mensalidades futuras</li>
            <li style="margin: 10px 0;"><span style="color: #4CAF50; margin-right: 8px;">✓</span> Todas as atualizações inclusas</li>
            <li style="margin: 10px 0;"><span style="color: #4CAF50; margin-right: 8px;">✓</span> Melhor para longo prazo</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    # Tentar gerar URL direta do Stripe para o plano vitalício
    url_checkout = None
    try:
        if STRIPE_PRICE_ID_VITALICIO:
            url_checkout = criar_url_checkout_stripe(STRIPE_PRICE_ID_VITALICIO)
        else:
            st.error("ID do plano vitalício não configurado")
    except Exception as e:
        st.error(f"Erro ao gerar URL de checkout: {str(e)}")
        
    if url_checkout:
        # Abordagem com botão Streamlit nativo
        if st.button("COMPRAR VITALÍCIO", key="vitalicio_btn", type="primary", use_container_width=True):
            # Abre o URL em uma nova aba - usando JavaScript
            js = f"""<script>window.open("{url_checkout}", "_blank");</script>"""
            st.markdown(js, unsafe_allow_html=True)
            st.success("✅ Redirecionando para página de pagamento...")
            
            # Solução alternativa caso o JavaScript não funcione
            st.markdown(f"**Se o navegador não abrir automaticamente, [clique aqui]({url_checkout})**")
    else:
        st.error("Não foi possível gerar o link de pagamento vitalício")

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

# Removemos o JavaScript redundante já que estamos usando botões Streamlit

# Testar período gratuito
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### Não está pronto para assinar?")
st.markdown("Experimente grátis por 7 dias sem necessidade de cartão de crédito.")

# Para o botão de teste gratuito, vamos usar uma abordagem diferente
# Neste caso, vamos usar um botão normal do Streamlit que redireciona para uma página simples
# de cadastro para iniciar o teste

if st.button("INICIAR TESTE GRATUITO", type="primary", key="teste_btn", use_container_width=False):
    # Redirecionando para a página de teste, que não necessita de middleware
    st.page_link("/pages/iniciar_teste.py", label="Iniciar teste gratuito", icon="🔄")