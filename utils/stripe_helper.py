"""
Módulo auxiliar para integração com Stripe.
Este módulo fornece funções para interagir com a API do Stripe
e facilitar a integração com os planos de assinatura.
"""

import os
import json
import logging
import stripe
import streamlit as st
from typing import Dict, List, Optional, Any, Tuple

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variáveis para configuração do Stripe
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

# URL base do site (para redirecionamentos)
BASE_URL = os.environ.get("BASE_URL", "http://localhost:5000")

# Inicializar stripe se a chave estiver disponível
if STRIPE_API_KEY:
    stripe.api_key = STRIPE_API_KEY
    logger.info("Stripe API configurada com sucesso")
else:
    logger.warning("STRIPE_API_KEY não encontrada! A API do Stripe não funcionará corretamente.")


def get_stripe_status() -> Dict[str, Any]:
    """
    Verifica se o Stripe está configurado corretamente.
    
    Returns:
        Dict[str, Any]: Dicionário com status da configuração do Stripe
    """
    return {
        "configured": bool(STRIPE_API_KEY and STRIPE_PUBLISHABLE_KEY),
        "api_key_set": bool(STRIPE_API_KEY),
        "publishable_key_set": bool(STRIPE_PUBLISHABLE_KEY),
        "webhook_secret_set": bool(STRIPE_WEBHOOK_SECRET)
    }


def format_price(amount: int, currency: str = "brl") -> str:
    """
    Formata um preço de acordo com a moeda.
    
    Args:
        amount: Valor em centavos
        currency: Código da moeda (padrão: brl)
        
    Returns:
        str: Preço formatado
    """
    # Converter de centavos para valor decimal
    value = amount / 100.0
    
    if currency.lower() == "brl":
        return f"R$ {value:.2f}".replace(".", ",")
    elif currency.lower() == "usd":
        return f"US$ {value:.2f}"
    else:
        return f"{value:.2f} {currency.upper()}"


def get_all_products_and_prices() -> List[Dict[str, Any]]:
    """
    Obtém todos os produtos e preços ativos do Stripe.
    
    Returns:
        List[Dict[str, Any]]: Lista de produtos com seus preços
    """
    if not STRIPE_API_KEY:
        logger.warning("Tentativa de listar produtos sem API key configurada")
        return []
    
    try:
        # Buscar todos os produtos ativos
        products = stripe.Product.list(active=True)
        
        # Buscar todos os preços ativos
        prices = stripe.Price.list(active=True)
        
        # Mapear preços para produtos
        price_map = {}
        for price in prices.auto_paging_iter():
            if price.product not in price_map:
                price_map[price.product] = []
            
            price_data = {
                "id": price.id,
                "currency": price.currency,
                "unit_amount": price.unit_amount,
                "formatted_price": format_price(price.unit_amount or 0, price.currency),
                "type": price.type,
                "recurring": None
            }
            
            # Adicionar informações de recorrência se for uma assinatura
            if hasattr(price, 'recurring') and price.recurring:
                price_data["recurring"] = {
                    "interval": price.recurring.interval,
                    "interval_count": price.recurring.interval_count
                }
                
                # Adicionar descrição amigável do período
                if price.recurring.interval == "month":
                    if price.recurring.interval_count == 1:
                        price_data["interval_description"] = "mensal"
                    else:
                        price_data["interval_description"] = f"a cada {price.recurring.interval_count} meses"
                elif price.recurring.interval == "year":
                    if price.recurring.interval_count == 1:
                        price_data["interval_description"] = "anual"
                    else:
                        price_data["interval_description"] = f"a cada {price.recurring.interval_count} anos"
                elif price.recurring.interval == "week":
                    if price.recurring.interval_count == 1:
                        price_data["interval_description"] = "semanal"
                    else:
                        price_data["interval_description"] = f"a cada {price.recurring.interval_count} semanas"
                elif price.recurring.interval == "day":
                    if price.recurring.interval_count == 1:
                        price_data["interval_description"] = "diário"
                    else:
                        price_data["interval_description"] = f"a cada {price.recurring.interval_count} dias"
            
            price_map[price.product].append(price_data)
        
        # Construir a resposta
        result = []
        for product in products.auto_paging_iter():
            product_info = {
                "id": product.id,
                "name": product.name,
                "description": product.description or "",
                "images": product.images,
                "metadata": product.metadata,
                "prices": price_map.get(product.id, [])
            }
            
            # Filtrar para produtos do tipo assinatura (via metadados)
            if product.metadata.get("type") == "subscription":
                result.append(product_info)
        
        # Ordenar por ordem (se presente nos metadados)
        result.sort(key=lambda p: int(p.get("metadata", {}).get("order", "999")))
        
        return result
        
    except Exception as e:
        logger.error(f"Erro ao listar produtos do Stripe: {str(e)}")
        return []


