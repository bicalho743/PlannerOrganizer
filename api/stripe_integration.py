"""
Módulo para integração com o Stripe para pagamentos e assinaturas.
Este é um módulo de exemplo para demonstrar como integrar com a API do Stripe.
"""

import os
import json
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, Request, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
import stripe
from pydantic import BaseModel
import secrets
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurar Stripe - usamos a versão instalada no ambiente
# Para demonstração, estamos usando valores hardcoded
api_key = os.environ.get("STRIPE_API_KEY", "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")
webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
publishable_key = os.environ.get("STRIPE_PUBLISHABLE_KEY", "pk_live_51RFB2dLWUPER7pUXim2VuVkCESsrjNcHkDQuMJeDCvvW0ZsyFfqM2exfCTwSSe5O4R2TXBxHJtIpYSGBTAx2gBXT00gpAVYK1f")

# Inicializar FastAPI app
app = FastAPI(title="Stripe Integration API", description="API para integração com o Stripe")

# Adicionar middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ajustar para domínios específicos em produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar Stripe com a chave API
stripe.api_key = api_key
logger.info("Stripe API configurada com sucesso")

# Modelos para a API
class CheckoutSessionCreate(BaseModel):
    price_id: str
    success_url: str
    cancel_url: str
    mode: Optional[str] = "subscription"  # "subscription" ou "payment"
    customer_email: Optional[str] = None
    customer_name: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None

class SubscriptionInfo(BaseModel):
    subscription_id: str
    customer_id: str
    status: str
    current_period_end: int
    product_id: str
    price_id: str
    amount: float
    currency: str
    interval: str
    metadata: Optional[Dict[str, Any]] = None

