"""
Módulo de integração com Stripe para processamento de pagamentos e assinaturas
"""
import os
import logging
import stripe
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Configuração do Stripe
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')

# Inicializar Stripe
if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY
else:
    logger.warning("STRIPE_SECRET_KEY não definida. Funcionalidades de pagamento estarão indisponíveis.")

class StripeIntegration:
    @staticmethod
    def criar_cliente(email, nome, metadata=None):
        """Cria um cliente no Stripe"""
        if not STRIPE_SECRET_KEY:
            logger.error("STRIPE_SECRET_KEY não configurada")
            return None
            
        try:
            cliente = stripe.Customer.create(
                email=email,
                name=nome,
                metadata=metadata or {}
            )
            return cliente.id
        except Exception as e:
            logger.error(f"Erro ao criar cliente no Stripe: {e}")
            return None
    
    @staticmethod
    def criar_assinatura(customer_id, price_id, metadata=None):
        """Cria uma assinatura para o cliente"""
        if not STRIPE_SECRET_KEY:
            logger.error("STRIPE_SECRET_KEY não configurada")
            return None
            
        try:
            assinatura = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": price_id}],
                metadata=metadata or {}
            )
            return assinatura
        except Exception as e:
            logger.error(f"Erro ao criar assinatura no Stripe: {e}")
            return None
    
    @staticmethod
    def cancelar_assinatura(subscription_id):
        """Cancela uma assinatura existente"""
        if not STRIPE_SECRET_KEY:
            logger.error("STRIPE_SECRET_KEY não configurada")
            return None
            
        try:
            return stripe.Subscription.delete(subscription_id)
        except Exception as e:
            logger.error(f"Erro ao cancelar assinatura no Stripe: {e}")
            return None
    
    @staticmethod
    def atualizar_assinatura(subscription_id, price_id):
        """Atualiza uma assinatura para um novo plano"""
        if not STRIPE_SECRET_KEY:
            logger.error("STRIPE_SECRET_KEY não configurada")
            return None
            
        try:
            # Obter a assinatura atual
            assinatura = stripe.Subscription.retrieve(subscription_id)
            
            # Obter o ID do item da assinatura (geralmente há apenas um)
            item_id = assinatura['items']['data'][0].id
            
            # Atualizar a assinatura
            assinatura_atualizada = stripe.Subscription.modify(
                subscription_id,
                items=[{
                    'id': item_id,
                    'price': price_id,
                }]
            )
            return assinatura_atualizada
        except Exception as e:
            logger.error(f"Erro ao atualizar assinatura no Stripe: {e}")
            return None
    
    @staticmethod
    def obter_detalhes_assinatura(subscription_id):
        """Obtém detalhes de uma assinatura"""
        if not STRIPE_SECRET_KEY:
            logger.error("STRIPE_SECRET_KEY não configurada")
            return None
            
        try:
            return stripe.Subscription.retrieve(subscription_id)
        except Exception as e:
            logger.error(f"Erro ao obter detalhes da assinatura: {e}")
            return None
    
    @staticmethod
    def criar_session_checkout(customer_id, price_id, success_url, cancel_url, metadata=None):
        """Cria uma sessão de checkout para pagamento"""
        if not STRIPE_SECRET_KEY:
            logger.error("STRIPE_SECRET_KEY não configurada")
            return None
            
        try:
            checkout_session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata or {}
            )
            return checkout_session
        except Exception as e:
            logger.error(f"Erro ao criar sessão de checkout: {e}")
            return None
    
    @staticmethod
    def processar_webhook(payload, sig_header):
        """Processa eventos recebidos via webhook do Stripe"""
        if not STRIPE_WEBHOOK_SECRET:
            logger.error("STRIPE_WEBHOOK_SECRET não configurada")
            return False, "STRIPE_WEBHOOK_SECRET não configurada"
            
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
            
            # Aqui você pode implementar a lógica para cada tipo de evento
            # Por exemplo:
            if event['type'] == 'checkout.session.completed':
                # Processar pagamento concluído
                session = event['data']['object']
                customer_id = session.get('customer')
                subscription_id = session.get('subscription')
                # Atualizar banco de dados com informações da assinatura
                logger.info(f"Checkout concluído para customer_id={customer_id}, subscription_id={subscription_id}")
                
            elif event['type'] == 'invoice.paid':
                # Processar fatura paga
                invoice = event['data']['object']
                customer_id = invoice.get('customer')
                subscription_id = invoice.get('subscription')
                # Registrar pagamento no banco de dados
                logger.info(f"Fatura paga para customer_id={customer_id}, subscription_id={subscription_id}")
                
            elif event['type'] == 'customer.subscription.updated':
                # Processar atualização de assinatura
                subscription = event['data']['object']
                customer_id = subscription.get('customer')
                status = subscription.get('status')
                # Atualizar status da assinatura no banco de dados
                logger.info(f"Assinatura atualizada para customer_id={customer_id}, status={status}")
                
            elif event['type'] == 'customer.subscription.deleted':
                # Processar cancelamento de assinatura
                subscription = event['data']['object']
                customer_id = subscription.get('customer')
                # Atualizar status da assinatura no banco de dados
                logger.info(f"Assinatura cancelada para customer_id={customer_id}")
            
            return True, event
        except Exception as e:
            logger.error(f"Erro ao processar webhook: {e}")
            return False, str(e)