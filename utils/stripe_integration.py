"""
Módulo para integração com o Stripe
Este módulo fornece funções para gerenciar assinaturas, pagamentos e webhooks do Stripe.
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple

import stripe
import jwt
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from stripe.error import StripeError

from utils.database import get_database_connection, get_engine
from utils.firebase_auth import decode_firebase_token

# Configurar logger
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Configurar Stripe API
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
STRIPE_PRICE_ID_MENSAL = os.environ.get('STRIPE_PRICE_ID_MENSAL')
STRIPE_PRICE_ID_ANUAL = os.environ.get('STRIPE_PRICE_ID_ANUAL')
APP_URL = os.environ.get('APP_URL', 'http://localhost:5000')

# Inicializar Stripe
stripe.api_key = STRIPE_API_KEY

def get_stripe_customer(usuario_id: str, email: str, nome: str) -> str:
    """
    Obtém ou cria um cliente no Stripe
    
    Args:
        usuario_id: ID do usuário no Firebase
        email: Email do usuário
        nome: Nome do usuário
        
    Returns:
        str: ID do cliente no Stripe
    """
    try:
        # Verificar se o cliente já existe no banco de dados
        engine = get_engine()
        with engine.connect() as conn:
            query = text("""
                SELECT stripe_customer_id 
                FROM assinaturas 
                WHERE usuario_id = :usuario_id 
                LIMIT 1
            """)
            result = conn.execute(query, {"usuario_id": usuario_id}).fetchone()
            
            if result and result[0]:
                # Cliente já existe, verificar se existe no Stripe
                try:
                    stripe.Customer.retrieve(result[0])
                    return result[0]
                except stripe.error.InvalidRequestError:
                    # Cliente não existe mais no Stripe, criar novo
                    pass
        
        # Criar novo cliente no Stripe
        customer = stripe.Customer.create(
            email=email,
            name=nome,
            metadata={"usuario_id": usuario_id}
        )
        
        return customer.id
        
    except Exception as e:
        logger.error(f"Erro ao obter/criar cliente Stripe: {str(e)}")
        raise

def criar_checkout_session(
    usuario_id: str, 
    email: str, 
    nome: str, 
    plano: str = "mensal"
) -> Dict[str, Any]:
    """
    Cria uma sessão de checkout do Stripe
    
    Args:
        usuario_id: ID do usuário no Firebase
        email: Email do usuário
        nome: Nome do usuário
        plano: Tipo de plano ('mensal' ou 'anual')
        
    Returns:
        Dict: Informações da sessão de checkout
    """
    try:
        # Obter ID do cliente no Stripe
        customer_id = get_stripe_customer(usuario_id, email, nome)
        
        # Determinar o preço com base no plano
        price_id = STRIPE_PRICE_ID_MENSAL if plano == "mensal" else STRIPE_PRICE_ID_ANUAL
        
        # Criar sessão de checkout
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=f'{APP_URL}/pages/minha_assinatura?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{APP_URL}/pages/minha_assinatura',
            metadata={
                'usuario_id': usuario_id
            }
        )
        
        return {
            "id": checkout_session.id,
            "url": checkout_session.url
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Erro ao criar sessão de checkout: {str(e)}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Erro inesperado ao criar sessão: {str(e)}")
        return {"error": f"Erro inesperado: {str(e)}"}

def criar_portal_cliente(usuario_id: str) -> Dict[str, Any]:
    """
    Cria uma sessão do portal de clientes do Stripe
    
    Args:
        usuario_id: ID do usuário no Firebase
        
    Returns:
        Dict: Informações da sessão do portal
    """
    try:
        # Obter ID do cliente no Stripe do banco de dados
        engine = get_engine()
        with engine.connect() as conn:
            query = text("""
                SELECT stripe_customer_id 
                FROM assinaturas 
                WHERE usuario_id = :usuario_id 
                LIMIT 1
            """)
            result = conn.execute(query, {"usuario_id": usuario_id}).fetchone()
            
            if not result or not result[0]:
                return {"error": "Usuário não possui assinatura ativa"}
            
            customer_id = result[0]
        
        # Criar sessão do portal
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=f'{APP_URL}/pages/minha_assinatura',
        )
        
        return {
            "id": session.id,
            "url": session.url
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Erro ao criar portal do cliente: {str(e)}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Erro inesperado ao criar portal: {str(e)}")
        return {"error": f"Erro inesperado: {str(e)}"}

def processar_webhook(payload: bytes, sig_header: str) -> Dict[str, Any]:
    """
    Processa eventos de webhook do Stripe
    
    Args:
        payload: Dados do evento
        sig_header: Cabeçalho de assinatura
        
    Returns:
        Dict: Resultado do processamento
    """
    try:
        # Verificar assinatura do webhook
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
        
        event_data = event['data']
        event_type = event['type']
        
        logger.info(f"Webhook recebido: {event_type}")
        
        # Processar diferentes tipos de eventos
        if event_type == 'checkout.session.completed':
            return _processar_checkout_completado(event_data['object'])
        
        elif event_type == 'invoice.paid':
            return _processar_fatura_paga(event_data['object'])
        
        elif event_type == 'customer.subscription.updated':
            return _processar_assinatura_atualizada(event_data['object'])
        
        elif event_type == 'customer.subscription.deleted':
            return _processar_assinatura_cancelada(event_data['object'])
        
        # Outros eventos não processados
        return {"status": "success", "message": f"Evento {event_type} não processado"}
        
    except stripe.error.SignatureVerificationError:
        logger.error("Assinatura de webhook inválida")
        return {"status": "error", "message": "Assinatura inválida"}
    except Exception as e:
        logger.error(f"Erro ao processar webhook: {str(e)}")
        return {"status": "error", "message": str(e)}

def _processar_checkout_completado(session: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processa evento de checkout completado
    
    Args:
        session: Dados da sessão de checkout
        
    Returns:
        Dict: Resultado do processamento
    """
    try:
        usuario_id = session.get('metadata', {}).get('usuario_id')
        customer_id = session.get('customer')
        subscription_id = session.get('subscription')
        
        if not usuario_id or not customer_id or not subscription_id:
            logger.error("Dados obrigatórios ausentes no evento de checkout")
            return {"status": "error", "message": "Dados obrigatórios ausentes"}
        
        # Obter detalhes da assinatura
        subscription = stripe.Subscription.retrieve(subscription_id)
        plan_id = subscription['items']['data'][0]['plan']['id']
        
        # Obter ID do plano no banco de dados
        engine = get_engine()
        with engine.connect() as conn:
            # Buscar ou criar plano no banco de dados
            query = text("""
                SELECT id FROM planos 
                WHERE stripe_price_id = :price_id 
                LIMIT 1
            """)
            result = conn.execute(query, {"price_id": plan_id}).fetchone()
            
            if not result:
                logger.error(f"Plano não encontrado: {plan_id}")
                return {"status": "error", "message": f"Plano não encontrado: {plan_id}"}
            
            plano_id = result[0]
            
            # Verificar se já existe assinatura para este usuário
            query = text("""
                SELECT id FROM assinaturas 
                WHERE usuario_id = :usuario_id 
                LIMIT 1
            """)
            result = conn.execute(query, {"usuario_id": usuario_id}).fetchone()
            
            if result:
                # Atualizar assinatura existente
                query = text("""
                    UPDATE assinaturas 
                    SET stripe_customer_id = :customer_id,
                        stripe_subscription_id = :subscription_id,
                        plano_id = :plano_id,
                        status = :status,
                        data_inicio = :data_inicio,
                        data_fim = :data_fim,
                        data_atualizacao = CURRENT_TIMESTAMP
                    WHERE usuario_id = :usuario_id
                    RETURNING id
                """)
            else:
                # Criar nova assinatura
                query = text("""
                    INSERT INTO assinaturas 
                    (usuario_id, stripe_customer_id, stripe_subscription_id, plano_id, status, data_inicio, data_fim)
                    VALUES 
                    (:usuario_id, :customer_id, :subscription_id, :plano_id, :status, :data_inicio, :data_fim)
                    RETURNING id
                """)
            
            # Executar query
            result = conn.execute(query, {
                "usuario_id": usuario_id,
                "customer_id": customer_id,
                "subscription_id": subscription_id,
                "plano_id": plano_id,
                "status": subscription['status'],
                "data_inicio": datetime.fromtimestamp(subscription['current_period_start']),
                "data_fim": datetime.fromtimestamp(subscription['current_period_end'])
            }).fetchone()
            
            assinatura_id = result[0]
            
            # Atualizar tipo de plano do usuário
            query = text("""
                UPDATE perfis 
                SET tipo_plano = :tipo_plano
                WHERE usuario_id = :usuario_id
            """)
            
            conn.execute(query, {
                "usuario_id": usuario_id,
                "tipo_plano": "pago"
            })
            
            conn.commit()
            
            return {
                "status": "success", 
                "message": "Assinatura criada/atualizada com sucesso",
                "assinatura_id": assinatura_id
            }
    
    except Exception as e:
        logger.error(f"Erro ao processar checkout: {str(e)}")
        return {"status": "error", "message": str(e)}