def create_checkout_session(
    price_id: str, 
    success_url: Optional[str] = None,
    cancel_url: Optional[str] = None,
    customer_email: Optional[str] = None,
    metadata: Optional[Dict[str, str]] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Cria uma sessão de checkout do Stripe para um pagamento único ou assinatura.
    
    Args:
        price_id: ID do preço do Stripe
        success_url: URL de redirecionamento após sucesso
        cancel_url: URL de redirecionamento após cancelamento
        customer_email: Email do cliente (opcional)
        metadata: Metadados adicionais para a sessão (opcional)
        
    Returns:
        Tuple[bool, Dict[str, Any]]: (Sucesso, Dados da sessão ou erro)
    """
    if not STRIPE_API_KEY:
        logger.warning("Tentativa de criar sessão de checkout sem API key configurada")
        return False, {"error": "Stripe não configurado"}
    
    # URLs padrão se não forem especificadas
    if not success_url:
        success_url = f"{BASE_URL}/success?session_id={{CHECKOUT_SESSION_ID}}"
    if not cancel_url:
        cancel_url = f"{BASE_URL}/cancel"
    
    try:
        # Configurar os dados da sessão
        checkout_data = {
            "success_url": success_url,
            "cancel_url": cancel_url,
            "payment_method_types": ["card"],
            "mode": "subscription",
            "line_items": [
                {
                    "price": price_id,
                    "quantity": 1,
                }
            ],
        }
        
        # Adicionar email do cliente se fornecido
        if customer_email:
            checkout_data["customer_email"] = customer_email
            
        # Adicionar metadados se fornecidos
        if metadata:
            checkout_data["metadata"] = metadata
        
        # Criar a sessão no Stripe
        session = stripe.checkout.Session.create(**checkout_data)
        
        return True, {"id": session.id, "url": session.url}
        
    except Exception as e:
        logger.error(f"Erro ao criar sessão do Stripe: {str(e)}")
        return False, {"error": str(e)}


def render_checkout_button(price_id: str, button_text: str = "Assinar", key: Optional[str] = None) -> None:
    """
    Renderiza um botão de checkout do Stripe usando Streamlit.
    
    Args:
        price_id: ID do preço do Stripe
        button_text: Texto a ser exibido no botão
        key: Chave única para o botão (opcional)
    """
    button_key = key or f"checkout_button_{price_id}"
    
    if st.button(button_text, key=button_key):
        # Criar a sessão de checkout
        success, result = create_checkout_session(
            price_id=price_id,
            # URLs padrão serão utilizadas
        )
        
        if success:
            # Redirecionar para a URL de checkout do Stripe
            st.markdown(f"<meta http-equiv='refresh' content='0;url={result['url']}'>", unsafe_allow_html=True)
            st.info("Redirecionando para o Stripe Checkout...")
            st.markdown(f"Se não for redirecionado automaticamente, [clique aqui]({result['url']})")
        else:
            st.error(f"Erro ao processar o checkout: {result.get('error', 'Erro desconhecido')}")
            if not STRIPE_API_KEY:
                st.warning("Stripe não está configurado. Configure a variável de ambiente STRIPE_API_KEY.")


def get_checkout_js_snippet(publishable_key: Optional[str] = None) -> str:
    """
    Retorna o snippet JavaScript para integração com o Stripe Checkout.
    
    Args:
        publishable_key: Chave publicável do Stripe (opcional)
        
    Returns:
        str: Snippet JavaScript
    """
    key = publishable_key or STRIPE_PUBLISHABLE_KEY
    
    return f"""
    <script src="https://js.stripe.com/v3/"></script>
    <script>
        const stripe = Stripe('{key}');
        
        function redirectToCheckout(sessionId) {{
            stripe.redirectToCheckout({{
                sessionId: sessionId
            }}).then(function (result) {{
                if (result.error) {{
                    console.error(result.error.message);
                    alert('Erro ao processar o pagamento: ' + result.error.message);
                }}
            }});
        }}
    </script>
    """


def get_subscription_info(subscription_id: str) -> Dict[str, Any]:
    """
    Obtém informações detalhadas de uma assinatura específica.
    
    Args:
        subscription_id: ID da assinatura do Stripe
        
    Returns:
        Dict[str, Any]: Informações da assinatura
    """
    if not STRIPE_API_KEY:
        logger.warning("Tentativa de buscar assinatura sem API key configurada")
        return {"error": "Stripe não configurado"}
    
    try:
        # Buscar a assinatura
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        # Extrair dados relevantes
        item = subscription.items.data[0] if subscription.items.data else None
        price = item.price if item else None
        
        return {
            "subscription_id": subscription.id,
            "customer_id": subscription.customer,
            "status": subscription.status,
            "current_period_end": subscription.current_period_end,
            "product_id": price.product if price else "",
            "price_id": price.id if price else "",
            "amount": price.unit_amount / 100 if price and price.unit_amount else 0,
            "currency": price.currency if price else "brl",
            "interval": price.recurring.interval if price and price.recurring else "",
            "metadata": subscription.metadata
        }
        
    except Exception as e:
        logger.error(f"Erro ao buscar assinatura: {str(e)}")
        return {"error": str(e)}