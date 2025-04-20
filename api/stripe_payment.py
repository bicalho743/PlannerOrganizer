"""
API para integração com o Stripe para pagamentos
"""
import os
import stripe
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

app = FastAPI()

# Configurar CORS para permitir requisições de qualquer origem
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Obter a chave secreta do Stripe a partir da variável de ambiente
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

class CheckoutRequest(BaseModel):
    plan_id: str
    user_id: Optional[str] = None
    email: Optional[str] = None
    customer_data: Optional[Dict[str, Any]] = None

@app.get("/")
async def root():
    return {"message": "API de integração com o Stripe"}

@app.post("/api/create-checkout-session")
async def create_checkout_session(request: CheckoutRequest):
    """
    Cria uma sessão de checkout do Stripe para um plano específico
    """
    # Inicializar variáveis para evitar erros de escopo
    mode = None
    
    try:
        # Verificar se o plano existe
        plano = PLANOS.get(request.plan_id)
        if not plano:
            return {"error": f"Plano não encontrado: {request.plan_id}"}
        
        # Definir modo com base no tipo de produto
        mode = "subscription" if plano["tipo"] == "subscription" else "payment"
        
        # Se o plano for de assinatura, garantimos que o preço associado seja recorrente
        if mode == "subscription":
            precos_recorrentes = {}  # Cache para preços recorrentes já criados
            
            try:
                # Recuperar o preço e verificar se é recorrente
                try:
                    price = stripe.Price.retrieve(plano["price_id"])
                    print(f"Preço existente encontrado: {price.id}")
                    
                    # Verificar se o preço é recorrente
                    if price.type != "recurring":
                        print(f"O preço {plano['price_id']} não é recorrente (tipo: {price.type}). Criando versão recorrente...")
                        
                        # Obter produto associado e garantir que esteja ativo
                        produto_id = price.product
                        try:
                            # Verificar e ativar o produto se necessário
                            produto = stripe.Product.retrieve(produto_id)
                            if not produto.active:
                                print(f"Produto {produto_id} não está ativo. Ativando...")
                                stripe.Product.modify(
                                    produto_id,
                                    active=True
                                )
                                print(f"Produto {produto_id} ativado com sucesso.")
                        except Exception as e:
                            print(f"Erro ao verificar/ativar produto: {str(e)}")
                        
                        # Verificar se já criamos um preço recorrente para este produto e plano
                        cache_key = f"{produto_id}_{plano['duracao']}"
                        if cache_key in precos_recorrentes:
                            price_id = precos_recorrentes[cache_key]
                            print(f"Usando preço recorrente do cache: {price_id}")
                            plano["price_id"] = price_id
                        else:
                            # Criar um novo preço recorrente
                            intervalos = {"monthly": "month", "yearly": "year"}
                            intervalo = intervalos.get(plano["duracao"], "month")
                            
                            novo_preco = stripe.Price.create(
                                unit_amount=int(plano["valor"] * 100),  # Converter para centavos
                                currency="brl",
                                recurring={"interval": intervalo},
                                product=produto_id,
                                metadata={
                                    "plan_id": request.plan_id, 
                                    "original_price_id": plano["price_id"],
                                    "auto_created": "true"
                                }
                            )
                            print(f"Novo preço recorrente criado: {novo_preco.id}")
                            
                            # Armazenar no cache e atualizar o plano
                            precos_recorrentes[cache_key] = novo_preco.id
                            plano["price_id"] = novo_preco.id
                    else:
                        print(f"Preço já é recorrente: {price.id}, tipo: {price.type}")
                        
                except stripe.error.InvalidRequestError as e:
                    print(f"Erro ao buscar preço: {str(e)}")
                    
                    # Se o preço não existe, criamos um novo produto e preço
                    print(f"Criando novo produto e preço recorrente para {plano['nome']}")
                    
                    # Criar um produto primeiro
                    produto_nome = f"Planner Organizer - {plano['nome']}"
                    try:
                        # Tentar encontrar um produto existente com esse nome
                        produtos = stripe.Product.list(limit=100)
                        produto_existente = None
                        for p in produtos.data:
                            if p.name == produto_nome:
                                produto_existente = p
                                break
                        
                        if produto_existente:
                            produto = produto_existente
                            print(f"Produto existente encontrado: {produto.id}")
                            # Garantir que o produto esteja ativo
                            if not produto.active:
                                print(f"Produto {produto.id} não está ativo. Ativando...")
                                stripe.Product.modify(
                                    produto.id,
                                    active=True
                                )
                                print(f"Produto {produto.id} ativado com sucesso.")
                        else:
                            # Criar novo produto (garantindo que esteja ativo)
                            produto = stripe.Product.create(
                                name=produto_nome,
                                description=plano["descricao"],
                                active=True
                            )
                            print(f"Novo produto criado: {produto.id}")
                        
                        # Criar o preço recorrente
                        intervalos = {"monthly": "month", "yearly": "year"}
                        intervalo = intervalos.get(plano["duracao"], "month")
                        
                        novo_preco = stripe.Price.create(
                            unit_amount=int(plano["valor"] * 100),  # Converter para centavos
                            currency="brl",
                            recurring={"interval": intervalo},
                            product=produto.id,
                            metadata={"plan_id": request.plan_id, "auto_created": "true"}
                        )
                        print(f"Novo preço recorrente criado: {novo_preco.id}")
                        
                        # Atualizar o price_id no objeto plano
                        plano["price_id"] = novo_preco.id
                    except Exception as e:
                        print(f"Erro ao lidar com produto: {str(e)}")
                        raise
            except Exception as e:
                print(f"Erro ao criar preço recorrente: {str(e)}")
                return {"error": f"Erro ao criar preço recorrente: {str(e)}"}
        
        # Configurar detalhes de pagamento com URLs dinâmicas
        domain = "https://planner-organizer.replit.app"
        
        checkout_session_params = {
            "line_items": [
                {
                    "price": plano["price_id"],
                    "quantity": 1,
                }
            ],
            "mode": mode,
            "success_url": f"{domain}/sucesso?session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url": f"{domain}/cancelado",
            "metadata": {
                "plan_id": request.plan_id,
                "plano_nome": plano["nome"],
                "user_id": request.user_id or "",
            }
        }
        
        # Se um e-mail foi fornecido, pré-preencher os dados do cliente
        if request.email:
            checkout_session_params["customer_email"] = request.email
        
        # Para assinaturas com período de teste gratuito
        if mode == "subscription" and plano["periodo_teste"] > 0:
            checkout_session_params["subscription_data"] = {
                "trial_period_days": plano["periodo_teste"]
            }
        
        # Adicionar informações de diagnóstico
        print(f"Criando sessão com parâmetros: {checkout_session_params}")
        
        # Criar sessão de checkout
        checkout_session = stripe.checkout.Session.create(**checkout_session_params)
        
        # Retornar a URL da sessão e o ID
        return {
            "id": checkout_session.id,
            "url": checkout_session.url
        }
    
    except stripe.error.StripeError as e:
        # Capturar e retornar erros do Stripe mais detalhados
        error_details = {
            "error": str(e),
            "error_type": type(e).__name__,
            "plan_id": request.plan_id
        }
        # Adicionar o modo apenas se já estiver definido
        if 'mode' in locals():
            error_details["mode"] = mode
            
        print(f"Erro do Stripe: {error_details}")
        return error_details
    except Exception as e:
        # Capturar outros erros
        return {"error": f"Erro ao criar sessão de checkout: {str(e)}"}

