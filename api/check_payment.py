"""
API para verificar o status de pagamento com o Stripe
"""
import os
import stripe
import json
import firebase_admin
from firebase_admin import credentials, auth, firestore
from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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

# Chave API do Stripe
stripe.api_key = os.environ.get("STRIPE_API_KEY")

# Inicializar Firebase Admin SDK
try:
    # Usar credenciais se disponíveis
    if os.environ.get("FIREBASE_SERVICE_ACCOUNT"):
        cred_dict = json.loads(os.environ.get("FIREBASE_SERVICE_ACCOUNT"))
        cred = credentials.Certificate(cred_dict)
        firebase_app = firebase_admin.initialize_app(cred)
    else:
        # Tentativa de inicializar sem credenciais (ambiente de desenvolvimento)
        firebase_app = firebase_admin.initialize_app()
    
    # Inicializar Firestore
    db = firestore.client()
    firebase_auth = auth
except Exception as e:
    print(f"Erro ao inicializar Firebase Admin SDK: {e}")
    db = None
    firebase_auth = None

# Mapear planos do Stripe para detalhes das assinaturas
PLANOS = {
    "price_1RFBNXLWUPER7pUXzmz8cdsL": {
        "nome": "Plano Mensal",
        "tipo": "subscription",
        "duracao": "monthly",
        "periodo_teste": 7,
        "valor": 9.70
    },
    "price_1RFBTtLWUPER7pUXPt2Ajhgz": {
        "nome": "Plano Anual",
        "tipo": "subscription",
        "duracao": "yearly",
        "periodo_teste": 7,
        "valor": 97.00
    },
    "price_1RFBULLWUPER7pUXCiGZn3Jn": {
        "nome": "Acesso Vitalício",
        "tipo": "lifetime",
        "duracao": "forever",
        "periodo_teste": 0,
        "valor": 247.00
    }
}

@app.get("/")
async def root():
    return {"message": "API de verificação de pagamento"}

@app.get("/api/check-payment-status")
async def check_payment_status(
    session_id: str = Query(..., description="ID da sessão de checkout do Stripe"),
    user_id: Optional[str] = Query(None, description="ID do usuário no Firebase")
):
    """
    Verifica o status de pagamento de uma sessão de checkout
    """
    try:
        # Recuperar sessão do Stripe
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        if not checkout_session:
            return {
                "status": "error",
                "message": "Sessão de checkout não encontrada"
            }
            
        # Verificar o status da sessão
        payment_status = checkout_session.get("payment_status")
        checkout_status = checkout_session.get("status")
        
        # Para pagamentos únicos
        if payment_status == "paid" and checkout_status == "complete":
            # Verificar se há um ID de cliente
            customer_id = checkout_session.get("customer")
            
            # Se tivermos um ID de usuário do Firebase, atualizar os dados de assinatura
            if user_id and db:
                # Recuperar line items para identificar o plano
                line_items = stripe.checkout.Session.list_line_items(session_id)
                
                if line_items and line_items.data:
                    # Identificar o produto/plano
                    price_id = line_items.data[0].price.id
                    plan_info = PLANOS.get(price_id, {
                        "nome": "Plano Desconhecido",
                        "tipo": "unknown"
                    })
                    
                    # Preparar dados de assinatura
                    subscription_data = {
                        "status": "active",
                        "plan": plan_info.get("nome"),
                        "tipo": plan_info.get("tipo"),
                        "checkout_session_id": session_id,
                        "stripe_customer_id": customer_id,
                        "updated_at": firestore.SERVER_TIMESTAMP
                    }
                    
                    # Se for um pagamento único (vitalício)
                    if plan_info.get("tipo") == "lifetime":
                        subscription_data["expires_at"] = None  # Nunca expira
                    
                    # Atualizar no Firestore
                    try:
                        user_ref = db.collection('users').document(user_id)
                        user_ref.set({
                            'subscription': subscription_data,
                            'updated_at': firestore.SERVER_TIMESTAMP
                        }, merge=True)
                    except Exception as db_error:
                        print(f"Erro ao atualizar Firestore: {db_error}")
                        # Continuar mesmo com erro no banco
            
            # Retornar status de sucesso
            return {
                "status": "success",
                "payment_status": payment_status,
                "checkout_status": checkout_status,
                "customer_id": customer_id,
                "plan_name": plan_info.get("nome") if 'plan_info' in locals() else "Plano"
            }
        
        # Para pagamentos pendentes
        elif payment_status == "unpaid" and checkout_status == "open":
            return {
                "status": "pending",
                "message": "Pagamento ainda não processado"
            }
        
        # Para outros estados
        else:
            return {
                "status": "other",
                "payment_status": payment_status,
                "checkout_status": checkout_status,
                "message": "Status não reconhecido"
            }
    
    except stripe.error.StripeError as e:
        return {
            "status": "error",
            "message": f"Erro do Stripe: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erro ao verificar pagamento: {str(e)}"
        }

@app.get("/api/check-subscription")
async def check_subscription(
    user_id: str = Query(..., description="ID do usuário no Firebase")
):
    """
    Verifica o status da assinatura de um usuário
    """
    if not db:
        return {
            "status": "error",
            "message": "Firestore não inicializado"
        }
    
    try:
        # Recuperar documento do usuário
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if user_doc.exists:
            user_data = user_doc.to_dict()
            subscription = user_data.get('subscription', {})
            
            # Verificar status
            status = subscription.get('status')
            if status == 'active':
                # Para assinaturas recorrentes, verificar validade
                if subscription.get('tipo') != 'lifetime':
                    # TODO: Implementar verificação de data de expiração
                    pass
                
                return {
                    "status": "active",
                    "plan": subscription.get('plan'),
                    "type": subscription.get('tipo'),
                    "details": subscription
                }
            else:
                return {
                    "status": "inactive",
                    "plan": subscription.get('plan'),
                    "message": f"Assinatura com status: {status}"
                }
        else:
            return {
                "status": "not_found",
                "message": "Nenhuma assinatura encontrada para este usuário"
            }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erro ao verificar assinatura: {str(e)}"
        }

# Para rodar a aplicação localmente 
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)