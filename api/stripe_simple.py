"""
Módulo simplificado para integração com o Stripe para pagamentos e assinaturas.
"""

import os
import stripe
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from starlette.responses import JSONResponse
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração do Stripe - Usando chaves fornecidas diretamente para demo
stripe_api_key = os.environ.get("STRIPE_API_KEY", "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")
stripe_publishable_key = os.environ.get("STRIPE_PUBLISHABLE_KEY", "pk_live_51RFB2dLWUPER7pUXim2VuVkCESsrjNcHkDQuMJeDCvvW0ZsyFfqM2exfCTwSSe5O4R2TXBxHJtIpYSGBTAx2gBXT00gpAVYK1f")

# Configurar o Stripe com a chave API
stripe.api_key = stripe_api_key
logger.info("Stripe API configurada com sucesso")

app = FastAPI(title="Stripe Simple API", description="API simplificada para integração com o Stripe")

# Adicionar middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ajustar para domínios específicos em produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar diretório para arquivos estáticos (se existir)
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    logger.info("Diretório de arquivos estáticos montado com sucesso")
except Exception as e:
    logger.warning(f"Não foi possível montar o diretório de arquivos estáticos: {str(e)}")

@app.get("/")
def home():
    """Redireciona para a página inicial estática ou retorna informações da API"""
    try:
        # Tentar redirecionar para o HTML estático
        return RedirectResponse(url="/static/index.html")
    except:
        # Se não existir, retorna informações da API
        return {
            "app": "Stripe Simple API",
            "version": "1.0.0",
            "status": "online",
            "stripe_configured": bool(stripe_api_key)
        }

@app.post("/create-checkout-session")
async def create_checkout_session():
    """
    Cria uma sessão de checkout do Stripe para pagamento único.
    Exemplo de uso para o frontend:
    
    fetch('/create-checkout-session', {method: 'POST'})
    .then(res => res.json())
    .then(data => {
        stripe.redirectToCheckout({sessionId: data.id});
    });
    """
    if not stripe_api_key:
        return JSONResponse({"error": "Stripe API não configurada"}, status_code=503)
    
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "brl",
                    "product_data": {
                        "name": "Plano Anual PlannerOrganizer",
                    },
                    "unit_amount": 9700,  # em centavos => R$ 97,00
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=os.environ.get("STRIPE_SUCCESS_URL", "https://plannerorganiza.com.br/sucesso"),
            cancel_url=os.environ.get("STRIPE_CANCEL_URL", "https://plannerorganiza.com.br/erro"),
        )
        return JSONResponse({"id": session.id})
    except Exception as e:
        logger.error(f"Erro ao criar sessão do Stripe: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=400)

@app.post("/create-subscription")
async def create_subscription():
    """
    Cria uma sessão de checkout do Stripe para assinatura.
    Similar ao endpoint de pagamento único, mas configura uma assinatura recorrente.
    """
    if not stripe_api_key:
        return JSONResponse({"error": "Stripe API não configurada"}, status_code=503)
    
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "brl",
                    "product_data": {
                        "name": "Plano Anual PlannerOrganizer",
                    },
                    "unit_amount": 9700,  # em centavos => R$ 97,00
                    "recurring": {"interval": "year"}
                },
                "quantity": 1,
            }],
            mode="subscription",
            success_url=os.environ.get("STRIPE_SUCCESS_URL", "https://plannerorganiza.com.br/sucesso"),
            cancel_url=os.environ.get("STRIPE_CANCEL_URL", "https://plannerorganiza.com.br/erro"),
        )
        return JSONResponse({"id": session.id})
    except Exception as e:
        logger.error(f"Erro ao criar assinatura do Stripe: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=400)

@app.get("/plans")
async def get_plans():
    """Retorna os planos disponíveis para o frontend"""
    return JSONResponse({
        "plans": [
            {
                "id": "monthly",
                "name": "Plano Mensal",
                "description": "Acesso a todos os recursos com pagamento mensal",
                "price": 9.70,
                "price_cents": 970,
                "currency": "brl",
                "interval": "month",
                "featured": False
            },
            {
                "id": "yearly",
                "name": "Plano Anual",
                "description": "Acesso a todos os recursos com pagamento anual. Economize 17%!",
                "price": 97.00,
                "price_cents": 9700,
                "currency": "brl",
                "interval": "year",
                "featured": True
            },
            {
                "id": "lifetime",
                "name": "Acesso Vitalício",
                "description": "Acesso permanente a todos os recursos com pagamento único",
                "price": 247.00,
                "price_cents": 24700,
                "currency": "brl",
                "interval": "once",
                "featured": False
            }
        ]
    })

@app.post("/create-checkout-session/{plan_id}")
async def create_checkout_session_for_plan(plan_id: str):
    """
    Cria uma sessão de checkout do Stripe para um plano específico.
    Planos disponíveis: monthly, yearly, lifetime
    """
    if not stripe_api_key:
        return JSONResponse({"error": "Stripe API não configurada"}, status_code=503)
    
    plans = {
        "monthly": {
            "name": "Plano Mensal PlannerOrganizer",
            "price": 970,  # 9,70 em centavos
            "interval": "month",
            "mode": "subscription"
        },
        "yearly": {
            "name": "Plano Anual PlannerOrganizer",
            "price": 9700,  # 97,00 em centavos
            "interval": "year",
            "mode": "subscription"
        },
        "lifetime": {
            "name": "Acesso Vitalício PlannerOrganizer",
            "price": 24700,  # 247,00 em centavos
            "interval": None,
            "mode": "payment"
        }
    }
    
    if plan_id not in plans:
        return JSONResponse({"error": "Plano não encontrado"}, status_code=404)
    
    plan = plans[plan_id]
    
    try:
        line_item = {
            "price_data": {
                "currency": "brl",
                "product_data": {
                    "name": plan["name"],
                },
                "unit_amount": plan["price"],
            },
            "quantity": 1,
        }
        
        # Adicionar recurring apenas para assinaturas
        if plan["interval"]:
            line_item["price_data"]["recurring"] = {"interval": plan["interval"]}
        
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[line_item],
            mode=plan["mode"],
            success_url=os.environ.get("STRIPE_SUCCESS_URL", "https://plannerorganiza.com.br/sucesso"),
            cancel_url=os.environ.get("STRIPE_CANCEL_URL", "https://plannerorganiza.com.br/erro"),
        )
        return JSONResponse({"id": session.id})
    except Exception as e:
        logger.error(f"Erro ao criar sessão do Stripe: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=400)

# Ponto de entrada para execução direta
if __name__ == "__main__":
    import uvicorn
    # Executar o servidor FastAPI
    uvicorn.run("stripe_simple:app", host="0.0.0.0", port=8001, reload=True)