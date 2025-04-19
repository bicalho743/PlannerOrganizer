"""
Integração entre Firebase e Stripe para gerenciamento de usuários e assinaturas.
Este módulo processa webhooks do Stripe e atualiza os dados correspondentes no Firebase.
"""
import os
import json
import time
import stripe
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, auth, firestore
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

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

# Mapear planos do Stripe para detalhes das assinaturas
PLANOS = {
    "monthly": {
        "price_id": "price_1RFBNXLWUPER7pUXzmz8cdsL",
        "nome": "Plano Mensal",
        "tipo": "subscription",
        "duracao": "monthly",
        "periodo_teste": 7,
        "valor": 9.70,
        "descricao": "Assinatura mensal com 7 dias grátis"
    },
    "yearly": {
        "price_id": "price_1RFBTtLWUPER7pUXPt2Ajhgz",
        "nome": "Plano Anual",
        "tipo": "subscription",
        "duracao": "yearly",
        "periodo_teste": 7,
        "valor": 97.00,
        "descricao": "Assinatura anual com 7 dias grátis"
    },
    "lifetime": {
        "price_id": "price_1RFBULLWUPER7pUXCiGZn3Jn",
        "nome": "Acesso Vitalício",
        "tipo": "lifetime",
        "duracao": "forever",
        "periodo_teste": 0,
        "valor": 247.00,
        "descricao": "Acesso vitalício sem mensalidades"
    }
}

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
except Exception as e:
    print(f"Erro ao inicializar Firebase Admin SDK: {e}")
    db = None

class UserData(BaseModel):
    """
    Dados do usuário para criação da conta e checkout
    """
    email: str
    name: Optional[str] = None
    plan_id: str

class CheckoutRequest(BaseModel):
    """
    Dados para criar uma sessão de checkout
    """
    plan_id: str
    user_id: Optional[str] = None
    email: Optional[str] = None
    customer_data: Optional[Dict[str, Any]] = None

@app.get("/")
async def root():
    return {"message": "API de integração entre Firebase e Stripe"}

async def create_firebase_user(email: str, name: str = None) -> str:
    """
    Cria um usuário no Firebase Authentication e retorna o UID
    """
    try:
        # Gerar uma senha temporária - o usuário deverá redefini-la
        password = f"Temp{int(time.time())}"
        
        # Criar usuário no Firebase Authentication
        user = auth.create_user(
            email=email,
            password=password,
            display_name=name or email.split('@')[0],
            email_verified=False
        )
        
        # Enviar e-mail para redefinição de senha
        auth.generate_password_reset_link(email)
        
        # Criar documento do usuário no Firestore
        if db:
            user_ref = db.collection('users').document(user.uid)
            user_ref.set({
                'email': email,
                'name': name or email.split('@')[0],
                'created_at': firestore.SERVER_TIMESTAMP,
                'subscription': {
                    'status': 'pending',
                    'created_at': firestore.SERVER_TIMESTAMP
                }
            })
        
        return user.uid
    
    except Exception as e:
        print(f"Erro ao criar usuário: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao criar usuário: {str(e)}")

async def update_user_subscription(user_id: str, subscription_data: Dict[str, Any]):
    """
    Atualiza os dados de assinatura do usuário no Firestore
    """
    if not db:
        raise HTTPException(status_code=500, detail="Banco de dados não inicializado")
    
    try:
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail=f"Usuário não encontrado: {user_id}")
        
        # Adicionar timestamp da atualização
        subscription_data['updated_at'] = firestore.SERVER_TIMESTAMP
        
        # Atualizar dados de assinatura
        user_ref.update({
            'subscription': subscription_data
        })
        
        return {"status": "success", "message": "Assinatura atualizada com sucesso"}
    
    except Exception as e:
        print(f"Erro ao atualizar assinatura: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar assinatura: {str(e)}")