def _processar_fatura_paga(invoice: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processa evento de fatura paga
    
    Args:
        invoice: Dados da fatura
        
    Returns:
        Dict: Resultado do processamento
    """
    try:
        customer_id = invoice.get('customer')
        subscription_id = invoice.get('subscription')
        invoice_id = invoice.get('id')
        amount_paid = invoice.get('amount_paid')
        
        if not customer_id or not subscription_id or not invoice_id:
            logger.error("Dados obrigatórios ausentes no evento de fatura")
            return {"status": "error", "message": "Dados obrigatórios ausentes"}
        
        # Registrar pagamento no banco de dados
        engine = get_engine()
        with engine.connect() as conn:
            # Obter ID da assinatura
            query = text("""
                SELECT id FROM assinaturas 
                WHERE stripe_subscription_id = :subscription_id 
                LIMIT 1
            """)
            result = conn.execute(query, {"subscription_id": subscription_id}).fetchone()
            
            if not result:
                logger.error(f"Assinatura não encontrada: {subscription_id}")
                return {"status": "error", "message": f"Assinatura não encontrada: {subscription_id}"}
            
            assinatura_id = result[0]
            
            # Verificar se pagamento já foi registrado
            query = text("""
                SELECT id FROM pagamentos 
                WHERE stripe_invoice_id = :invoice_id 
                LIMIT 1
            """)
            result = conn.execute(query, {"invoice_id": invoice_id}).fetchone()
            
            if result:
                logger.info(f"Pagamento já registrado: {invoice_id}")
                return {"status": "success", "message": "Pagamento já registrado"}
            
            # Registrar pagamento
            query = text("""
                INSERT INTO pagamentos 
                (assinatura_id, stripe_invoice_id, valor, status, data_pagamento)
                VALUES 
                (:assinatura_id, :invoice_id, :valor, :status, :data_pagamento)
                RETURNING id
            """)
            
            result = conn.execute(query, {
                "assinatura_id": assinatura_id,
                "invoice_id": invoice_id,
                "valor": amount_paid / 100,  # Converter de centavos para reais
                "status": "pago",
                "data_pagamento": datetime.now()
            }).fetchone()
            
            conn.commit()
            
            return {
                "status": "success", 
                "message": "Pagamento registrado com sucesso",
                "pagamento_id": result[0]
            }
    
    except Exception as e:
        logger.error(f"Erro ao processar fatura: {str(e)}")
        return {"status": "error", "message": str(e)}

def _processar_assinatura_atualizada(subscription: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processa evento de assinatura atualizada
    
    Args:
        subscription: Dados da assinatura
        
    Returns:
        Dict: Resultado do processamento
    """
    try:
        subscription_id = subscription.get('id')
        status = subscription.get('status')
        
        if not subscription_id or not status:
            logger.error("Dados obrigatórios ausentes no evento de assinatura")
            return {"status": "error", "message": "Dados obrigatórios ausentes"}
        
        # Atualizar assinatura no banco de dados
        engine = get_engine()
        with engine.connect() as conn:
            query = text("""
                UPDATE assinaturas 
                SET status = :status,
                    data_inicio = :data_inicio,
                    data_fim = :data_fim,
                    data_atualizacao = CURRENT_TIMESTAMP
                WHERE stripe_subscription_id = :subscription_id
                RETURNING usuario_id
            """)
            
            result = conn.execute(query, {
                "subscription_id": subscription_id,
                "status": status,
                "data_inicio": datetime.fromtimestamp(subscription['current_period_start']),
                "data_fim": datetime.fromtimestamp(subscription['current_period_end'])
            }).fetchone()
            
            if not result:
                logger.error(f"Assinatura não encontrada: {subscription_id}")
                return {"status": "error", "message": f"Assinatura não encontrada: {subscription_id}"}
            
            usuario_id = result[0]
            
            # Atualizar tipo de plano do usuário
            tipo_plano = "gratuito" if status in ["canceled", "unpaid"] else "pago"
            
            query = text("""
                UPDATE perfis 
                SET tipo_plano = :tipo_plano
                WHERE usuario_id = :usuario_id
            """)
            
            conn.execute(query, {
                "usuario_id": usuario_id,
                "tipo_plano": tipo_plano
            })
            
            conn.commit()
            
            return {
                "status": "success", 
                "message": "Assinatura atualizada com sucesso",
                "usuario_id": usuario_id
            }
    
    except Exception as e:
        logger.error(f"Erro ao atualizar assinatura: {str(e)}")
        return {"status": "error", "message": str(e)}

def _processar_assinatura_cancelada(subscription: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processa evento de assinatura cancelada
    
    Args:
        subscription: Dados da assinatura
        
    Returns:
        Dict: Resultado do processamento
    """
    try:
        subscription_id = subscription.get('id')
        canceled_at = subscription.get('canceled_at')
        
        if not subscription_id:
            logger.error("ID de assinatura ausente no evento")
            return {"status": "error", "message": "ID de assinatura ausente"}
        
        # Atualizar assinatura no banco de dados
        engine = get_engine()
        with engine.connect() as conn:
            query = text("""
                UPDATE assinaturas 
                SET status = 'canceled',
                    data_cancelamento = :data_cancelamento,
                    data_atualizacao = CURRENT_TIMESTAMP
                WHERE stripe_subscription_id = :subscription_id
                RETURNING usuario_id
            """)
            
            result = conn.execute(query, {
                "subscription_id": subscription_id,
                "data_cancelamento": datetime.fromtimestamp(canceled_at) if canceled_at else datetime.now()
            }).fetchone()
            
            if not result:
                logger.error(f"Assinatura não encontrada: {subscription_id}")
                return {"status": "error", "message": f"Assinatura não encontrada: {subscription_id}"}
            
            usuario_id = result[0]
            
            # Atualizar tipo de plano do usuário
            query = text("""
                UPDATE perfis 
                SET tipo_plano = 'gratuito'
                WHERE usuario_id = :usuario_id
            """)
            
            conn.execute(query, {
                "usuario_id": usuario_id
            })
            
            conn.commit()
            
            return {
                "status": "success", 
                "message": "Assinatura cancelada com sucesso",
                "usuario_id": usuario_id
            }
    
    except Exception as e:
        logger.error(f"Erro ao cancelar assinatura: {str(e)}")
        return {"status": "error", "message": str(e)}

def obter_status_assinatura(usuario_id: str) -> Dict[str, Any]:
    """
    Obtém o status da assinatura do usuário
    
    Args:
        usuario_id: ID do usuário no Firebase
        
    Returns:
        Dict: Informações da assinatura
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            query = text("""
                SELECT * FROM vw_status_assinatura
                WHERE usuario_id = :usuario_id
            """)
            
            result = conn.execute(query, {"usuario_id": usuario_id}).fetchone()
            
            if not result:
                return {
                    "status_assinatura": "sem_assinatura",
                    "tipo_plano": "gratuito",
                    "possui_assinatura": False
                }
            
            # Converter para dicionário
            columns = result.keys()
            assinatura = {col: getattr(result, col) for col in columns}
            
            # Adicionar flag de posse de assinatura
            assinatura["possui_assinatura"] = assinatura["status_assinatura"] != "sem_assinatura"
            
            return assinatura
    
    except Exception as e:
        logger.error(f"Erro ao obter status da assinatura: {str(e)}")
        return {
            "status_assinatura": "erro",
            "tipo_plano": "gratuito",
            "possui_assinatura": False,
            "erro": str(e)
        }

def verificar_limite_atingido(usuario_id: str, tipo_limite: str) -> bool:
    """
    Verifica se o usuário atingiu o limite do plano
    
    Args:
        usuario_id: ID do usuário no Firebase
        tipo_limite: Tipo de limite a verificar ('clientes', 'propostas', 'produtos')
        
    Returns:
        bool: True se o limite foi atingido, False caso contrário
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            query = text(f"""
                SELECT limite_{tipo_limite}_atingido FROM vw_status_assinatura
                WHERE usuario_id = :usuario_id
            """)
            
            result = conn.execute(query, {"usuario_id": usuario_id}).fetchone()
            
            if not result:
                return False
            
            return result[0]
    
    except Exception as e:
        logger.error(f"Erro ao verificar limite: {str(e)}")
        return False