"""
Módulo para finalização de propostas com correção de bugs
"""
import streamlit as st
from datetime import datetime
import pandas as pd

def finalizar_proposta_segura(proposta_id, gerar_financeiro=True):
    """
    Alias para finalizar_proposta_corrigido para compatibilidade
    """
    return finalizar_proposta_corrigido(proposta_id, gerar_financeiro)

def finalizar_proposta_sql(proposta_id, gerar_financeiro=True):
    """
    Alias para finalizar_proposta_corrigido usando SQL direto
    """
    return finalizar_proposta_corrigido(proposta_id, gerar_financeiro)

def finalizar_proposta_corrigido(proposta_id, gerar_financeiro=True):
    """
    Finaliza uma proposta com correção de bugs
    
    Args:
        proposta_id: ID da proposta a ser finalizada
        gerar_financeiro: Se deve gerar lançamento financeiro
        
    Returns:
        dict: Resultado da operação
    """
    try:
        if 'db' not in st.session_state:
            return {'success': False, 'error': 'Database não inicializado'}
            
        db = st.session_state.db
        
        # Buscar a proposta
        propostas = db.get_propostas()
        if propostas.empty:
            return {'success': False, 'error': 'Nenhuma proposta encontrada'}
            
        proposta = propostas[propostas['id'] == proposta_id]
        if proposta.empty:
            return {'success': False, 'error': 'Proposta não encontrada'}
            
        proposta_data = proposta.iloc[0]
        
        # Atualizar status da proposta
        try:
            db.update_proposta(
                proposta_id,
                status='Finalizada',
                status_execucao='Finalizada',
                data_fim=datetime.now()
            )
            
            # Gerar lançamento financeiro se solicitado
            if gerar_financeiro and proposta_data['valor'] > 0:
                db.add_financeiro(
                    tipo='Receita',
                    descricao=f'Receita da proposta #{proposta_data["numero"]} - {proposta_data["cliente_nome"]}',
                    valor=proposta_data['valor'],
                    data=datetime.now(),
                    categoria='Serviços',
                    proposta_id=proposta_id
                )
            
            return {
                'success': True, 
                'message': 'Proposta finalizada com sucesso',
                'financeiro_gerado': gerar_financeiro
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erro ao finalizar proposta: {str(e)}'}
            
    except Exception as e:
        return {'success': False, 'error': f'Erro geral: {str(e)}'}

def reabrir_proposta(proposta_id):
    """
    Reabre uma proposta finalizada
    
    Args:
        proposta_id: ID da proposta a ser reaberta
        
    Returns:
        dict: Resultado da operação
    """
    try:
        if 'db' not in st.session_state:
            return {'success': False, 'error': 'Database não inicializado'}
            
        db = st.session_state.db
        
        # Atualizar status da proposta
        db.update_proposta(
            proposta_id,
            status='Em execução',
            status_execucao='Em execução',
            data_fim=None
        )
        
        return {'success': True, 'message': 'Proposta reaberta com sucesso'}
        
    except Exception as e:
        return {'success': False, 'error': f'Erro ao reabrir proposta: {str(e)}'}