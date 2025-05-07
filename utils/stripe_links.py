import os
import streamlit as st
import logging

logger = logging.getLogger(__name__)

# URLs dos planos (definidas estaticamente para teste)
# Estas URLs são diretas para o Stripe e não expiram
MENSAL_URL = "https://buy.stripe.com/test_28og2t34LeLJ6mQ144" 
ANUAL_URL = "https://buy.stripe.com/test_7sI7vRcJ56T29z8dQQ"
VITALICIO_URL = "https://buy.stripe.com/test_eVa2bv34L1Aw29yfYZ"

# Configurações de preços do Stripe para APIs
STRIPE_PRICE_ID_MENSAL = os.environ.get('STRIPE_PRICE_ID_MENSAL')
STRIPE_PRICE_ID_ANUAL = os.environ.get('STRIPE_PRICE_ID_ANUAL')
STRIPE_PRICE_ID_VITALICIO = os.environ.get('STRIPE_PRICE_ID_VITALICIO')

def exibir_planos_streamlit():
    """
    Exibe os planos usando links diretos do Stripe em vez de botões JavaScript
    para evitar problemas com o React.
    """
    # Injetar CSS
    st.markdown("""
    <style>
        /* Cartões de preços */
        .planos-container {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 20px;
            margin: 20px 0;
        }
        
        .plano-card {
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            padding: 25px;
            width: 280px;
            position: relative;
            overflow: hidden;
        }
        
        .plano-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 12px rgba(0,0,0,0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .destaque {
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
        
        .plano-titulo {
            color: #1E366F;
            font-size: 1.5rem;
            margin-bottom: 15px;
            text-align: center;
        }
        
        .plano-preco {
            font-size: 2.5rem;
            font-weight: bold;
            color: #2196F3;
            margin: 15px 0 5px;
            text-align: center;
        }
        
        .plano-periodo {
            color: #757575;
            font-size: 0.9rem;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .recursos-lista {
            text-align: left;
            list-style-type: none;
            padding: 0;
            margin: 20px 0;
        }
        
        .recursos-lista li {
            margin: 10px 0;
            padding-left: 25px;
            position: relative;
        }
        
        .recursos-lista li:before {
            content: "✓";
            color: #4CAF50;
            position: absolute;
            left: 0;
        }
        
        .economia {
            background-color: #E8F5E9;
            color: #2E7D32;
            padding: 5px 10px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
            display: inline-block;
            margin-top: 5px;
            text-align: center;
            width: 100%;
        }
        
        /* Links de checkout */
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
    
    # Exibir cabeçalho
    st.title("Planner Organizer")
    st.header("Escolha o plano ideal para você")
    
    # Exibir cards de planos
    st.markdown(f"""
    <div class="planos-container">
        <!-- Plano Mensal -->
        <div class="plano-card">
            <h3 class="plano-titulo">Plano Mensal</h3>
            <div class="plano-preco">R$9,70</div>
            <div class="plano-periodo">por mês</div>
            
            <ul class="recursos-lista">
                <li>Acesso a todos os recursos</li>
                <li>Suporte por e-mail</li>
                <li>Cancelamento a qualquer momento</li>
                <li>Ideal para testar o sistema</li>
            </ul>
            
            <a href="{MENSAL_URL}" target="_blank" class="checkout-link">
                ASSINAR MENSAL
            </a>
        </div>
        
        <!-- Plano Anual -->
        <div class="plano-card">
            <div class="destaque">RECOMENDADO</div>
            <h3 class="plano-titulo">Plano Anual</h3>
            <div class="plano-preco">R$97,00</div>
            <div class="plano-periodo">por ano</div>
            <div class="economia">ECONOMIZE 17%</div>
            
            <ul class="recursos-lista">
                <li>Acesso a todos os recursos</li>
                <li>Suporte prioritário</li>
                <li>Atualizações gratuitas</li>
                <li>Treinamento personalizado</li>
                <li>Melhor custo-benefício</li>
            </ul>
            
            <a href="{ANUAL_URL}" target="_blank" class="checkout-link anual">
                ASSINAR ANUAL
            </a>
        </div>
        
        <!-- Plano Vitalício -->
        <div class="plano-card">
            <h3 class="plano-titulo">Acesso Vitalício</h3>
            <div class="plano-preco">R$247,00</div>
            <div class="plano-periodo">pagamento único</div>
            
            <ul class="recursos-lista">
                <li>Acesso permanente ao sistema</li>
                <li>Suporte prioritário</li>
                <li>Sem mensalidades futuras</li>
                <li>Acesso a todas as atualizações</li>
                <li>Melhor para longo prazo</li>
            </ul>
            
            <a href="{VITALICIO_URL}" target="_blank" class="checkout-link vitalicio">
                COMPRAR VITALÍCIO
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Rodapé
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: center;">
        <h3>Não está pronto para assinar?</h3>
        <p>Experimente grátis por 7 dias sem necessidade de cartão de crédito.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Botão usando Streamlit nativo (sem JavaScript)
    if st.button("INICIAR TESTE GRATUITO", type="primary"):
        st.page_link("/pages/iniciar_teste.py", label="Iniciar teste gratuito de 7 dias", icon="🔄")