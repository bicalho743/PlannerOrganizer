"""
Módulo para gerenciamento de integrações com o Stripe
Este módulo fornece funções para interagir diretamente com a API do Stripe
sem depender do backend FastAPI, evitando problemas de middleware de sessão.
"""

import os
import logging
from typing import Optional, Dict, Any, Union

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Recuperar chaves do ambiente
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY")
STRIPE_PRICE_ID_MENSAL = os.environ.get('STRIPE_PRICE_ID_MENSAL')
STRIPE_PRICE_ID_ANUAL = os.environ.get('STRIPE_PRICE_ID_ANUAL')
STRIPE_PRICE_ID_VITALICIO = os.environ.get('STRIPE_PRICE_ID_VITALICIO')

# Registrar informações de configuração no log
logger.info(f"STRIPE_API_KEY presente: {'Sim' if STRIPE_API_KEY else 'Não'}")
logger.info(f"STRIPE_PRICE_ID_MENSAL: {STRIPE_PRICE_ID_MENSAL}")
logger.info(f"STRIPE_PRICE_ID_ANUAL: {STRIPE_PRICE_ID_ANUAL}")
logger.info(f"STRIPE_PRICE_ID_VITALICIO: {STRIPE_PRICE_ID_VITALICIO}")

def criar_url_checkout_stripe(price_id: str, 
                             success_url: Optional[str] = None, 
                             cancel_url: Optional[str] = None,
                             customer_email: Optional[str] = None) -> Optional[str]:
    """
    Cria uma URL direta de checkout do Stripe sem passar pelo nosso backend
    
    Args:
        price_id: ID do preço no Stripe
        success_url: URL para redirecionar após sucesso
        cancel_url: URL para redirecionar após cancelamento
        customer_email: Email do cliente para pré-preencher
        
    Returns:
        str: URL de checkout ou None se houver erro
    """
    try:
        import stripe
        
        if not STRIPE_API_KEY:
            logger.error("STRIPE_API_KEY não configurada!")
            return None
        
        if not price_id:
            logger.error("price_id não fornecido!")
            return None
        
        # Valores padrão para URLs de redirecionamento
        if not success_url:
            success_url = "http://localhost:5000/minha_assinatura?status=success"
        if not cancel_url:
            cancel_url = "http://localhost:5000/planos?status=cancel"
        
        # Configurar a API do Stripe com a chave
        stripe.api_key = STRIPE_API_KEY
        
        logger.info(f"Tentando criar sessão Stripe para price_id: {price_id}")
        
        # Parâmetros da sessão de checkout
        checkout_params = {
            "payment_method_types": ["card"],
            "line_items": [{
                "price": price_id,
                "quantity": 1
            }],
            "mode": "subscription",
            "success_url": success_url,
            "cancel_url": cancel_url,
        }
        
        # Adicionar email do cliente se fornecido
        if customer_email:
            checkout_params["customer_email"] = customer_email
        
        # Criando a sessão diretamente com o Stripe
        checkout_session = stripe.checkout.Session.create(**checkout_params)
        
        # Retornar a URL da sessão de checkout
        logger.info(f"Sessão Stripe criada com sucesso: {checkout_session.url[:30]}...")
        return checkout_session.url
        
    except Exception as e:
        logger.error(f"Erro ao criar sessão de checkout Stripe: {str(e)}")
        return None

def obter_price_id_por_plano(plano: str) -> Optional[str]:
    """
    Retorna o ID do preço com base no nome do plano
    
    Args:
        plano: Nome do plano (Mensal, Anual, Vitalício)
        
    Returns:
        str: ID do preço ou None se não encontrado
    """
    if plano.lower() == "mensal":
        return STRIPE_PRICE_ID_MENSAL
    elif plano.lower() == "anual":
        return STRIPE_PRICE_ID_ANUAL
    elif plano.lower() in ["vitalicio", "vitalício"]:
        return STRIPE_PRICE_ID_VITALICIO
    else:
        logger.error(f"Plano desconhecido: {plano}")
        return None

def verificar_configuracao_stripe() -> Dict[str, bool]:
    """
    Verifica se todas as chaves necessárias do Stripe estão configuradas
    
    Returns:
        Dict[str, bool]: Dicionário com status de cada chave
    """
    return {
        "api_key": bool(STRIPE_API_KEY),
        "price_mensal": bool(STRIPE_PRICE_ID_MENSAL),
        "price_anual": bool(STRIPE_PRICE_ID_ANUAL),
        "price_vitalicio": bool(STRIPE_PRICE_ID_VITALICIO)
    }