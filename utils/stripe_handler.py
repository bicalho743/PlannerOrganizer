"""
Módulo para gerenciar a integração com o Stripe
"""
import os
import stripe
import json
from datetime import datetime

# Configuração do Stripe
stripe.api_key = os.environ.get('STRIPE_API_KEY')
WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')

# Importação adiada para evitar dependência circular
from utils.assinatura_db import (
    registrar_assinatura,
    atualizar_status_assinatura,
    cancelar_assinatura
)

def criar_sessao_checkout(price_id, usuario_id, usuario_email, usuario_nome, success_url, cancel_url):
    """
    Cria uma sessão de checkout no Stripe para um determinado plano.
    
    Args:
        price_id: ID do preço no Stripe
        usuario_id: ID do usuário no sistema
        usuario_email: E-mail do usuário
        usuario_nome: Nome do usuário
        success_url: URL para redirecionamento em caso de sucesso
        cancel_url: URL para redirecionamento em caso de cancelamento
        
    Returns:
        dict: ID da sessão e URL para redirecionamento ou mensagem de erro
    """
    try:
        if not stripe.api_key:
            return {
                'success': False,
                'message': 'Chave da API Stripe não configurada'
            }
            
        if not price_id:
            return {
                'success': False,
                'message': 'ID de preço não especificado'
            }
        
        # Determinar o modo com base no tipo de price_id
        mode = 'subscription'
        try:
            price = stripe.Price.retrieve(price_id)
            if price.type == 'one_time':
                mode = 'payment'
        except Exception as e:
            print(f"Erro ao verificar tipo do preço: {str(e)}")
        
        # Criar sessão de checkout
        checkout_session = stripe.checkout.Session.create(
            customer_email=usuario_email,
            client_reference_id=str(usuario_id),
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode=mode,  # 'subscription' para assinaturas recorrentes, 'payment' para pagamento único
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'usuario_id': str(usuario_id),
                'usuario_nome': usuario_nome,
                'usuario_email': usuario_email
            }
        )
        
        return {
            'success': True,
            'session_id': checkout_session.id,
            'checkout_url': checkout_session.url
        }
    
    except stripe.error.StripeError as e:
        return {
            'success': False,
            'message': f'Erro do Stripe: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Erro ao criar sessão de checkout: {str(e)}'
        }

def processar_webhook_evento(payload, sig_header):
    """
    Processa eventos de webhook do Stripe.
    
    Args:
        payload: Corpo do payload do webhook
        sig_header: Cabeçalho de assinatura do Stripe
        
    Returns:
        dict: Resultado do processamento do evento
    """
    try:
        if not WEBHOOK_SECRET:
            return {
                'success': False,
                'message': 'Segredo de webhook não configurado'
            }
        
        # Verificar a assinatura do evento
        event = stripe.Webhook.construct_event(
            payload, sig_header, WEBHOOK_SECRET
        )
        
        # Identificar o tipo de evento e processar adequadamente
        tipo_evento = event['type']
        
        print(f"Evento Stripe recebido: {tipo_evento}")
        
        resultado = {'success': True, 'message': 'Evento processado com sucesso'}
        
        # Processar diferentes tipos de eventos
        if tipo_evento == 'checkout.session.completed':
            resultado = _processar_checkout_completed(event)
        
        elif tipo_evento == 'invoice.paid':
            resultado = _processar_invoice_paid(event)
        
        elif tipo_evento == 'customer.subscription.updated':
            resultado = _processar_subscription_updated(event)
        
        elif tipo_evento == 'customer.subscription.deleted':
            resultado = _processar_subscription_deleted(event)
        
        # Registrar resultado para verificação
        print(f"Processamento do evento {tipo_evento}: {resultado}")
        
        return resultado
    
    except stripe.error.SignatureVerificationError:
        return {
            'success': False,
            'message': 'Assinatura do webhook inválida'
        }
    except stripe.error.StripeError as e:
        return {
            'success': False,
            'message': f'Erro do Stripe: {str(e)}'
        }
    except Exception as e:
        import traceback
        return {
            'success': False,
            'message': f'Erro ao processar evento: {str(e)}',
            'traceback': traceback.format_exc()
        }

