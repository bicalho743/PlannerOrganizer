import streamlit as st
import os

def exibir_planos_stripe_js():
    """
    Exibe planos com integração do Stripe via JavaScript
    """
    st.markdown("## Planos de Assinatura")
    
    # Obter a chave publicável do Stripe do ambiente
    stripe_publishable_key = os.environ.get("STRIPE_PUBLISHABLE_KEY")
    if not stripe_publishable_key:
        st.error("Chave publicável do Stripe não configurada!")
        return
    
    # CSS para os cards de planos
    st.markdown("""
    <style>
    .planos-container {
        display: flex;
        flex-wrap: wrap;
        gap: 20px;
        justify-content: center;
        margin-top: 2rem;
    }
    
    .plano-card {
        background: white;
        border-radius: 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        padding: 25px;
        width: 300px;
        text-align: center;
        transition: transform 0.3s;
    }
    
    .plano-card:hover {
        transform: translateY(-5px);
    }
    
    .plano-destaque {
        border: 2px solid #4CAF50;
        position: relative;
    }
    
    .plano-titulo {
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 15px;
        color: #1E366F;
    }
    
    .plano-preco {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 5px;
    }
    
    .plano-periodo {
        color: #757575;
        font-size: 0.9rem;
        margin-bottom: 15px;
    }
    
    .plano-economia {
        background-color: #1E88E5;
        color: white;
        font-weight: 600;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 0.7rem;
        display: inline-block;
        margin-bottom: 15px;
    }
    
    .plano-beneficios {
        text-align: left;
        margin-bottom: 25px;
    }
    
    .plano-beneficios ul {
        padding-left: 20px;
        list-style-type: none;
    }
    
    .plano-beneficios li {
        margin-bottom: 8px;
        position: relative;
        padding-left: 25px;
    }
    
    .plano-beneficios li:before {
        content: "✓";
        color: #4CAF50;
        position: absolute;
        left: 0;
        font-weight: bold;
    }
    
    .btn-assinar {
        background-color: #1E88E5;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 12px 20px;
        font-weight: 600;
        cursor: pointer;
        width: 100%;
        font-size: 1rem;
        transition: background-color 0.3s;
    }
    
    .btn-assinar:hover {
        background-color: #1565C0;
    }
    </style>
    """, unsafe_allow_html=True)

    # Script JavaScript para integração do Stripe
    st.markdown(f"""
    <script src="https://js.stripe.com/v3/"></script>
    <script>
        // Inicializar o Stripe com sua chave publicável
        var stripe = Stripe('{stripe_publishable_key}');
        
        // Função para iniciar o checkout para o plano mensal
        function checkoutMensal() {{
            stripe.redirectToCheckout({{
                lineItems: [{{
                    price: 'price_1RFBNXLWUPER7pUXzmz8cdsL',
                    quantity: 1
                }}],
                mode: 'subscription',
                successUrl: window.location.origin + '/sucesso',
                cancelUrl: window.location.origin + '/cancelado',
                clientReferenceId: 'mensal_' + Date.now()
            }}).then(function(result) {{
                if (result.error) {{
                    alert(result.error.message);
                }}
            }});
        }}
        
        // Função para iniciar o checkout para o plano anual
        function checkoutAnual() {{
            stripe.redirectToCheckout({{
                lineItems: [{{
                    price: 'price_1RFBTtLWUPER7pUXPt2Ajhgz',
                    quantity: 1
                }}],
                mode: 'subscription',
                successUrl: window.location.origin + '/sucesso',
                cancelUrl: window.location.origin + '/cancelado',
                clientReferenceId: 'anual_' + Date.now()
            }}).then(function(result) {{
                if (result.error) {{
                    alert(result.error.message);
                }}
            }});
        }}
        
        // Função para iniciar o checkout para o plano vitalício
        function checkoutVitalicio() {{
            stripe.redirectToCheckout({{
                lineItems: [{{
                    price: 'price_1RFBULLWUPER7pUXCiGZn3Jn',
                    quantity: 1
                }}],
                mode: 'payment',
                successUrl: window.location.origin + '/sucesso',
                cancelUrl: window.location.origin + '/cancelado',
                clientReferenceId: 'vitalicio_' + Date.now()
            }}).then(function(result) {{
                if (result.error) {{
                    alert(result.error.message);
                }}
            }});
        }}
    </script>
    """, unsafe_allow_html=True)
    
    # HTML dos cards de planos
    st.markdown("""
    <div class="planos-container">
        <!-- Plano Mensal -->
        <div class="plano-card">
            <div class="plano-titulo">📱 Plano Mensal</div>
            <div class="plano-preco">R$9,70</div>
            <div class="plano-periodo">por mês</div>
            <div style="background-color: #e6fff0; color: #00a651; padding: 5px; border-radius: 5px; text-align: center; margin-bottom: 15px; font-size: 12px; font-weight: bold;">✨ 7 DIAS DE TESTE GRÁTIS</div>
            <div class="plano-beneficios">
                <ul>
                    <li>Acesso a todos os recursos</li>
                    <li>Suporte prioritário</li>
                    <li>Atualizações gratuitas</li>
                    <li>Cancele quando quiser</li>
                    <li>Ideal para começar</li>
                </ul>
            </div>
            <button class="btn-assinar" onclick="checkoutMensal()">Assinar Plano Mensal</button>
        </div>
        
        <!-- Plano Anual -->
        <div class="plano-card plano-destaque">
            <div class="plano-titulo">📆 Plano Anual</div>
            <div class="plano-preco">R$97,00</div>
            <div class="plano-periodo">por ano</div>
            <div class="plano-economia">ECONOMIZE 17%</div>
            <div style="background-color: #e6fff0; color: #00a651; padding: 5px; border-radius: 5px; text-align: center; margin-bottom: 15px; font-size: 12px; font-weight: bold;">✨ 7 DIAS DE TESTE GRÁTIS</div>
            <div class="plano-beneficios">
                <ul>
                    <li>Acesso a todos os recursos</li>
                    <li>Suporte prioritário</li>
                    <li>Atualizações gratuitas</li>
                    <li>Treinamento personalizado</li>
                    <li>Melhor custo-benefício</li>
                </ul>
            </div>
            <button class="btn-assinar" onclick="checkoutAnual()">Assinar Plano Anual</button>
        </div>
        
        <!-- Plano Vitalício -->
        <div class="plano-card">
            <div class="plano-titulo">💎 Acesso Vitalício</div>
            <div class="plano-preco">R$247,00</div>
            <div class="plano-periodo">pagamento único</div>
            <div class="plano-economia">MELHOR VALOR A LONGO PRAZO</div>
            <div class="plano-beneficios">
                <ul>
                    <li>Acesso permanente ao sistema</li>
                    <li>Suporte prioritário</li>
                    <li>Sem mensalidades futuras</li>
                    <li>Todas as atualizações inclusas</li>
                    <li>Melhor para longo prazo</li>
                </ul>
            </div>
            <button class="btn-assinar" onclick="checkoutVitalicio()">Adquirir Acesso Vitalício</button>
        </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    st.set_page_config(
        page_title="Planos Planner Organizer",
        page_icon="📊",
        layout="wide"
    )
    exibir_planos_stripe_js()