"""
Módulo de funções auxiliares para a página de planos e integração com Stripe
Este módulo usa utils/stripe_handler.py para interagir com a API do Stripe
"""

import streamlit as st
import logging
from utils.stripe_handler import (
    criar_url_checkout_stripe,
    obter_price_id_por_plano,
    verificar_configuracao_stripe,
    STRIPE_PRICE_ID_MENSAL,
    STRIPE_PRICE_ID_ANUAL,
    STRIPE_PRICE_ID_VITALICIO,
    STRIPE_API_KEY
)

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def criar_botao_checkout_stripe(plano: str, texto_botao: str = None, 
                              usar_container_width: bool = True, tipo: str = "primary") -> bool:
    """
    Cria um botão Streamlit que redireciona para o checkout do Stripe quando clicado
    
    Args:
        plano: Nome do plano (Mensal, Anual, Vitalício)
        texto_botao: Texto a ser exibido no botão (opcional)
        usar_container_width: Se o botão deve ocupar toda a largura do container
        tipo: Tipo do botão (primary, secondary)
        
    Returns:
        bool: True se o botão foi clicado e o URL foi gerado com sucesso
    """
    # Determinar o texto do botão
    if not texto_botao:
        texto_botao = f"ASSINAR {plano.upper()}"
    
    # Obter o price_id para o plano
    price_id = obter_price_id_por_plano(plano)
    
    # Verificar se temos um price_id válido para o plano
    if not price_id:
        st.error(f"ID do plano {plano} não está configurado")
        return False
    
    # Criar o botão Streamlit
    if st.button(texto_botao, type=tipo, key=f"{plano.lower()}_btn", use_container_width=usar_container_width):
        # Tentar criar a URL de checkout
        checkout_url = criar_url_checkout_stripe(price_id)
        
        if checkout_url:
            # Abre o URL em uma nova aba - usando JavaScript
            js = f"""<script>window.open("{checkout_url}", "_blank");</script>"""
            st.markdown(js, unsafe_allow_html=True)
            st.success(f"✅ Redirecionando para página de pagamento do plano {plano}...")
            
            # Solução alternativa caso o JavaScript não funcione
            st.markdown(f"**Se o navegador não abrir automaticamente, [clique aqui]({checkout_url})**")
            return True
        else:
            st.error(f"Não foi possível gerar o link de pagamento para o plano {plano}")
            return False
    
    return False

def mostrar_secao_planos(layout_colunas: bool = True) -> None:
    """
    Mostra a seção de planos com opções para assinar
    
    Args:
        layout_colunas: Se deve usar layout de colunas (True) ou cards (False)
    """
    # Verificar configuração do Stripe
    config = verificar_configuracao_stripe()
    if not config["api_key"]:
        st.error("⚠️ Configuração do Stripe incompleta: API Key não configurada")
    
    missing_prices = []
    if not config["price_mensal"]:
        missing_prices.append("Mensal")
    if not config["price_anual"]:
        missing_prices.append("Anual")
    if not config["price_vitalicio"]:
        missing_prices.append("Vitalício")
    
    if missing_prices:
        st.warning(f"⚠️ Preços não configurados: {', '.join(missing_prices)}")
    
    # Layout em colunas
    if layout_colunas:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 💡 Plano Mensal")
            st.markdown("#### R$ 9,70")
            st.markdown("*por mês*")
            st.markdown("- ✓ Acesso a todos os recursos")
            st.markdown("- ✓ Suporte por e-mail")
            st.markdown("- ✓ Cancelamento a qualquer momento")
            
            criar_botao_checkout_stripe("Mensal")
        
        with col2:
            st.markdown("### 🔥 Plano Anual")
            st.markdown("#### R$ 97,00")
            st.markdown("*por ano (economia de 17%)*")
            st.markdown("- ✓ Acesso a todos os recursos")
            st.markdown("- ✓ Suporte prioritário")
            st.markdown("- ✓ Atualizações gratuitas")
            
            criar_botao_checkout_stripe("Anual")
        
        with col3:
            st.markdown("### 🏆 Acesso Vitalício")
            st.markdown("#### R$ 247,00")
            st.markdown("*pagamento único*")
            st.markdown("- ✓ Acesso permanente ao sistema")
            st.markdown("- ✓ Suporte prioritário")
            st.markdown("- ✓ Sem mensalidades futuras")
            
            criar_botao_checkout_stripe("Vitalício")
    
    # Layout com cards via HTML
    else:
        st.markdown("""
        <style>
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
            width: 100%;
            max-width: 300px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        .pricing-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 12px rgba(0,0,0,0.1);
        }
        .pricing-title {
            color: #1E366F;
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 15px;
            text-align: center;
        }
        .pricing-price {
            font-size: 2.5rem;
            font-weight: 700;
            color: #2196F3;
            text-align: center;
            margin: 15px 0 5px 0;
        }
        .pricing-period {
            color: #666;
            text-align: center;
            font-size: 0.9rem;
            margin-bottom: 20px;
        }
        .feature-list {
            margin: 20px 0;
            padding-left: 0;
            list-style-type: none;
        }
        .feature-list li {
            padding: 5px 0;
            padding-left: 25px;
            position: relative;
        }
        .feature-list li:before {
            content: "✓";
            color: #4CAF50;
            position: absolute;
            left: 0;
        }
        </style>
        
        <div class="pricing-container">
            <!-- Plano Mensal -->
            <div class="pricing-card">
                <div class="pricing-title">💡 Plano Mensal</div>
                <div class="pricing-price">R$ 9,70</div>
                <div class="pricing-period">por mês</div>
                <ul class="feature-list">
                    <li>Acesso a todos os recursos</li>
                    <li>Suporte por e-mail</li>
                    <li>Cancelamento a qualquer momento</li>
                </ul>
            </div>
            
            <!-- Plano Anual -->
            <div class="pricing-card">
                <div class="pricing-title">🔥 Plano Anual</div>
                <div class="pricing-price">R$ 97,00</div>
                <div class="pricing-period">por ano (economia de 17%)</div>
                <ul class="feature-list">
                    <li>Acesso a todos os recursos</li>
                    <li>Suporte prioritário</li>
                    <li>Atualizações gratuitas</li>
                </ul>
            </div>
            
            <!-- Plano Vitalício -->
            <div class="pricing-card">
                <div class="pricing-title">🏆 Acesso Vitalício</div>
                <div class="pricing-price">R$ 247,00</div>
                <div class="pricing-period">pagamento único</div>
                <ul class="feature-list">
                    <li>Acesso permanente ao sistema</li>
                    <li>Suporte prioritário</li>
                    <li>Sem mensalidades futuras</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Adicionar botões do Streamlit abaixo dos cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            criar_botao_checkout_stripe("Mensal", "ASSINAR MENSAL")
        
        with col2:
            criar_botao_checkout_stripe("Anual", "ASSINAR ANUAL") 
        
        with col3:
            criar_botao_checkout_stripe("Vitalício", "COMPRAR VITALÍCIO")