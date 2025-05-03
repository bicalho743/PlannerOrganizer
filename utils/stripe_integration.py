"""
Módulo de integração com Stripe para processamento de pagamentos
Este módulo fornece funcionalidades para:
1. Configurar clientes no Stripe
2. Criar e gerenciar assinaturas
3. Processar webhooks do Stripe
4. Atualizar status de planos no banco de dados
"""
import os
import stripe
import logging
import jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .database import Perfil

# Configurar logger
logger = logging.getLogger(__name__)

# Obter API Key do ambiente
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
STRIPE_PRICE_ID_MENSAL = os.environ.get('STRIPE_PRICE_ID_MENSAL')
STRIPE_PRICE_ID_ANUAL = os.environ.get('STRIPE_PRICE_ID_ANUAL')

# Definir os planos disponíveis
PLANOS = {
    'gratuito': {
        'nome': 'Gratuito',
        'descricao': 'Plano gratuito com recursos básicos',
        'limite_clientes': 10,
        'limite_propostas': 5,
        'preco_mensal': 0,
    },
    'profissional': {
        'nome': 'Profissional',
        'descricao': 'Plano completo para profissionais',
        'limite_clientes': 100,
        'limite_propostas': 50,
        'preco_mensal': 49.90,
        'stripe_price_id_mensal': STRIPE_PRICE_ID_MENSAL,
        'stripe_price_id_anual': STRIPE_PRICE_ID_ANUAL,
    }
}

def inicializar_stripe():
    """
    Inicializa a API do Stripe com a chave fornecida no ambiente
    """
    if not STRIPE_API_KEY:
        logger.warning("STRIPE_API_KEY não está definida no ambiente. Pagamentos não funcionarão.")
        return False
    
    stripe.api_key = STRIPE_API_KEY
    return True

def obter_ou_criar_cliente(perfil, session):
    """
    Obtém ou cria um cliente no Stripe e atualiza o perfil com o ID do cliente
    
    Args:
        perfil: Objeto Perfil do usuário
        session: Sessão do SQLAlchemy
        
    Returns:
        dict: Objeto do cliente no Stripe
    """
    # Verificar se o perfil já tem um cliente_stripe_id
    if hasattr(perfil, 'cliente_stripe_id') and perfil.cliente_stripe_id:
        try:
            # Tentar obter o cliente existente
            cliente = stripe.Customer.retrieve(perfil.cliente_stripe_id)
            return cliente
        except stripe.error.InvalidRequestError:
            # Cliente não existe mais no Stripe, criar um novo
            logger.warning(f"Cliente {perfil.cliente_stripe_id} não encontrado no Stripe. Criando novo.")
            pass
    
    # Criar um novo cliente no Stripe
    try:
        cliente = stripe.Customer.create(
            email=perfil.email,
            name=perfil.nome,
            metadata={
                'usuario_id': perfil.usuario_id,
                'plano': perfil.plano
            }
        )
        
        # Atualizar o perfil com o ID do cliente Stripe
        if not hasattr(perfil, 'cliente_stripe_id'):
            # Verificar se precisamos adicionar a coluna ao modelo
            logger.warning("A coluna cliente_stripe_id não existe no modelo Perfil. A integração completa com o Stripe requer uma migração de banco.")
        else:
            perfil.cliente_stripe_id = cliente.id
            session.commit()
        
        return cliente
    except Exception as e:
        logger.error(f"Erro ao criar cliente no Stripe: {e}")
        raise