def _processar_checkout_completed(evento):
    """
    Processa o evento de checkout.session.completed.
    
    Args:
        evento: Objeto de evento do Stripe
        
    Returns:
        dict: Resultado do processamento
    """
    try:
        # Extrair dados da sessão de checkout
        session = evento['data']['object']
        
        usuario_id = session.get('client_reference_id')
        if not usuario_id:
            usuario_id = session.get('metadata', {}).get('usuario_id')
        
        if not usuario_id:
            return {
                'success': False,
                'message': 'ID de usuário não encontrado na sessão'
            }
        
        # Converter para inteiro se for string
        usuario_id = int(usuario_id)
        
        # Obter informações do modo de pagamento e plano
        mode = session.get('mode')
        
        # Determinar o tipo de plano com base nos produtos da sessão
        plano = "Desconhecido"
        
        try:
            # Obter informações das linhas de compra (produtos)
            line_items = stripe.checkout.Session.list_line_items(session.id)
            
            if line_items and line_items.data:
                # Obter primeiro item da lista
                primeiro_item = line_items.data[0]
                
                # Recuperar informações do preço e produto
                price_id = primeiro_item.price.id
                produto = stripe.Product.retrieve(primeiro_item.price.product)
                
                # Determinar plano com base no nome do produto
                nome_produto = produto.name.lower()
                
                if 'mensal' in nome_produto:
                    plano = 'Mensal'
                elif 'anual' in nome_produto:
                    plano = 'Anual'
                elif 'vitalício' in nome_produto or 'vitalicio' in nome_produto:
                    plano = 'Vitalicio'
                else:
                    plano = produto.name  # Usar o nome exato do produto
        
        except Exception as e:
            print(f"Erro ao obter detalhes do produto: {str(e)}")
            # Fallback - tentar determinar o plano pelo modo
            if mode == 'subscription':
                plano = 'Mensal'  # Assumir mensal por padrão para assinaturas
            else:
                plano = 'Vitalicio'  # Assumir vitalício para pagamentos únicos
        
        # Obter IDs do cliente e assinatura
        customer_id = session.get('customer')
        subscription_id = session.get('subscription')
        
        # Registrar a assinatura no banco de dados
        resultado = registrar_assinatura(
            usuario_id=usuario_id,
            plano=plano,
            subscription_id=subscription_id,
            customer_id=customer_id,
            status="ativa",
            metadados={
                'evento': 'checkout.session.completed',
                'timestamp': datetime.fromtimestamp(evento.get('created')).isoformat(),
                'session_id': session.id,
                'modo': mode
            }
        )
        
        print(f"Assinatura registrada: {resultado}")
        
        # Tentativa de enviar e-mail de confirmação
        try:
            from utils.email_sender import enviar_confirmacao_assinatura
            email = session.get('customer_email') or session.get('metadata', {}).get('usuario_email')
            nome = session.get('metadata', {}).get('usuario_nome', 'Cliente')
            
            if email:
                enviar_confirmacao_assinatura(email, nome, plano)
        except Exception as e:
            print(f"Erro ao enviar e-mail de confirmação: {str(e)}")
        
        return {
            'success': resultado.get('sucesso', False),
            'message': resultado.get('mensagem', 'Erro interno'),
            'plano': plano,
            'customer_id': customer_id,
            'subscription_id': subscription_id
        }
    
    except Exception as e:
        import traceback
        return {
            'success': False,
            'message': f'Erro ao processar checkout: {str(e)}',
            'traceback': traceback.format_exc()
        }

