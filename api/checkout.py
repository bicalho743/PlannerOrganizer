"""
API para processamento de checkout do Stripe
"""
import os
import stripe
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

# Configurações do Stripe
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY")
STRIPE_PRICE_ID_MENSAL = os.environ.get("STRIPE_PRICE_ID_MENSAL")
STRIPE_PRICE_ID_ANUAL = os.environ.get("STRIPE_PRICE_ID_ANUAL")
STRIPE_PRICE_ID_VITALICIO = os.environ.get("STRIPE_PRICE_ID_VITALICIO")

# Configurar o cliente Stripe com a chave API
if STRIPE_API_KEY:
    stripe.api_key = STRIPE_API_KEY

# Mapeamento de planos para IDs de preço do Stripe
PRICE_MAPPING = {
    "mensal": STRIPE_PRICE_ID_MENSAL,
    "anual": STRIPE_PRICE_ID_ANUAL,
    "vitalicio": STRIPE_PRICE_ID_VITALICIO
}

# Modelo para solicitação de checkout
class CheckoutRequest(BaseModel):
    plan_type: str

# Criar router para os endpoints de checkout
router = APIRouter(prefix="/api/checkout", tags=["checkout"])

@router.post("/")
async def criar_checkout(request: CheckoutRequest):
    """
    Endpoint para criar uma sessão de checkout do Stripe
    """
    if not STRIPE_API_KEY:
        raise HTTPException(status_code=500, detail="Stripe API Key não configurada")
    
    # Obter o ID do preço com base no tipo de plano
    price_id = PRICE_MAPPING.get(request.plan_type)
    if not price_id:
        raise HTTPException(status_code=400, detail=f"Tipo de plano inválido: {request.plan_type}")
    
    try:
        # Criar uma sessão de checkout do Stripe
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1
            }],
            mode="subscription" if request.plan_type != "vitalicio" else "payment",
            success_url="https://plannerorganiza.com.br/sucesso",
            cancel_url="https://plannerorganiza.com.br/planos"
        )
        
        # Retornar a URL de checkout
        return {"url": checkout_session.url}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar sessão de checkout: {str(e)}")

@router.post("/mensal")
async def checkout_mensal():
    """
    Endpoint para criar uma sessão de checkout para o plano mensal
    """
    if not STRIPE_API_KEY or not STRIPE_PRICE_ID_MENSAL:
        raise HTTPException(status_code=500, detail="Configuração do Stripe incompleta para plano mensal")
    
    try:
        # Criar uma sessão de checkout do Stripe
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": STRIPE_PRICE_ID_MENSAL,
                "quantity": 1
            }],
            mode="subscription",
            success_url="https://plannerorganiza.com.br/sucesso",
            cancel_url="https://plannerorganiza.com.br/planos"
        )
        
        # Retornar a URL de checkout
        return {"url": checkout_session.url}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar sessão de checkout: {str(e)}")

@router.post("/anual")
async def checkout_anual():
    """
    Endpoint para criar uma sessão de checkout para o plano anual
    """
    if not STRIPE_API_KEY or not STRIPE_PRICE_ID_ANUAL:
        raise HTTPException(status_code=500, detail="Configuração do Stripe incompleta para plano anual")
    
    try:
        # Criar uma sessão de checkout do Stripe
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": STRIPE_PRICE_ID_ANUAL,
                "quantity": 1
            }],
            mode="subscription",
            success_url="https://plannerorganiza.com.br/sucesso",
            cancel_url="https://plannerorganiza.com.br/planos"
        )
        
        # Retornar a URL de checkout
        return {"url": checkout_session.url}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar sessão de checkout: {str(e)}")

@router.post("/vitalicio")
async def checkout_vitalicio():
    """
    Endpoint para criar uma sessão de checkout para o plano vitalício
    """
    if not STRIPE_API_KEY or not STRIPE_PRICE_ID_VITALICIO:
        raise HTTPException(status_code=500, detail="Configuração do Stripe incompleta para plano vitalício")
    
    try:
        # Criar uma sessão de checkout do Stripe
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": STRIPE_PRICE_ID_VITALICIO,
                "quantity": 1
            }],
            mode="payment",
            success_url="https://plannerorganiza.com.br/sucesso",
            cancel_url="https://plannerorganiza.com.br/planos"
        )
        
        # Retornar a URL de checkout
        return {"url": checkout_session.url}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar sessão de checkout: {str(e)}")