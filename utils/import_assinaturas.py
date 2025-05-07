"""
Módulo para importação de funções de gerenciamento de assinaturas
"""
import os
from datetime import datetime, timedelta
import stripe

# Configuração do Stripe
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY')
stripe.api_key = STRIPE_API_KEY

# Importação de funções de gerenciamento de banco de dados
from utils.assinatura_db import (
    registrar_assinatura,
    obter_assinatura_usuario,
    atualizar_status_assinatura,
    cancelar_assinatura,
    verificar_assinatura_ativa
)

# Importação de funções para envio de e-mails
from utils.email_sender import (
    enviar_confirmacao_assinatura,
    enviar_notificacao_pagamento,
    enviar_lembrete_renovacao,
    enviar_notificacao_cancelamento
)

# Função para criar uma sessão de checkout do Stripe
def criar_sessao_checkout(price_id, usuario_id, usuario_email=None, usuario_nome=None,
                         success_url=None, cancel_url=None):
    """
    Cria uma sessão de checkout do Stripe
    
    Args:
        price_id: ID do preço no Stripe
        usuario_id: ID do usuário
        usuario_email: E-mail do usuário (opcional)
        usuario_nome: Nome do usuário (opcional)
        success_url: URL de redirecionamento após sucesso (opcional)
        cancel_url: URL de redirecionamento após cancelamento (opcional)
        
    Returns:
        dict: Resultado da operação
    """
    try:
        if not STRIPE_API_KEY:
            return {
                'success': False,
                'message': 'Chave de API do Stripe não configurada'
            }
            
        # Configurar URLs de redirecionamento padrão
        if not success_url:
            success_url = os.environ.get('APP_URL', 'http://localhost:5000') + '/minha_assinatura?status=success'
            
        if not cancel_url:
            cancel_url = os.environ.get('APP_URL', 'http://localhost:5000') + '/minha_assinatura?status=cancel'
        
        # Metadados para rastreabilidade
        metadata = {
            'usuario_id': usuario_id,
            'created_at': datetime.now().isoformat()
        }
        
        if usuario_nome:
            metadata['usuario_nome'] = usuario_nome
            
        if usuario_email:
            metadata['usuario_email'] = usuario_email
        
        # Determinar se deve incluir o período de teste
        # Planos anuais e vitalício têm teste grátis de 7 dias
        add_trial = price_id in [os.environ.get('STRIPE_PRICE_ID_ANUAL'), os.environ.get('STRIPE_PRICE_ID_VITALICIO')]
        
        # Parâmetros base
        checkout_params = {
            'payment_method_types': ['card'],
            'line_items': [
                {
                    'price': price_id,
                    'quantity': 1,
                },
            ],
            'mode': 'subscription',
            'success_url': success_url,
            'cancel_url': cancel_url,
            'customer_email': usuario_email,
            'metadata': metadata
        }
        
        # Adicionar período de teste se aplicável
        if add_trial:
            checkout_params['subscription_data'] = {
                'trial_period_days': 7
            }
        
        # Criar sessão de checkout
        checkout_session = stripe.checkout.Session.create(**checkout_params)
        
        return {
            'success': True,
            'checkout_url': checkout_session.url,
            'session_id': checkout_session.id
        }
        
    except stripe.error.StripeError as e:
        print(f"Erro Stripe: {str(e)}")
        return {
            'success': False,
            'message': f'Erro do Stripe: {str(e)}'
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        return {
            'success': False,
            'message': f'Erro ao criar sessão de checkout: {str(e)}'
        }

# Função para processar webhook do Stripe
def processar_webhook_evento(payload, sig_header):
    """
    Processa um evento de webhook do Stripe
    
    Args:
        payload: Conteúdo do webhook
        sig_header: Cabeçalho de assinatura
        
    Returns:
        dict: Resultado do processamento
    """
    try:
        if not STRIPE_API_KEY:
            return {
                'success': False,
                'message': 'Chave de API do Stripe não configurada'
            }
            
        # Obter a chave secreta para verificação de webhooks
        webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
        
        if not webhook_secret:
            return {
                'success': False,
                'message': 'Chave secreta de webhook não configurada'
            }
        
        # Verificar assinatura do webhook
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except ValueError as e:
            # Payload inválido
            return {
                'success': False,
                'message': f'Payload inválido: {str(e)}'
            }
        except stripe.error.SignatureVerificationError as e:
            # Assinatura inválida
            return {
                'success': False,
                'message': f'Assinatura inválida: {str(e)}'
            }
            
        # Processar o evento com base no tipo
        print(f"Evento recebido: {event['type']}")
        
        # Checkout completado
        if event['type'] == 'checkout.session.completed':
            return processar_checkout_completado(event)
            
        # Pagamento bem-sucedido
        elif event['type'] == 'invoice.payment_succeeded':
            return processar_pagamento_bem_sucedido(event)
            
        # Pagamento falhou
        elif event['type'] == 'invoice.payment_failed':
            return processar_pagamento_falhou(event)
            
        # Assinatura cancelada
        elif event['type'] == 'customer.subscription.deleted':
            return processar_assinatura_cancelada(event)
            
        # Outros eventos
        return {
            'success': True,
            'message': f'Evento {event["type"]} recebido, mas não processado'
        }
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        return {
            'success': False,
            'message': f'Erro ao processar webhook: {str(e)}'
        }

# Função para processar checkout completado
def processar_checkout_completado(event):
    """
    Processa um evento de checkout completado
    
    Args:
        event: Evento do Stripe
        
    Returns:
        dict: Resultado do processamento
    """
    try:
        # Extrair dados da sessão
        session = event['data']['object']
        
        # Obter metadados
        metadata = session.get('metadata', {})
        usuario_id = metadata.get('usuario_id')
        usuario_nome = metadata.get('usuario_nome', 'Usuário')
        usuario_email = metadata.get('customer_email') or metadata.get('usuario_email')
        
        if not usuario_id:
            return {
                'success': False,
                'message': 'ID do usuário não encontrado nos metadados'
            }
            
        # Obter detalhes do modo e preço
        mode = session.get('mode')
        
        if mode == 'subscription':
            # Obter detalhes da assinatura
            subscription_id = session.get('subscription')
            
            if subscription_id:
                # Obter dados da assinatura
                subscription = stripe.Subscription.retrieve(subscription_id)
                customer_id = subscription.get('customer')
                
                # Obter plano
                plano = None
                preco_id = None
                
                if subscription.get('items') and subscription['items'].get('data'):
                    item = subscription['items']['data'][0]
                    preco_id = item.get('price', {}).get('id')
                    
                # Determinar o plano com base no preço
                if preco_id == os.environ.get('STRIPE_PRICE_ID_MENSAL'):
                    plano = 'Mensal'
                    periodo = 30
                elif preco_id == os.environ.get('STRIPE_PRICE_ID_ANUAL'):
                    plano = 'Anual'
                    periodo = 365
                elif preco_id == os.environ.get('STRIPE_PRICE_ID_VITALICIO'):
                    plano = 'Vitalicio'
                    periodo = None
                else:
                    plano = 'Desconhecido'
                    periodo = 30
                
                # Calcular datas
                data_inicio = datetime.now()
                data_fim = None
                
                if periodo:
                    data_fim = data_inicio + timedelta(days=periodo)
                
                # Registrar assinatura no banco de dados
                resultado_registro = registrar_assinatura(
                    usuario_id=usuario_id,
                    plano=plano,
                    customer_id=customer_id,
                    subscription_id=subscription_id,
                    status='ativo',
                    data_inicio=data_inicio,
                    data_fim=data_fim
                )
                
                if not resultado_registro.get('sucesso'):
                    print(f"Erro ao registrar assinatura: {resultado_registro.get('mensagem')}")
                
                # Enviar e-mail de confirmação
                if usuario_email:
                    enviar_confirmacao_assinatura(
                        destinatario=usuario_email,
                        nome=usuario_nome,
                        plano=plano
                    )
                
                return {
                    'success': True,
                    'message': f'Assinatura do plano {plano} registrada com sucesso'
                }
            
        return {
            'success': True,
            'message': 'Checkout completado processado, mas não é uma assinatura'
        }
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        return {
            'success': False,
            'message': f'Erro ao processar checkout completado: {str(e)}'
        }

# Função para processar pagamento bem-sucedido
def processar_pagamento_bem_sucedido(event):
    """
    Processa um evento de pagamento bem-sucedido
    
    Args:
        event: Evento do Stripe
        
    Returns:
        dict: Resultado do processamento
    """
    try:
        # Extrair dados da fatura
        invoice = event['data']['object']
        
        # Obter ID do cliente e assinatura
        customer_id = invoice.get('customer')
        subscription_id = invoice.get('subscription')
        
        if not customer_id or not subscription_id:
            return {
                'success': False,
                'message': 'Fatura sem cliente ou assinatura'
            }
            
        # Obter cliente
        try:
            customer = stripe.Customer.retrieve(customer_id)
            usuario_email = customer.get('email')
            usuario_nome = customer.get('name', 'Usuário')
        except:
            usuario_email = None
            usuario_nome = 'Usuário'
            
        # Obter detalhes da assinatura
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            # Obter plano
            plano = None
            preco_id = None
            
            if subscription.get('items') and subscription['items'].get('data'):
                item = subscription['items']['data'][0]
                preco_id = item.get('price', {}).get('id')
                
            # Determinar o plano com base no preço
            if preco_id == os.environ.get('STRIPE_PRICE_ID_MENSAL'):
                plano = 'Mensal'
                periodo = 30
            elif preco_id == os.environ.get('STRIPE_PRICE_ID_ANUAL'):
                plano = 'Anual'
                periodo = 365
            elif preco_id == os.environ.get('STRIPE_PRICE_ID_VITALICIO'):
                plano = 'Vitalicio'
                periodo = None
            else:
                plano = 'Desconhecido'
                periodo = 30
                
            # Obter metadados da assinatura
            metadata = subscription.get('metadata', {})
            usuario_id = metadata.get('usuario_id')
            
            if not usuario_id:
                # Tentar buscar na lista de assinaturas por subscription_id
                from utils.assinatura_db import obter_assinatura_por_subscription_id
                resultado_busca = obter_assinatura_por_subscription_id(subscription_id)
                
                if resultado_busca.get('sucesso'):
                    usuario_id = resultado_busca.get('assinatura', {}).get('usuario_id')
            
            if usuario_id:
                # Calcular datas
                data_inicio = datetime.now()
                data_fim = None
                
                if periodo:
                    data_fim = data_inicio + timedelta(days=periodo)
                
                # Atualizar assinatura no banco de dados
                resultado_atualizacao = atualizar_status_assinatura(
                    usuario_id=usuario_id,
                    status='ativo',
                    plano=plano,
                    data_inicio=data_inicio,
                    data_fim=data_fim
                )
                
                if not resultado_atualizacao.get('sucesso'):
                    print(f"Erro ao atualizar assinatura: {resultado_atualizacao.get('mensagem')}")
                
                # Enviar e-mail de notificação
                if usuario_email:
                    enviar_notificacao_pagamento(
                        destinatario=usuario_email,
                        nome=usuario_nome,
                        plano=plano
                    )
                
                return {
                    'success': True,
                    'message': f'Pagamento processado com sucesso para o plano {plano}'
                }
            
        except Exception as e:
            print(f"Erro ao processar detalhes da assinatura: {str(e)}")
            
        return {
            'success': True,
            'message': 'Pagamento processado, mas não foi possível atualizar a assinatura'
        }
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        return {
            'success': False,
            'message': f'Erro ao processar pagamento bem-sucedido: {str(e)}'
        }

# Função para processar pagamento que falhou
def processar_pagamento_falhou(event):
    """
    Processa um evento de pagamento que falhou
    
    Args:
        event: Evento do Stripe
        
    Returns:
        dict: Resultado do processamento
    """
    try:
        # Extrair dados da fatura
        invoice = event['data']['object']
        
        # Obter ID do cliente e assinatura
        customer_id = invoice.get('customer')
        subscription_id = invoice.get('subscription')
        
        if not customer_id or not subscription_id:
            return {
                'success': False,
                'message': 'Fatura sem cliente ou assinatura'
            }
            
        # Obter detalhes da assinatura
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            # Obter metadados da assinatura
            metadata = subscription.get('metadata', {})
            usuario_id = metadata.get('usuario_id')
            
            if not usuario_id:
                # Tentar buscar na lista de assinaturas por subscription_id
                from utils.assinatura_db import obter_assinatura_por_subscription_id
                resultado_busca = obter_assinatura_por_subscription_id(subscription_id)
                
                if resultado_busca.get('sucesso'):
                    usuario_id = resultado_busca.get('assinatura', {}).get('usuario_id')
            
            if usuario_id:
                # Atualizar status para 'pendente'
                resultado_atualizacao = atualizar_status_assinatura(
                    usuario_id=usuario_id,
                    status='pendente'
                )
                
                if not resultado_atualizacao.get('sucesso'):
                    print(f"Erro ao atualizar assinatura: {resultado_atualizacao.get('mensagem')}")
                
                return {
                    'success': True,
                    'message': 'Status da assinatura atualizado para pendente'
                }
            
        except Exception as e:
            print(f"Erro ao processar detalhes da assinatura: {str(e)}")
            
        return {
            'success': True,
            'message': 'Falha no pagamento processada, mas não foi possível atualizar a assinatura'
        }
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        return {
            'success': False,
            'message': f'Erro ao processar falha no pagamento: {str(e)}'
        }

# Função para processar assinatura cancelada
def processar_assinatura_cancelada(event):
    """
    Processa um evento de assinatura cancelada
    
    Args:
        event: Evento do Stripe
        
    Returns:
        dict: Resultado do processamento
    """
    try:
        # Extrair dados da assinatura
        subscription = event['data']['object']
        
        # Obter ID da assinatura e cliente
        subscription_id = subscription.get('id')
        customer_id = subscription.get('customer')
        
        if not subscription_id:
            return {
                'success': False,
                'message': 'ID da assinatura não encontrado'
            }
            
        # Obter cliente
        try:
            customer = stripe.Customer.retrieve(customer_id)
            usuario_email = customer.get('email')
            usuario_nome = customer.get('name', 'Usuário')
        except:
            usuario_email = None
            usuario_nome = 'Usuário'
            
        # Obter metadados da assinatura
        metadata = subscription.get('metadata', {})
        usuario_id = metadata.get('usuario_id')
        
        if not usuario_id:
            # Tentar buscar na lista de assinaturas por subscription_id
            from utils.assinatura_db import obter_assinatura_por_subscription_id
            resultado_busca = obter_assinatura_por_subscription_id(subscription_id)
            
            if resultado_busca.get('sucesso'):
                usuario_id = resultado_busca.get('assinatura', {}).get('usuario_id')
                
                # Se encontramos o usuário, também podemos obter o e-mail
                if not usuario_email:
                    from utils.database import Database
                    db = Database()
                    usuario = db.get_usuario_by_id(usuario_id)
                    if usuario:
                        usuario_email = usuario.get('email')
                        usuario_nome = usuario.get('nome', 'Usuário')
        
        if usuario_id:
            # Cancelar assinatura no banco de dados
            resultado_cancelamento = cancelar_assinatura(usuario_id)
            
            if not resultado_cancelamento.get('sucesso'):
                print(f"Erro ao cancelar assinatura: {resultado_cancelamento.get('mensagem')}")
            
            # Enviar e-mail de notificação
            if usuario_email:
                enviar_notificacao_cancelamento(
                    destinatario=usuario_email,
                    nome=usuario_nome
                )
            
            return {
                'success': True,
                'message': 'Assinatura cancelada com sucesso'
            }
            
        return {
            'success': True,
            'message': 'Assinatura cancelada, mas não foi possível atualizar no banco de dados'
        }
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        return {
            'success': False,
            'message': f'Erro ao processar cancelamento de assinatura: {str(e)}'
        }

# Função para cancelar assinatura no Stripe
def cancelar_assinatura_stripe(subscription_id):
    """
    Cancela uma assinatura no Stripe
    
    Args:
        subscription_id: ID da assinatura
        
    Returns:
        dict: Resultado da operação
    """
    try:
        if not STRIPE_API_KEY:
            return {
                'success': False,
                'message': 'Chave de API do Stripe não configurada'
            }
            
        # Cancelar assinatura
        stripe.Subscription.cancel(subscription_id)
        
        return {
            'success': True,
            'message': 'Assinatura cancelada com sucesso'
        }
        
    except stripe.error.StripeError as e:
        print(f"Erro Stripe: {str(e)}")
        return {
            'success': False,
            'message': f'Erro do Stripe: {str(e)}'
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        return {
            'success': False,
            'message': f'Erro ao cancelar assinatura: {str(e)}'
        }

# Função para mudar o plano de uma assinatura
def mudar_plano_assinatura(subscription_id, price_id):
    """
    Muda o plano de uma assinatura
    
    Args:
        subscription_id: ID da assinatura
        price_id: ID do novo preço
        
    Returns:
        dict: Resultado da operação
    """
    try:
        if not STRIPE_API_KEY:
            return {
                'success': False,
                'message': 'Chave de API do Stripe não configurada'
            }
            
        # Obter assinatura
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        # Obter ID do item
        item_id = None
        
        if subscription.get('items') and subscription['items'].get('data'):
            item_id = subscription['items']['data'][0].get('id')
            
        if not item_id:
            return {
                'success': False,
                'message': 'Item da assinatura não encontrado'
            }
            
        # Atualizar assinatura
        stripe.Subscription.modify(
            subscription_id,
            items=[
                {
                    'id': item_id,
                    'price': price_id,
                }
            ]
        )
        
        return {
            'success': True,
            'message': 'Plano atualizado com sucesso'
        }
        
    except stripe.error.StripeError as e:
        print(f"Erro Stripe: {str(e)}")
        return {
            'success': False,
            'message': f'Erro do Stripe: {str(e)}'
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        return {
            'success': False,
            'message': f'Erro ao mudar plano de assinatura: {str(e)}'
        }

# Função para criar sessão do portal de clientes
def criar_sessao_portal_cliente(customer_id, return_url=None):
    """
    Cria uma sessão do portal de clientes do Stripe
    
    Args:
        customer_id: ID do cliente no Stripe
        return_url: URL de retorno após o uso do portal
        
    Returns:
        str: URL da sessão ou None em caso de erro
    """
    try:
        if not STRIPE_API_KEY:
            print("Chave de API do Stripe não configurada")
            return None
            
        # Configurar URL de retorno padrão
        if not return_url:
            return_url = os.environ.get('APP_URL', 'http://localhost:5000') + '/minha_assinatura'
        
        # Criar sessão do portal
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        
        return session.url
        
    except Exception as e:
        print(f"Erro ao criar sessão do portal: {str(e)}")
        return None