def _processar_invoice_paid(evento):
    """
    Processa o evento de invoice.paid.
    
    Args:
        evento: Objeto de evento do Stripe
        
    Returns:
        dict: Resultado do processamento
    """
    try:
        # Extrair dados da fatura
        invoice = evento['data']['object']
        
        # Obter ID da assinatura associada
        subscription_id = invoice.get('subscription')
        
        if not subscription_id:
            return {
                'success': False,
                'message': 'Fatura não associada a uma assinatura'
            }
        
        # Recuperar dados da assinatura
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        # Obter ID do cliente
        customer_id = invoice.get('customer')
        
        # Obter metadata do cliente que pode conter o usuario_id
        customer = stripe.Customer.retrieve(customer_id)
        usuario_id = customer.get('metadata', {}).get('usuario_id')
        
        # Se não tiver usuario_id nos metadados, tentar encontrar na assinatura
        if not usuario_id:
            usuario_id = subscription.get('metadata', {}).get('usuario_id')
        
        # Se ainda não tiver, buscar em assinaturas anteriores
        if not usuario_id:
            # Este é um ponto que pode ser expandido para buscar o usuario_id
            # em outras fontes de dados, como banco próprio
            pass
        
        # Se conseguiu encontrar o usuario_id, atualizar o status da assinatura
        if usuario_id:
            usuario_id = int(usuario_id)
            
            # Determinar o plano com base na assinatura
            plano = "Desconhecido"
            
            try:
                items = subscription.get('items', {}).get('data', [])
                if items:
                    price_id = items[0].get('price', {}).get('id')
                    produto = stripe.Product.retrieve(items[0].get('price', {}).get('product'))
                    
                    nome_produto = produto.name.lower()
                    if 'mensal' in nome_produto:
                        plano = 'Mensal'
                    elif 'anual' in nome_produto:
                        plano = 'Anual'
                    else:
                        plano = produto.name
            except Exception as e:
                print(f"Erro ao obter detalhes do produto: {str(e)}")
            
            # Atualizar a assinatura no banco de dados
            resultado = atualizar_status_assinatura(
                subscription_id=subscription_id,
                novo_status="ativa"
            )
            
            # Tentativa de enviar e-mail de confirmação
            try:
                from utils.email_sender import enviar_notificacao_pagamento
                email = customer.get('email')
                nome = customer.get('name', 'Cliente')
                
                if email:
                    enviar_notificacao_pagamento(email, nome, plano)
            except Exception as e:
                print(f"Erro ao enviar e-mail de notificação: {str(e)}")
            
            return {
                'success': resultado.get('sucesso', False),
                'message': resultado.get('mensagem', 'Erro interno'),
                'plano': plano,
                'customer_id': customer_id,
                'subscription_id': subscription_id
            }
        
        return {
            'success': False,
            'message': 'ID de usuário não encontrado'
        }
    
    except Exception as e:
        import traceback
        return {
            'success': False,
            'message': f'Erro ao processar pagamento: {str(e)}',
            'traceback': traceback.format_exc()
        }

def _processar_subscription_updated(evento):
    """
    Processa o evento de atualização de assinatura.
    
    Args:
        evento: Objeto de evento do Stripe
        
    Returns:
        dict: Resultado do processamento
    """
    try:
        # Extrair dados da assinatura atualizada
        subscription = evento['data']['object']
        
        # Obter ID da assinatura
        subscription_id = subscription.get('id')
        
        if not subscription_id:
            return {
                'success': False,
                'message': 'ID de assinatura não encontrado'
            }
        
        # Determinar o novo status
        status = subscription.get('status', 'unknown')
        
        # Mapear status do Stripe para nosso sistema
        status_mapeado = {
            'active': 'ativa',
            'past_due': 'pendente',
            'unpaid': 'pendente',
            'canceled': 'cancelada',
            'incomplete': 'pendente',
            'incomplete_expired': 'cancelada',
            'trialing': 'teste',
            'paused': 'pausada'
        }.get(status, status)
        
        # Atualizar a assinatura no banco de dados
        resultado = atualizar_status_assinatura(
            subscription_id=subscription_id,
            novo_status=status_mapeado
        )
        
        return {
            'success': resultado.get('sucesso', False),
            'message': resultado.get('mensagem', 'Erro interno'),
            'novo_status': status_mapeado,
            'subscription_id': subscription_id
        }
    
    except Exception as e:
        import traceback
        return {
            'success': False,
            'message': f'Erro ao processar atualização de assinatura: {str(e)}',
            'traceback': traceback.format_exc()
        }

