import streamlit as st
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importar funções do novo módulo de gerenciamento do Stripe
from utils.stripe_handler import (
    criar_url_checkout_stripe,
    obter_price_id_por_plano,
    verificar_configuracao_stripe,
    STRIPE_PRICE_ID_MENSAL,
    STRIPE_PRICE_ID_ANUAL,
    STRIPE_PRICE_ID_VITALICIO,
    STRIPE_API_KEY
)

def main():
    st.set_page_config(
        page_title="Teste Checkout Stripe",
        page_icon="💳",
        layout="centered"
    )
    
    st.title("Teste de Integração Direta com Stripe")
    st.subheader("Ferramenta para testar a geração de URLs de checkout")
    
    # Interface básica para escolher o plano
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### Dados de Configuração")
        st.write(f"API Key presente: {'✅' if STRIPE_API_KEY else '❌'}")
        st.write(f"Price ID Mensal: {'✅' if STRIPE_PRICE_ID_MENSAL else '❌'}")
        st.write(f"Price ID Anual: {'✅' if STRIPE_PRICE_ID_ANUAL else '❌'}")
        st.write(f"Price ID Vitalício: {'✅' if STRIPE_PRICE_ID_VITALICIO else '❌'}")
    
    with col2:
        plano = st.radio("Selecione o plano:", ["Mensal", "Anual", "Vitalício"])
        
        # Determinar o price_id com base no plano selecionado
        price_id = None
        if plano == "Mensal":
            price_id = STRIPE_PRICE_ID_MENSAL
        elif plano == "Anual":
            price_id = STRIPE_PRICE_ID_ANUAL
        elif plano == "Vitalício":
            price_id = STRIPE_PRICE_ID_VITALICIO
    
    # Botão para gerar URL de checkout
    if st.button("Gerar URL de Checkout", type="primary", use_container_width=True):
        # Verificar se temos um price_id
        if not price_id:
            st.error(f"Price ID para o plano {plano} não está configurado!")
        else:
            # Criar URL de checkout
            with st.spinner("Gerando URL de checkout..."):
                checkout_url = criar_url_checkout_stripe(price_id)
            
            if checkout_url:
                st.success("✅ URL de checkout gerada com sucesso!")
                
                # Mostrar a URL
                st.code(checkout_url)
                
                # Opção para abrir em nova aba
                st.markdown(f"""
                <a href="{checkout_url}" target="_blank">
                    <button style="background-color: #4CAF50; color: white; border: none; border-radius: 5px; padding: 10px; cursor: pointer; width: 100%;">
                        Abrir Checkout em Nova Aba
                    </button>
                </a>
                """, unsafe_allow_html=True)
                
                # Abre o URL em uma nova aba - usando JavaScript
                js = f"""<script>window.open("{checkout_url}", "_blank");</script>"""
                st.markdown(js, unsafe_allow_html=True)
            else:
                st.error("❌ Falha ao gerar URL de checkout!")
    
    # Explicação
    st.markdown("---")
    st.markdown("""
    ### Como funciona
    
    1. Este teste usa a API do Stripe diretamente, sem depender da nossa API FastAPI
    2. A sessão de checkout é criada diretamente, evitando problemas de sessão
    3. O URL gerado redireciona para o Stripe, onde o usuário pode concluir o pagamento
    
    ### Requisitos
    
    - STRIPE_API_KEY: Chave secreta do Stripe para autenticação
    - STRIPE_PRICE_ID_*: IDs dos preços configurados no Stripe para cada plano
    """)

# Executar a aplicação
if __name__ == "__main__":
    main()