class ProductInfo(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    images: List[str] = []
    metadata: Optional[Dict[str, Any]] = None
    prices: List[Dict[str, Any]] = []

# Endpoints da API
@app.get("/")
async def read_root():
    return {"message": "Stripe Integration API is running"}

@app.get("/api/health")
async def health_check():
    """Endpoint para verificar o status da API"""
    # Verificar se conseguimos conectar com o Stripe
    stripe_status = "ok" if api_key else "not_configured"
    return {
        "status": "ok",
        "version": "1.0.0",
        "stripe": stripe_status
    }

@app.post("/api/checkout/session", response_model=Dict[str, str])
async def create_checkout_session(session_data: CheckoutSessionCreate):
    """
    Cria uma sessão de checkout do Stripe para um pagamento único ou assinatura.
    
    Este endpoint recebe:
    - ID do preço do Stripe
    - URLs de sucesso e cancelamento
    - Informações opcionais do cliente
    
    Retorna:
    - ID da sessão de checkout
    - URL para redirecionamento
    """
    if not api_key:
        raise HTTPException(status_code=503, detail="Stripe API não configurada")
    
    try:
        # Verificar versão do Stripe para ajustar a API adequadamente
        stripe_version = getattr(stripe, "__version__", "unknown")
        logger.info(f"Usando Stripe versão: {stripe_version}")
        
        # Configurar os dados da sessão - compatível com Stripe 8.x até 12.x
        checkout_data = {
            "success_url": session_data.success_url,
            "cancel_url": session_data.cancel_url,
            "payment_method_types": ["card"],
        }
        
        # Configuração específica baseada no modo (assinatura ou pagamento único)
        # O erro "You must provide at least one recurring price in subscription mode when using prices"
        # ocorre porque o plano lifetime não é uma assinatura recorrente
        if session_data.mode == "payment":
            checkout_data["mode"] = "payment"
            checkout_data["line_items"] = [
                {
                    "price": session_data.price_id,
                    "quantity": 1,
                }
            ]
        else:
            checkout_data["mode"] = "subscription"
            checkout_data["line_items"] = [
                {
                    "price": session_data.price_id,
                    "quantity": 1,
                }
            ]
        
        # Adicionar email do cliente se fornecido
        if session_data.customer_email:
            checkout_data["customer_email"] = session_data.customer_email
            
        # Adicionar metadados se fornecidos
        if session_data.metadata:
            checkout_data["metadata"] = session_data.metadata
        
        # Criar a sessão no Stripe
        session = stripe.checkout.Session.create(**checkout_data)
        
        return {"id": session.id, "url": session.url}
        
    except stripe.error.StripeError as e:
        logger.error(f"Erro ao criar sessão do Stripe: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Erro ao criar sessão: {str(e)}")

@app.get("/api/products", response_model=List[ProductInfo])
async def list_products():
    """
    Lista todos os produtos e preços ativos no Stripe.
    
    Retorna:
    - Lista de produtos com suas informações e preços
    """
    if not api_key:
        raise HTTPException(status_code=503, detail="Stripe API não configurada")
    
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
            
            price_map[price.product].append({
                "id": price.id,
                "currency": price.currency,
                "unit_amount": price.unit_amount / 100 if price.unit_amount else 0,
                "type": price.type,
                "recurring": price.recurring if hasattr(price, 'recurring') else None,
                "metadata": price.metadata
            })
        
        # Construir a resposta
        result = []
        for product in products.auto_paging_iter():
            product_info = {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "images": product.images,
                "metadata": product.metadata,
                "prices": price_map.get(product.id, [])
            }
            result.append(product_info)
        
        return result
        
    except stripe.error.StripeError as e:
        logger.error(f"Erro ao listar produtos do Stripe: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Erro ao listar produtos: {str(e)}")

@app.get("/api/subscription/{subscription_id}", response_model=SubscriptionInfo)
async def get_subscription(subscription_id: str):
    """
    Obtém detalhes de uma assinatura específica do Stripe.
    
    Retorna:
    - Informações detalhadas da assinatura
    """
    if not api_key:
        raise HTTPException(status_code=503, detail="Stripe API não configurada")
    
    try:
        # Buscar a assinatura
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        # Extrair dados relevantes
        item = subscription.items.data[0] if subscription.items.data else None
        price = item.price if item else None
        
        subscription_info = {
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
        
        return subscription_info
        
    except stripe.error.StripeError as e:
        logger.error(f"Erro ao buscar assinatura: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Erro ao buscar assinatura: {str(e)}")

@app.post("/api/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    """
    Webhook para receber eventos do Stripe.
    
    Este endpoint processa eventos como:
    - Pagamentos bem-sucedidos
    - Assinaturas criadas/atualizadas/canceladas
    - Falhas de pagamento
    """
    if not webhook_secret:
        logger.warning("STRIPE_WEBHOOK_SECRET não configurado!")
        return JSONResponse(status_code=200, content={"status": "webhook_not_configured"})
    
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Stripe-Signature header is missing")

    try:
        # Ler o corpo da requisição
        payload = await request.body()
        
        # Verificar assinatura do evento
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature,
            secret=webhook_secret
        )
        
        # Processar o evento
        event_type = event['type']
        logger.info(f"Evento Stripe recebido: {event_type}")
        
        if event_type == 'checkout.session.completed':
            session = event['data']['object']
            logger.info(f"Checkout completo: {session.id}")
            # Processar checkout completo
            # TODO: Atualizar banco de dados
            
        elif event_type == 'invoice.paid':
            invoice = event['data']['object']
            logger.info(f"Fatura paga: {invoice.id}")
            # Processar fatura paga
            # TODO: Atualizar status de assinatura no banco
            
        elif event_type == 'invoice.payment_failed':
            invoice = event['data']['object']
            logger.info(f"Falha no pagamento de fatura: {invoice.id}")
            # Processar falha no pagamento
            # TODO: Notificar usuário
            
        elif event_type == 'customer.subscription.created':
            subscription = event['data']['object']
            logger.info(f"Assinatura criada: {subscription.id}")
            # Processar nova assinatura
            # TODO: Registrar assinatura no banco
            
        elif event_type == 'customer.subscription.updated':
            subscription = event['data']['object']
            logger.info(f"Assinatura atualizada: {subscription.id}")
            # Processar atualização de assinatura
            # TODO: Atualizar assinatura no banco
            
        elif event_type == 'customer.subscription.deleted':
            subscription = event['data']['object']
            logger.info(f"Assinatura cancelada: {subscription.id}")
            # Processar cancelamento de assinatura
            # TODO: Marcar assinatura como cancelada no banco
            
        return JSONResponse(status_code=200, content={"status": "success"})
        
    except stripe.error.SignatureVerificationError:
        logger.error("Assinatura do webhook inválida!")
        raise HTTPException(status_code=400, detail="Invalid signature")
        
    except Exception as e:
        logger.error(f"Erro no webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")

# Ponto de entrada para execução direta
if __name__ == "__main__":
    import uvicorn
    # Executar o servidor FastAPI
    uvicorn.run("stripe_integration:app", host="0.0.0.0", port=8000)