def _processar_subscription_deleted(evento):
    """
    Processa o evento de cancelamento de assinatura.
    
    Args:
        evento: Objeto de evento do Stripe
        
    Returns:
        dict: Resultado do processamento
    """
    try:
        # Extrair dados da assinatura cancelada
        subscription = evento['data']['object']
        
        # Obter ID da assinatura
        subscription_id = subscription.get('id')
        
        if not subscription_id:
            return {
                'success': False,
                'message': 'ID de assinatura não encontrado'
            }
        
        # Cancelar a assinatura no banco de dados
        resultado = cancelar_assinatura(subscription_id)
        
        # Tentar enviar email de notificação de cancelamento
        try:
            customer_id = subscription.get('customer')
            if customer_id:
                customer = stripe.Customer.retrieve(customer_id)
                email = customer.get('email')
                nome = customer.get('name', 'Cliente')
                
                if email:
                    from utils.email_sender import enviar_notificacao_cancelamento
                    enviar_notificacao_cancelamento(email, nome)
        except Exception as e:
            print(f"Erro ao enviar e-mail de cancelamento: {str(e)}")
        
        return {
            'success': resultado.get('sucesso', False),
            'message': resultado.get('mensagem', 'Erro interno'),
            'subscription_id': subscription_id
        }
    
    except Exception as e:
        import traceback
        return {
            'success': False,
            'message': f'Erro ao processar cancelamento de assinatura: {str(e)}',
            'traceback': traceback.format_exc()
        }

def obter_url_gerenciamento_assinatura(customer_id):
    """
    Cria uma URL para o portal de gerenciamento de assinatura do cliente.
    
    Args:
        customer_id: ID do cliente no Stripe
        
    Returns:
        dict: URL para o portal ou mensagem de erro
    """
    try:
        if not stripe.api_key:
            return {
                'success': False,
                'message': 'Chave da API Stripe não configurada'
            }
        
        # URL base para retorno após ações no portal
        return_url = os.environ.get('APP_URL', 'https://www.plannerorganiza.com.br')
        return_url += "/minha_assinatura"
        
        # Criar sessão do portal de clientes
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        
        return {
            'success': True,
            'url': session.url
        }
    
    except stripe.error.StripeError as e:
        return {
            'success': False,
            'message': f'Erro do Stripe: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Erro ao criar portal de gerenciamento: {str(e)}'
        }

def verificar_status_assinatura(subscription_id):
    """
    Verifica o status atual de uma assinatura.
    
    Args:
        subscription_id: ID da assinatura no Stripe
        
    Returns:
        dict: Status da assinatura e detalhes
    """
    try:
        if not stripe.api_key:
            return {
                'success': False,
                'message': 'Chave da API Stripe não configurada'
            }
        
        # Obter dados da assinatura
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        # Mapear status do Stripe para nosso sistema
        status = subscription.get('status', 'unknown')
        status_mapeado = {
            'active': 'ativa',
            'past_due': 'pendente',
            'unpaid': 'pendente',
            'canceled': 'cancelada',
            'incomplete': 'pendente',
            'incomplete_expired': 'cancelada',
            'trialing': 'teste',
            'paused': 'pausada'
        }.get(status, status)
        
        # Verificar data de término de assinatura
        current_period_end = subscription.get('current_period_end')
        data_fim = None
        if current_period_end:
            data_fim = datetime.fromtimestamp(current_period_end).strftime('%d/%m/%Y')
        
        return {
            'success': True,
            'status': status_mapeado,
            'status_original': status,
            'data_fim': data_fim,
            'detalhes': {
                'canceled_at': subscription.get('canceled_at'),
                'cancel_at': subscription.get('cancel_at'),
                'current_period_start': subscription.get('current_period_start'),
                'current_period_end': current_period_end
            }
        }
    
    except stripe.error.StripeError as e:
        return {
            'success': False,
            'message': f'Erro do Stripe: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Erro ao verificar status da assinatura: {str(e)}'
        }