@app.post("/webhook")
async def webhook_handler(request: Request):
    """
    Manipulador de webhook para processar eventos do Stripe
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    endpoint_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    
    try:
        # Verificar a assinatura para autenticar o webhook
        if endpoint_secret and sig_header:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        else:
            # Se não há segredo de webhook, apenas analisar o JSON (menos seguro)
            data = await request.json()
            event = data
        
        # Processar eventos específicos
        if event["type"] == "checkout.session.completed":
            checkout_session = event["data"]["object"]
            # Aqui você pode processar a conclusão do checkout, como:
            # - Ativar uma assinatura
            # - Enviar e-mails de confirmação
            # - Atualizar banco de dados
            print(f"Checkout concluído com sucesso: {checkout_session['id']}")
            
        elif event["type"] == "customer.subscription.created":
            subscription = event["data"]["object"]
            # Processar a criação da assinatura
            print(f"Assinatura criada: {subscription['id']}")
            
        elif event["type"] == "customer.subscription.updated":
            subscription = event["data"]["object"]
            # Processar a atualização da assinatura
            print(f"Assinatura atualizada: {subscription['id']}")
            
        elif event["type"] == "customer.subscription.deleted":
            subscription = event["data"]["object"]
            # Processar o cancelamento da assinatura
            print(f"Assinatura cancelada: {subscription['id']}")
        
        # Retorna um código 200 para confirmar o recebimento
        return {"status": "success"}
    
    except Exception as e:
        print(f"Erro no webhook: {str(e)}")
        return {"error": str(e)}, 400

# Para rodar a aplicação localmente para teste
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)