@app.post("/api/create-user-and-checkout")
async def create_user_and_checkout_session(user_data: UserData):
    """
    Cria um usuário no Firebase e uma sessão de checkout no Stripe
    """
    try:
        # Verificar se o plano existe
        if user_data.plan_id not in PLANOS:
            raise HTTPException(status_code=400, detail=f"Plano não encontrado: {user_data.plan_id}")
        
        # Criar usuário no Firebase
        user_id = await create_firebase_user(user_data.email, user_data.name)
        
        # Criar checkout com o usuário vinculado
        plano = PLANOS[user_data.plan_id]
        
        # Definir modo com base no tipo de produto
        mode = "subscription" if plano["tipo"] == "subscription" else "payment"
        
        # Configurar detalhes de pagamento
        checkout_session_params = {
            "line_items": [
                {
                    "price": plano["price_id"],
                    "quantity": 1,
                }
            ],
            "mode": mode,
            "success_url": "https://planner-organizer.replit.app/sucesso?session_id={CHECKOUT_SESSION_ID}",
            "cancel_url": "https://planner-organizer.replit.app/cancelado",
            "customer_email": user_data.email,
            "metadata": {
                "plan_id": user_data.plan_id,
                "plano_nome": plano["nome"],
                "user_id": user_id,
                "email": user_data.email
            }
        }
        
        # Para assinaturas com período de teste gratuito
        if mode == "subscription" and plano["periodo_teste"] > 0:
            checkout_session_params["subscription_data"] = {
                "trial_period_days": plano["periodo_teste"]
            }
        
        # Criar sessão de checkout
        checkout_session = stripe.checkout.Session.create(**checkout_session_params)
        
        # Atualizar status do usuário no Firestore
        if db:
            user_ref = db.collection('users').document(user_id)
            user_ref.update({
                'subscription.checkout_session_id': checkout_session.id,
                'subscription.plan_id': user_data.plan_id,
                'subscription.plan_name': plano["nome"],
                'subscription.checkout_created_at': firestore.SERVER_TIMESTAMP
            })
        
        # Retornar dados para o cliente
        return {
            "user_id": user_id,
            "checkout_session_id": checkout_session.id,
            "checkout_url": checkout_session.url
        }
    
    except HTTPException as he:
        # Repassar exceções HTTP
        raise he
    except Exception as e:
        print(f"Erro no processo de criação de usuário e checkout: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: Optional[str] = Header(None)):
    """
    Webhook para processar eventos do Stripe e atualizar o Firebase
    """
    # Verificar se o banco de dados está inicializado
    if not db:
        return {"error": "Firebase não inicializado"}, 500
    
    payload = await request.body()
    endpoint_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    
    try:
        # Verificar a assinatura para autenticar o webhook
        if endpoint_secret and stripe_signature:
            event = stripe.Webhook.construct_event(
                payload, stripe_signature, endpoint_secret
            )
        else:
            # Para desenvolvimento, apenas analisar JSON (não recomendado para produção)
            payload_json = json.loads(payload)
            event = payload_json
        
        # Extrair dados do evento
        event_type = event.get("type")
        event_data = event.get("data", {}).get("object", {})
        
        print(f"Webhook recebido: {event_type}")
        
        # Processar eventos de checkout
        if event_type == "checkout.session.completed":
            # Extrair informações da sessão
            session_id = event_data.get("id")
            metadata = event_data.get("metadata", {})
            user_id = metadata.get("user_id")
            plan_id = metadata.get("plan_id")
            
            if not user_id:
                print(f"Sessão {session_id} não tem user_id nos metadados")
                return {"status": "warning", "message": "user_id não encontrado"}
            
            # Recuperar informações completas da sessão
            session = stripe.checkout.Session.retrieve(
                session_id,
                expand=["line_items", "customer", "subscription"]
            )
            
            # Extrair dados relevantes
            customer_id = session.get("customer")
            subscription_id = session.get("subscription")
            
            # Recuperar plano a partir dos line items
            line_items = stripe.checkout.Session.list_line_items(session_id)
            price_id = None
            if line_items and line_items.data:
                price_id = line_items.data[0].price.id
            
            # Encontrar o tipo de plano com base no price_id
            plan_info = None
            for plan_key, plan_data in PLANOS.items():
                if plan_data["price_id"] == price_id:
                    plan_info = plan_data
                    break
            
            # Determinar plano e tipo
            plan_type = plan_info.get("tipo") if plan_info else "unknown"
            plan_name = plan_info.get("nome") if plan_info else "Plano"
            
            # Preparar dados de assinatura
            subscription_data = {
                "status": "active",
                "plan_id": plan_id,
                "plan_name": plan_name,
                "plan_type": plan_type,
                "stripe_customer_id": customer_id,
                "checkout_session_id": session_id,
                "activation_date": firestore.SERVER_TIMESTAMP
            }
            
            # Para assinaturas recorrentes, adicionar ID da assinatura
            if subscription_id and plan_type == "subscription":
                subscription = stripe.Subscription.retrieve(subscription_id)
                current_period_end = subscription.get("current_period_end")
                
                subscription_data.update({
                    "stripe_subscription_id": subscription_id,
                    "current_period_end": datetime.fromtimestamp(current_period_end) if current_period_end else None,
                    "cancel_at_period_end": subscription.get("cancel_at_period_end", False)
                })
            
            # Para planos vitalícios, não há data de expiração
            if plan_type == "lifetime":
                subscription_data["expires_at"] = None  # Nunca expira
            
            # Atualizar dados do usuário no Firestore
            user_ref = db.collection('users').document(user_id)
            user_ref.update({
                "subscription": subscription_data,
                "updated_at": firestore.SERVER_TIMESTAMP
            })
            
            print(f"Dados de assinatura atualizados para o usuário {user_id}")
            return {"status": "success", "user_id": user_id}
        
        # Processar eventos de assinatura
        elif event_type in ["customer.subscription.created", "customer.subscription.updated"]:
            subscription = event_data
            subscription_id = subscription.get("id")
            customer_id = subscription.get("customer")
            
            # Buscar usuário pelo customer_id
            users_ref = db.collection('users').where("subscription.stripe_customer_id", "==", customer_id).limit(1)
            users = users_ref.get()
            
            if not users or len(users) == 0:
                print(f"Nenhum usuário encontrado com customer_id: {customer_id}")
                return {"status": "warning", "message": "Usuário não encontrado"}
            
            user_doc = users[0]
            user_id = user_doc.id
            
            # Extrair dados da assinatura
            current_period_end = subscription.get("current_period_end")
            cancel_at_period_end = subscription.get("cancel_at_period_end", False)
            status = subscription.get("status")
            
            # Atualizar dados de assinatura
            user_ref = db.collection('users').document(user_id)
            user_ref.update({
                "subscription.status": status,
                "subscription.stripe_subscription_id": subscription_id,
                "subscription.current_period_end": datetime.fromtimestamp(current_period_end) if current_period_end else None,
                "subscription.cancel_at_period_end": cancel_at_period_end,
                "subscription.updated_at": firestore.SERVER_TIMESTAMP
            })
            
            print(f"Assinatura {subscription_id} atualizada para o usuário {user_id}")
            return {"status": "success", "user_id": user_id}
        
        # Processar cancelamento de assinatura
        elif event_type == "customer.subscription.deleted":
            subscription = event_data
            subscription_id = subscription.get("id")
            customer_id = subscription.get("customer")
            
            # Buscar usuário pelo customer_id
            users_ref = db.collection('users').where("subscription.stripe_customer_id", "==", customer_id).limit(1)
            users = users_ref.get()
            
            if not users or len(users) == 0:
                print(f"Nenhum usuário encontrado com customer_id: {customer_id}")
                return {"status": "warning", "message": "Usuário não encontrado"}
            
            user_doc = users[0]
            user_id = user_doc.id
            
            # Atualizar status da assinatura
            user_ref = db.collection('users').document(user_id)
            user_ref.update({
                "subscription.status": "canceled",
                "subscription.canceled_at": firestore.SERVER_TIMESTAMP,
                "subscription.updated_at": firestore.SERVER_TIMESTAMP
            })
            
            print(f"Assinatura {subscription_id} cancelada para o usuário {user_id}")
            return {"status": "success", "user_id": user_id}
        
        # Para outros tipos de eventos
        return {"status": "received", "type": event_type}
    
    except Exception as e:
        print(f"Erro ao processar webhook: {e}")
        return {"error": str(e)}, 400

# Para rodar a aplicação localmente para teste
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)