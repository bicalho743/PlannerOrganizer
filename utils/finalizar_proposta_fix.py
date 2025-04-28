"""
Versão corrigida do módulo finalizar_proposta para resolver problemas no Render
"""
import os
import logging
import pandas as pd
import streamlit as st
from decimal import Decimal
from datetime import datetime, date
from utils.database import Database

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validar_valor_numerico(valor):
    """
    Converte e valida um valor para formato numérico
    
    Args:
        valor: Valor para converter (string, int, float)
        
    Returns:
        float: Valor convertido ou 0.0 se inválido
    """
    if pd.isna(valor) or valor is None:
        return 0.0
        
    if isinstance(valor, (int, float, Decimal)):
        return float(valor)
        
    if isinstance(valor, str):
        # Remover caracteres não numéricos exceto ponto e vírgula
        valor_limpo = ''.join(c for c in valor if c.isdigit() or c in '.,')
        # Substituir vírgula por ponto (formato brasileiro)
        valor_limpo = valor_limpo.replace(',', '.')
        
        try:
            return float(valor_limpo) if valor_limpo else 0.0
        except:
            logger.warning(f"Não foi possível converter o valor '{valor}' para número. Usando 0.0.")
            return 0.0
    
    return 0.0

def finalizar_proposta_seguro(proposta_id, usuario_id=None):
    """
    Finaliza uma proposta de forma segura, com validações e conversões de tipo explícitas
    
    Args:
        proposta_id: ID da proposta
        usuario_id: ID do usuário para contexto
        
    Returns:
        dict: Resultado da operação
    """
    try:
        db = Database(usuario_id)
        
        # Log para debug
        logger.info(f"DEBUG FINALIZAR: Iniciando finalização segura da proposta ID={proposta_id}")
        
        # Obter proposta
        proposta = db.get_proposta(proposta_id)
        if not proposta:
            return {
                'status': 'error', 
                'message': f'Proposta ID {proposta_id} não encontrada'
            }
        
        # Verificar se já está finalizada
        if proposta.status == 'Finalizada':
            return {
                'status': 'error', 
                'message': f'Proposta já está finalizada'
            }
        
        # Verificar se existem lançamentos já associados
        lancamentos = db.get_lancamentos_by_proposta(proposta_id)
        logger.info(f"DEBUG FINALIZAR: Existem {len(lancamentos)} lançamentos para a proposta")
        
        # Verificar se já existe lançamento de receita
        lancamento_principal = None
        for l in lancamentos:
            if l.categoria == 'Serviços de Organização' and l.tipo == 'receita_a_receber':
                lancamento_principal = l
                break
        
        # Se não existe lançamento principal, criar
        valor_proposta = validar_valor_numerico(proposta.valor)
        
        if not lancamento_principal:
            # Criar lançamento de receita
            db.add_lancamento(
                descricao=f"Proposta #{proposta.id} - {proposta.cliente_nome}",
                valor=valor_proposta,
                data=datetime.now().date(),
                categoria="Serviços de Organização",
                tipo="receita_a_receber",
                status="Pendente",
                forma_pagamento="",
                proposta_id=proposta.id
            )
        else:
            logger.info(f"DEBUG FINALIZAR: Já existe lançamento de receita_a_receber para a proposta ID={proposta_id}, não criando novo lançamento base")
        
        # Tratar fornecedores
        fornecedores = db.get_proposta_fornecedores(proposta_id)
        logger.info(f"DEBUG FINALIZAR: Encontrados {len(fornecedores)} fornecedores para a proposta ID={proposta_id}")
        
        for fornecedor in fornecedores:
            # Processar comissão de parceiros se percentual > 0
            percentual = validar_valor_numerico(fornecedor.get('percentual', 0))
            
            if percentual > 0:
                logger.info(f"DEBUG FINALIZAR: Criando lançamento de comissão de {percentual}% para fornecedor {fornecedor.get('nome')}")
                
                valor_comissao = (percentual / 100) * valor_proposta
                
                db.add_lancamento(
                    descricao=f"Comissão {fornecedor.get('nome')} - Proposta #{proposta.id}",
                    valor=valor_comissao,
                    data=datetime.now().date(),
                    categoria="Comissões",
                    tipo="despesa_a_pagar",
                    status="Pendente",
                    forma_pagamento="",
                    proposta_id=proposta.id
                )
        
        # Tratar acréscimos (outros custos)
        acrescimos = db.get_proposta_acrescimos(proposta_id)
        logger.info(f"DEBUG FINALIZAR: Encontrados {len([a for a in acrescimos if a.get('tipo') == 'OUTRO'])} acréscimos do tipo OUTRO para a proposta ID={proposta_id}")
        
        for acrescimo in acrescimos:
            tipo_acrescimo = acrescimo.get('tipo', '')
            
            # Ignorar acréscimos já tratados (produtos, fornecedores)
            if tipo_acrescimo in ['PRODUTO', 'FORNECEDOR']:
                continue
                
            valor_acrescimo = validar_valor_numerico(acrescimo.get('valor', 0))
            
            if valor_acrescimo > 0:
                logger.info(f"DEBUG FINALIZAR: Criando lançamento para acréscimo {tipo_acrescimo}: {acrescimo.get('descricao')} - R$ {valor_acrescimo}")
                
                db.add_lancamento(
                    descricao=f"Acréscimo de {tipo_acrescimo} - Proposta #{proposta.id}",
                    valor=valor_acrescimo,
                    data=datetime.now().date(),
                    categoria="Custos de Projetos",
                    tipo="despesa_a_pagar",
                    status="Pendente",
                    forma_pagamento="",
                    proposta_id=proposta.id
                )
        
        # Tratar assistentes
        assistentes = db.get_proposta_assistentes(proposta_id)
        logger.info(f"DEBUG FINALIZAR: Encontrados {len(assistentes)} assistentes para a proposta ID={proposta_id}")
        
        for assistente in assistentes:
            valor_assistente = validar_valor_numerico(assistente.get('valor', 0))
            
            if valor_assistente > 0:
                logger.info(f"DEBUG FINALIZAR: Criando lançamento para assistente: {assistente.get('descricao')} - R$ {valor_assistente}")
                
                db.add_lancamento(
                    descricao=f"Serviço de {assistente.get('descricao')} - Proposta #{proposta.id}",
                    valor=valor_assistente,
                    data=datetime.now().date(),
                    categoria="Assistentes",
                    tipo="despesa_a_pagar",
                    status="Pendente",
                    forma_pagamento="",
                    proposta_id=proposta.id
                )
        
        # Tratar produtos
        produtos_total = 0
        produtos = db.get_proposta_produtos(proposta_id)
        
        for produto in produtos:
            quantidade = validar_valor_numerico(produto.get('quantidade', 0))
            valor_unitario = validar_valor_numerico(produto.get('valor_unitario', 0))
            
            produtos_total += quantidade * valor_unitario
        
        if produtos_total > 0:
            logger.info(f"DEBUG FINALIZAR: Criando novo lançamento para produtos da proposta ID={proposta_id}")
            
            db.add_lancamento(
                descricao=f"Produtos para proposta #{proposta.id}",
                valor=produtos_total,
                data=datetime.now().date(),
                categoria="Produtos",
                tipo="despesa_a_pagar",
                status="Pendente",
                forma_pagamento="",
                proposta_id=proposta.id
            )
        
        # Atualizar status da proposta
        db.update_proposta_status(proposta_id, 'Finalizada')
        
        logger.info(f"DEBUG FINALIZAR: Proposta #{proposta_id} finalizada com sucesso")
        
        return {
            'status': 'success',
            'message': 'Proposta finalizada com sucesso! Lançamentos financeiros gerados.',
            'proposta_id': proposta_id
        }
    
    except Exception as e:
        logger.error(f"ERRO ao finalizar proposta: {str(e)}")
        return {
            'status': 'error',
            'message': f'Erro ao finalizar proposta: {str(e)}'
        }