def criar_sessao_checkout(perfil, plano, tipo_assinatura='mensal', session=None):
    """
    Cria uma sessão de checkout para assinatura no Stripe
    
    Args:
        perfil: Objeto Perfil do usuário
        plano: Identificador do plano ('profissional', etc)
        tipo_assinatura: 'mensal' ou 'anual'
        session: Sessão do SQLAlchemy
        
    Returns:
        str: URL da sessão de checkout
    """
    if plano not in PLANOS or plano == 'gratuito':
        logger.error(f"Plano inválido: {plano}")
        raise ValueError(f"Plano inválido: {plano}")
    
    # Obter as configurações do plano
    config_plano = PLANOS[plano]
    price_id = config_plano.get(f'stripe_price_id_{tipo_assinatura}')
    
    if not price_id:
        logger.error(f"ID de preço não configurado para plano {plano} ({tipo_assinatura})")
        raise ValueError(f"ID de preço não configurado para plano {plano}")
    
    # Obter ou criar cliente no Stripe
    cliente = obter_ou_criar_cliente(perfil, session)
    
    # URL de retorno após o checkout
    success_url = os.environ.get('APP_URL', 'https://www.plannerorganiza.com.br') + '/assinatura-confirmada'
    cancel_url = os.environ.get('APP_URL', 'https://www.plannerorganiza.com.br') + '/planos'
    
    # Criar a sessão de checkout
    try:
        checkout_session = stripe.checkout.Session.create(
            customer=cliente.id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return checkout_session.url
    except Exception as e:
        logger.error(f"Erro ao criar sessão de checkout: {e}")
        raise

def processar_webhook(payload, sig_header, session):
    """
    Processa webhooks enviados pelo Stripe
    
    Args:
        payload: Dados do evento em raw bytes
        sig_header: Cabeçalho de assinatura do Stripe
        session: Sessão do SQLAlchemy
        
    Returns:
        bool: True se processado com sucesso
    """
    try:
        evento = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Payload inválido
        logger.error(f"Erro de validação de webhook: {e}")
        return False
    except stripe.error.SignatureVerificationError as e:
        # Assinatura inválida
        logger.error(f"Erro de verificação de assinatura: {e}")
        return False
    
    # Processar o evento
    event_type = evento['type']
    logger.info(f"Webhook do Stripe recebido: {event_type}")
    
    if event_type == 'checkout.session.completed':
        # Processar checkout completado
        return processar_checkout_completado(evento, session)
        
    elif event_type == 'invoice.paid':
        # Processar fatura paga (renovação de assinatura)
        return processar_fatura_paga(evento, session)
        
    elif event_type == 'customer.subscription.deleted':
        # Processar cancelamento de assinatura
        return processar_assinatura_cancelada(evento, session)
    
    # Outros tipos de eventos não são processados
    return True

def processar_checkout_completado(evento, session):
    """
    Processa um evento de checkout completado
    
    Args:
        evento: Objeto do evento do Stripe
        session: Sessão do SQLAlchemy
        
    Returns:
        bool: True se processado com sucesso
    """
    try:
        # Obter dados da sessão de checkout
        checkout_session = evento['data']['object']
        
        # Obter o ID do cliente
        cliente_id = checkout_session.get('customer')
        if not cliente_id:
            logger.error("ID de cliente não encontrado no evento de checkout")
            return False
        
        # Buscar o perfil associado ao cliente
        perfil = session.query(Perfil).filter_by(cliente_stripe_id=cliente_id).first()
        if not perfil:
            logger.error(f"Perfil não encontrado para cliente Stripe {cliente_id}")
            return False
        
        # Atualizar o plano do perfil para 'profissional'
        perfil.plano = 'profissional'
        
        # Adicionar data de início e expiração da assinatura (se tiver a coluna)
        if hasattr(perfil, 'assinatura_inicio'):
            perfil.assinatura_inicio = datetime.now()
        
        if hasattr(perfil, 'assinatura_expiracao'):
            # Definir para 1 ano no futuro como padrão, será ajustado ao receber evento de fatura
            perfil.assinatura_expiracao = datetime.now() + timedelta(days=365)
        
        session.commit()
        logger.info(f"Assinatura ativada para usuário {perfil.usuario_id}")
        return True
    
    except Exception as e:
        logger.error(f"Erro ao processar checkout completado: {e}")
        session.rollback()
        return False

def processar_fatura_paga(evento, session):
    """
    Processa um evento de fatura paga (renovação de assinatura)
    
    Args:
        evento: Objeto do evento do Stripe
        session: Sessão do SQLAlchemy
        
    Returns:
        bool: True se processado com sucesso
    """
    try:
        # Obter dados da fatura
        fatura = evento['data']['object']
        
        # Obter o ID do cliente
        cliente_id = fatura.get('customer')
        if not cliente_id:
            logger.error("ID de cliente não encontrado no evento de fatura")
            return False
        
        # Buscar o perfil associado ao cliente
        perfil = session.query(Perfil).filter_by(cliente_stripe_id=cliente_id).first()
        if not perfil:
            logger.error(f"Perfil não encontrado para cliente Stripe {cliente_id}")
            return False
        
        # Obter dados da assinatura para determinar o período
        if fatura.get('subscription'):
            try:
                assinatura = stripe.Subscription.retrieve(fatura.get('subscription'))
                periodo_fim = datetime.fromtimestamp(assinatura.current_period_end)
                
                # Atualizar a data de expiração se o modelo tiver o campo
                if hasattr(perfil, 'assinatura_expiracao'):
                    perfil.assinatura_expiracao = periodo_fim
                    session.commit()
                    logger.info(f"Data de expiração atualizada para {periodo_fim} para usuário {perfil.usuario_id}")
            except Exception as e:
                logger.error(f"Erro ao obter detalhes da assinatura: {e}")
        
        return True
    
    except Exception as e:
        logger.error(f"Erro ao processar fatura paga: {e}")
        session.rollback()
        return False

def processar_assinatura_cancelada(evento, session):
    """
    Processa um evento de assinatura cancelada
    
    Args:
        evento: Objeto do evento do Stripe
        session: Sessão do SQLAlchemy
        
    Returns:
        bool: True se processado com sucesso
    """
    try:
        # Obter dados da assinatura
        assinatura = evento['data']['object']
        
        # Obter o ID do cliente
        cliente_id = assinatura.get('customer')
        if not cliente_id:
            logger.error("ID de cliente não encontrado no evento de assinatura")
            return False
        
        # Buscar o perfil associado ao cliente
        perfil = session.query(Perfil).filter_by(cliente_stripe_id=cliente_id).first()
        if not perfil:
            logger.error(f"Perfil não encontrado para cliente Stripe {cliente_id}")
            return False
        
        # Verificar se a assinatura foi realmente cancelada
        if assinatura.get('status') == 'canceled':
            # Atualizar o plano do perfil para 'gratuito'
            perfil.plano = 'gratuito'
            
            # Limpar datas de assinatura se o modelo tiver os campos
            if hasattr(perfil, 'assinatura_expiracao'):
                perfil.assinatura_expiracao = None
            
            session.commit()
            logger.info(f"Plano alterado para gratuito para usuário {perfil.usuario_id} após cancelamento de assinatura")
        
        return True
    
    except Exception as e:
        logger.error(f"Erro ao processar assinatura cancelada: {e}")
        session.rollback()
        return False

def verificar_assinatura_ativa(perfil):
    """
    Verifica se o usuário tem uma assinatura ativa
    
    Args:
        perfil: Objeto Perfil do usuário
        
    Returns:
        bool: True se o usuário tiver uma assinatura ativa
    """
    # Verificar se o usuário está no plano gratuito
    if perfil.plano == 'gratuito':
        return False
    
    # Verificar se o modelo tem o campo de expiração
    if hasattr(perfil, 'assinatura_expiracao') and perfil.assinatura_expiracao:
        # Verificar se a assinatura expirou
        return perfil.assinatura_expiracao > datetime.now()
    
    # Se não tem o campo de expiração, confiar apenas no campo de plano
    return perfil.plano != 'gratuito'

def gerar_portal_cliente(perfil):
    """
    Gera um link para o portal do cliente no Stripe
    
    Args:
        perfil: Objeto Perfil do usuário
        
    Returns:
        str: URL do portal do cliente
    """
    if not hasattr(perfil, 'cliente_stripe_id') or not perfil.cliente_stripe_id:
        logger.error(f"Usuário {perfil.usuario_id} não tem um cliente Stripe associado")
        raise ValueError("Usuário não tem um cliente Stripe associado")
    
    try:
        # Criar a sessão do portal
        session = stripe.billing_portal.Session.create(
            customer=perfil.cliente_stripe_id,
            return_url=os.environ.get('APP_URL', 'https://www.plannerorganiza.com.br') + '/dashboard',
        )
        return session.url
    except Exception as e:
        logger.error(f"Erro ao criar sessão do portal: {e}")
        raise

def obter_limites_plano(perfil):
    """
    Obtém os limites do plano atual do usuário
    
    Args:
        perfil: Objeto Perfil do usuário
        
    Returns:
        dict: Dicionário com os limites do plano
    """
    plano_id = perfil.plano
    if plano_id not in PLANOS:
        logger.warning(f"Plano {plano_id} não encontrado, usando gratuito como padrão")
        plano_id = 'gratuito'
    
    return PLANOS[plano_id]

def verificar_dentro_limites(perfil, tipo, session):
    """
    Verifica se o usuário está dentro dos limites do plano
    
    Args:
        perfil: Objeto Perfil do usuário
        tipo: Tipo de limite a verificar ('clientes' ou 'propostas')
        session: Sessão do SQLAlchemy
        
    Returns:
        bool: True se o usuário estiver dentro dos limites
    """
    from .database import Cliente, Proposta
    
    # Obter limites do plano
    limites = obter_limites_plano(perfil)
    
    # Verificar o tipo de limite
    if tipo == 'clientes':
        # Contar clientes do usuário
        count = session.query(Cliente).filter_by(usuario_id=perfil.usuario_id).count()
        return count < limites.get('limite_clientes', 10)
    
    elif tipo == 'propostas':
        # Contar propostas do usuário
        count = session.query(Proposta).filter_by(usuario_id=perfil.usuario_id).count()
        return count < limites.get('limite_propostas', 5)
    
    else:
        logger.error(f"Tipo de limite desconhecido: {tipo}")
        return False