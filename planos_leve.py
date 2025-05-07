import streamlit as st
import os

# Configuração da página
st.set_page_config(
    page_title="Planos - Planner Organizer",
    page_icon="🏆",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Variáveis do Stripe diretamente de environment
STRIPE_PRICE_ID_MENSAL = os.environ.get('STRIPE_PRICE_ID_MENSAL')
STRIPE_PRICE_ID_ANUAL = os.environ.get('STRIPE_PRICE_ID_ANUAL')
STRIPE_PRICE_ID_VITALICIO = os.environ.get('STRIPE_PRICE_ID_VITALICIO')

# URLs dos planos (definidas estaticamente para teste)
MENSAL_URL = "https://buy.stripe.com/test_28og2t34LeLJ6mQ144" 
ANUAL_URL = "https://buy.stripe.com/test_7sI7vRcJ56T29z8dQQ"
VITALICIO_URL = "https://buy.stripe.com/test_eVa2bv34L1Aw29yfYZ"

def obter_link_checkout(plano):
    """
    Retorna links diretos para checkout do Stripe.
    Esses links são gerados direto no dashboard do Stripe e nunca expiram.
    """
    if plano == 'mensal':
        return MENSAL_URL
    elif plano == 'anual':
        return ANUAL_URL
    elif plano == 'vitalicio':
        return VITALICIO_URL
    return "#"

# Verificar se o arquivo HTML existe
html_path = 'planos_html.html'
if os.path.exists(html_path):
    with open(html_path, 'r', encoding='utf-8') as file:
        html_content = file.read()
    
    # Exibir o HTML diretamente
    st.components.v1.html(html_content, height=1200, scrolling=True)
else:
    # Fallback se o arquivo HTML não existir
    st.title("Planner Organizer")
    st.header("Escolha o plano ideal para você")
    
    # Usar colunas para layout
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Mensal")
        st.write("R$ 9,70 / mês")
        st.markdown("- Acesso a todos os recursos")
        st.markdown("- Suporte por e-mail")
        st.markdown("- Cancelamento a qualquer momento")
        st.link_button("ASSINAR MENSAL", obter_link_checkout('mensal'))
    
    with col2:
        st.subheader("Anual")
        st.write("R$ 97,00 / ano")
        st.info("ECONOMIZE 17%")
        st.markdown("- Acesso a todos os recursos")
        st.markdown("- Suporte prioritário")
        st.markdown("- Atualizações gratuitas")
        st.markdown("- Treinamento personalizado")
        st.link_button("ASSINAR ANUAL", obter_link_checkout('anual'), type="primary")
    
    with col3:
        st.subheader("Vitalício")
        st.write("R$ 247,00 (pagamento único)")
        st.markdown("- Acesso permanente ao sistema")
        st.markdown("- Suporte prioritário")
        st.markdown("- Sem mensalidades futuras")
        st.markdown("- Acesso a todas as atualizações")
        st.link_button("COMPRAR VITALÍCIO", obter_link_checkout('vitalicio'))
    
    # Separador
    st.divider()
    
    # Seção de teste gratuito
    st.subheader("Não está pronto para assinar?")
    st.write("Experimente grátis por 7 dias sem necessidade de cartão de crédito.")
    st.button("INICIAR TESTE GRATUITO", type="primary")