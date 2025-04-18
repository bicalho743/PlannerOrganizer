import os
import stripe
from fastapi import FastAPI, Request, Header
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sua chave secreta do Stripe do ambiente
api_key = os.environ.get("STRIPE_API_KEY")
stripe.api_key = api_key

if api_key:
    logger.info("Stripe API configurada com sucesso")
else:
    logger.warning("STRIPE_API_KEY não encontrada no ambiente")

app = FastAPI()

# Middleware CORS para permitir chamadas do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir arquivos HTML da pasta /static se existir
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    logger.info("Diretório de arquivos estáticos montado com sucesso")
except Exception as e:
    logger.warning(f"Não foi possível montar diretório de estáticos: {str(e)}")

@app.get("/")
def home():
    return {"message": "Stripe Direct API está funcionando"}

# Plano MENSAL
@app.post("/checkout/mensal")
def checkout_mensal():
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{
                "price": "price_1RFBNXLWUPER7pUXzmz8cdsL",  # R$ 9,70
                "quantity": 1,
            }],
            success_url="https://workspace.solanobicalho.repl.co/success",
            cancel_url="https://workspace.solanobicalho.repl.co/cancel",
        )
        return JSONResponse({"id": session.id, "url": session.url})
    except stripe.error.StripeError as e:
        logger.error(f"Erro ao criar sessão do Stripe: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={"error": f"Erro ao criar sessão: {str(e)}"}
        )

# Plano ANUAL - Com trial de 7 dias
@app.post("/checkout/anual")
def checkout_anual():
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{
                "price": "price_1RFBTtLWUPER7pUXPt2Ajhgz",  # R$ 97,00
                "quantity": 1,
            }],
            subscription_data={
                "trial_period_days": 7
            },
            success_url="https://workspace.solanobicalho.repl.co/success",
            cancel_url="https://workspace.solanobicalho.repl.co/cancel",
        )
        return JSONResponse({"id": session.id, "url": session.url})
    except stripe.error.StripeError as e:
        logger.error(f"Erro ao criar sessão do Stripe: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={"error": f"Erro ao criar sessão: {str(e)}"}
        )

# Plano VITALÍCIO - Pagamento único (não assinatura)
@app.post("/checkout/vitalicio")
def checkout_vitalicio():
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",  # pagamento único
            line_items=[{
                "price": "price_1RFBULLWUPER7pUXCiGZn3Jn",  # R$ 247,00
                "quantity": 1,
            }],
            success_url="https://workspace.solanobicalho.repl.co/success",
            cancel_url="https://workspace.solanobicalho.repl.co/cancel",
            metadata={
                "tipo_plano": "vitalicio"
            }
        )
        return JSONResponse({"id": session.id, "url": session.url})
    except stripe.error.StripeError as e:
        logger.error(f"Erro ao criar sessão do Stripe: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={"error": f"Erro ao criar sessão: {str(e)}"}
        )

# Webhook para processar eventos do Stripe
@app.post("/webhook")
async def stripe_webhook(request: Request):
    # Obtenha a chave de webhook do ambiente
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    if not webhook_secret:
        logger.warning("STRIPE_WEBHOOK_SECRET não configurada")
        return JSONResponse(status_code=200, content={"status": "webhook_not_configured"})
    
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    if not sig_header:
        return JSONResponse(status_code=400, content={"error": "Missing signature header"})

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        logger.error(f"Erro no webhook - payload inválido: {str(e)}")
        return JSONResponse(status_code=400, content={"error": "Invalid payload"})
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Erro no webhook - assinatura inválida: {str(e)}")
        return JSONResponse(status_code=400, content={"error": "Invalid signature"})

    # Processar eventos do Stripe
    event_type = event['type']
    logger.info(f"Evento Stripe recebido: {event_type}")
    
    # Quando o pagamento da primeira fatura for concluído
    if event_type == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        if 'subscription' in invoice:
            subscription_id = invoice['subscription']
            
            try:
                # Verificar se é do tipo 'vitalício' nos metadados
                subscription = stripe.Subscription.retrieve(subscription_id)
                if subscription.metadata.get("tipo_plano") == "vitalicio":
                    # Cancela a renovação, mantendo o acesso até o fim do ciclo
                    stripe.Subscription.modify(
                        subscription_id,
                        cancel_at_period_end=True
                    )
                    logger.info(f"Plano vitalício: assinatura {subscription_id} marcada para não renovar.")
            except Exception as e:
                logger.error(f"Erro ao processar assinatura: {str(e)}")
    
    # Outros eventos podem ser processados aqui
    elif event_type == 'checkout.session.completed':
        session = event['data']['object']
        logger.info(f"Checkout completo: {session.id}")
        # Processar checkout completo - poderia registrar no banco de dados
        
    elif event_type == 'customer.subscription.created':
        subscription = event['data']['object']
        logger.info(f"Assinatura criada: {subscription.id}")
        # Processar nova assinatura
        
    elif event_type == 'customer.subscription.updated':
        subscription = event['data']['object']
        logger.info(f"Assinatura atualizada: {subscription.id}")
        # Processar atualização de assinatura
        
    elif event_type == 'customer.subscription.deleted':
        subscription = event['data']['object']
        logger.info(f"Assinatura cancelada: {subscription.id}")
        # Processar cancelamento de assinatura

    return JSONResponse(status_code=200, content={"status": "ok"})

# Ponto de entrada para execução direta
if __name__ == "__main__":
    import uvicorn
    # Executar o servidor FastAPI
    uvicorn.run("stripe_direct:app", host="0.0.0.0", port=8002)