import os
import stripe
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# Configurar CORS para permitir requisições de qualquer origem
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar Stripe com a chave API
stripe.api_key = os.environ.get("STRIPE_API_KEY")

# Definir os IDs de preço para cada plano
PRICE_IDS = {
    "mensal": "price_1RFBNXLWUPER7pUXzmz8cdsL",
    "anual": "price_1RFBTtLWUPER7pUXPt2Ajhgz",
    "vitalicio": "price_1RFBULLWUPER7pUXCiGZn3Jn"
}

# Modelo de dados para a requisição de checkout
class CheckoutRequest(BaseModel):
    plan_id: str
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None

@app.get("/")
async def root():
    return {"message": "API de pagamento do Planner Organizer"}

@app.post("/create-checkout-session")
async def create_checkout_session(request: CheckoutRequest):
    """
    Cria uma sessão de checkout do Stripe para um plano específico.
    Planos disponíveis: mensal, anual, vitalicio
    """
    try:
        # Verificar se o plano existe
        if request.plan_id not in PRICE_IDS:
            return {"error": "Plano inválido. Escolha entre: mensal, anual, vitalicio"}
        
        # Obter o ID do preço
        price_id = PRICE_IDS[request.plan_id]
        
        # Determinar o modo de pagamento
        mode = "payment" if request.plan_id == "vitalicio" else "subscription"
        
        # URL base da aplicação
        domain_url = os.environ.get("REPLIT_DOMAIN", "http://localhost:5000")
        if not domain_url.startswith("http"):
            domain_url = f"https://{domain_url}"
        
        # URLs de sucesso e cancelamento
        success_url = request.success_url or f"{domain_url}/sucesso?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = request.cancel_url or f"{domain_url}/cancelado"
        
        # Criar a sessão de checkout
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1
                }
            ],
            mode=mode,
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=f"planner_{request.plan_id}_{os.urandom(4).hex()}"
        )
        
        return {"id": checkout_session.id, "url": checkout_session.url}
    except Exception as e:
        return {"error": str(e)}

@app.post("/webhook")
async def stripe_webhook(request: Request):
    """
    Webhook para receber eventos do Stripe.
    """
    # Obter o payload do webhook
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        # Verificar a assinatura do webhook
        webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
        if webhook_secret:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        else:
            # Sem verificação de assinatura para ambiente de desenvolvimento
            event = stripe.Event.construct_from(
                await request.json(), stripe.api_key
            )
        
        # Processar eventos
        if event.type == "checkout.session.completed":
            # Pagamento concluído
            session = event.data.object
            print(f"Checkout completado: {session.id}")
            
            # Aqui você pode adicionar lógica para registrar o pagamento no seu sistema
            
        return {"success": True}
        
    except Exception as e:
        return {"error": str(e)}

# Iniciar a aplicação FastAPI com uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)