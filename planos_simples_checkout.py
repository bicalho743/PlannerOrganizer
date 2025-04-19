import streamlit as st
import os
import webbrowser

def checkout_mensal():
    """
    Redireciona o usuário para a página de checkout do plano mensal no Stripe.
    """
    url = "https://buy.stripe.com/test_14k3dG3pL3rI6KQ000"
    st.info(f"Redirecionando para a página de checkout do plano mensal... Se a página não abrir automaticamente, [clique aqui]({url}).")
    st.markdown(f"""
    <meta http-equiv="refresh" content="0; url={url}">
    <script>
        window.location.href = "{url}";
    </script>
    """, unsafe_allow_html=True)

def checkout_anual():
    """
    Redireciona o usuário para a página de checkout do plano anual no Stripe.
    """
    url = "https://buy.stripe.com/test_5kA9F26BP1jA4CI004"
    st.info(f"Redirecionando para a página de checkout do plano anual... Se a página não abrir automaticamente, [clique aqui]({url}).")
    st.markdown(f"""
    <meta http-equiv="refresh" content="0; url={url}">
    <script>
        window.location.href = "{url}";
    </script>
    """, unsafe_allow_html=True)

def checkout_vitalicio():
    """
    Redireciona o usuário para a página de checkout do plano vitalício no Stripe.
    """
    url = "https://buy.stripe.com/test_aEU9F26BPeSEbZ6005"
    st.info(f"Redirecionando para a página de checkout do plano vitalício... Se a página não abrir automaticamente, [clique aqui]({url}).")
    st.markdown(f"""
    <meta http-equiv="refresh" content="0; url={url}">
    <script>
        window.location.href = "{url}";
    </script>
    """, unsafe_allow_html=True)

def checkout_direto_api():
    """
    Cria uma sessão de checkout usando a API do Stripe e redireciona o usuário.
    """
    import stripe
    
    stripe_api_key = os.environ.get("STRIPE_API_KEY")
    
    if not stripe_api_key:
        st.error("Chave API do Stripe não configurada!")
        return
    
    stripe.api_key = stripe_api_key
    
    try:
        # Criar uma sessão de checkout
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price": "price_1RFBNXLWUPER7pUXzmz8cdsL",  # ID do preço do plano mensal
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url="https://suaurl.com/sucesso",
            cancel_url="https://suaurl.com/cancelado",
        )
        
        # Redirecionar para a URL de checkout
        url = checkout_session.url
        st.info(f"Redirecionando para o checkout do Stripe... Se a página não abrir automaticamente, [clique aqui]({url}).")
        st.markdown(f"""
        <meta http-equiv="refresh" content="0; url={url}">
        <script>
            window.location.href = "{url}";
        </script>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Erro ao criar a sessão de checkout: {str(e)}")

if __name__ == "__main__":
    st.set_page_config(
        page_title="Checkout - Planner Organizer",
        page_icon="📊",
        layout="centered"
    )
    
    # Verificar qual plano foi solicitado através do parâmetro de URL
    query_params = st.experimental_get_query_params()
    plano = query_params.get("plano", [""])[0]
    
    if plano == "mensal":
        checkout_mensal()
    elif plano == "anual":
        checkout_anual()
    elif plano == "vitalicio":
        checkout_vitalicio()
    elif plano == "api":
        checkout_direto_api()
    else:
        st.error("Plano não especificado ou inválido.")
        st.markdown("""
        Por favor, selecione um plano válido:
        - [Plano Mensal](planos_simples_checkout.py?plano=mensal)
        - [Plano Anual](planos_simples_checkout.py?plano=anual)
        - [Plano Vitalício](planos_simples_checkout.py?plano=vitalicio)
        """)