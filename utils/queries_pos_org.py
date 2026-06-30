"""
Queries para módulo Pós-Organização
Funções para gerenciar pós-organização, ações e templates
"""
import pandas as pd
from datetime import datetime, timedelta
from utils.models import PostOrganization, PostOrganizationAction, PostOrgTemplate, Cliente, Proposta


def create_post_organization(session, usuario_id, proposta_id, cliente_id, data_final_projeto):
    """
    Cria um registro de pós-organização e as ações automáticas padrão.
    Chamado automaticamente quando uma proposta é finalizada.
    
    Args:
        session: Sessão do banco de dados
        usuario_id: ID do usuário
        proposta_id: ID da proposta finalizada
        cliente_id: ID do cliente
        data_final_projeto: Data de finalização do projeto
        
    Returns:
        int: ID do registro criado ou None se erro
    """
    try:
        # Verificar se já existe pós-organização para esta proposta
        existing = session.query(PostOrganization).filter(
            PostOrganization.proposta_id == proposta_id,
            PostOrganization.usuario_id == usuario_id
        ).first()
        
        if existing:
            print(f"Pós-organização já existe para proposta {proposta_id}")
            return existing.id
        
        # Criar registro principal
        post_org = PostOrganization(
            proposta_id=proposta_id,
            cliente_id=cliente_id,
            data_final_projeto=data_final_projeto,
            status='ATIVO',
            usuario_id=usuario_id
        )
        session.add(post_org)
        session.flush()
        
        # Buscar templates do banco para criar as ações
        templates = session.query(PostOrgTemplate).order_by(PostOrgTemplate.dias_apos).all()
        if templates:
            acoes_padrao = [(t.etapa, data_final_projeto + timedelta(days=t.dias_apos)) for t in templates]
        else:
            # Fallback com as etapas padrão caso a tabela não exista
            acoes_padrao = [
                ('agradecimento',  data_final_projeto + timedelta(days=1)),
                ('acompanhamento', data_final_projeto + timedelta(days=7)),
                ('ajuste_fino',    data_final_projeto + timedelta(days=30)),
                ('feedback',       data_final_projeto + timedelta(days=45)),
                ('continuidade',   data_final_projeto + timedelta(days=60)),
            ]

        for action_type, due_date in acoes_padrao:
            action = PostOrganizationAction(
                post_organization_id=post_org.id,
                action_type=action_type,
                due_date=due_date,
                status='PENDENTE',
                usuario_id=usuario_id
            )
            session.add(action)
        
        session.commit()
        print(f"Pós-organização criada com sucesso para proposta {proposta_id}")
        return post_org.id
        
    except Exception as e:
        session.rollback()
        print(f"Erro ao criar pós-organização: {str(e)}")
        raise e


def get_post_organizations(session, usuario_id, status_filter=None):
    """
    Retorna lista de pós-organizações do usuário.
    
    Args:
        session: Sessão do banco de dados
        usuario_id: ID do usuário
        status_filter: Filtrar por status ('ATIVO', 'CONCLUIDO') ou None para todos
        
    Returns:
        DataFrame com dados das pós-organizações
    """
    try:
        q = session.query(PostOrganization).filter(
            PostOrganization.usuario_id == usuario_id
        )
        
        if status_filter:
            q = q.filter(PostOrganization.status == status_filter)
        
        post_orgs = q.order_by(PostOrganization.created_at.desc()).all()
        
        df_data = []
        for po in post_orgs:
            # Buscar próxima ação pendente
            proxima_acao = session.query(PostOrganizationAction).filter(
                PostOrganizationAction.post_organization_id == po.id,
                PostOrganizationAction.status == 'PENDENTE'
            ).order_by(PostOrganizationAction.due_date).first()
            
            # Buscar nome do cliente
            cliente = session.query(Cliente).filter(Cliente.id == po.cliente_id).first()
            cliente_nome = cliente.nome if cliente else 'N/A'
            
            # Buscar número da proposta
            proposta = session.query(Proposta).filter(Proposta.id == po.proposta_id).first()
            proposta_numero = proposta.numero if proposta else 'N/A'
            
            df_data.append({
                'id': po.id,
                'proposta_id': po.proposta_id,
                'proposta_numero': proposta_numero,
                'cliente_id': po.cliente_id,
                'cliente_nome': cliente_nome,
                'cliente_telefone': cliente.telefone if cliente else None,
                'data_final_projeto': po.data_final_projeto,
                'status': po.status,
                'created_at': po.created_at,
                'proxima_acao': proxima_acao.action_type if proxima_acao else None,
                'proxima_acao_data': proxima_acao.due_date if proxima_acao else None
            })
        
        return pd.DataFrame(df_data)
        
    except Exception as e:
        print(f"Erro ao buscar pós-organizações: {str(e)}")
        return pd.DataFrame()


def get_post_organization_actions(session, post_organization_id):
    """
    Retorna todas as ações de uma pós-organização.
    
    Args:
        session: Sessão do banco de dados
        post_organization_id: ID da pós-organização
        
    Returns:
        DataFrame com as ações
    """
    try:
        actions = session.query(PostOrganizationAction).filter(
            PostOrganizationAction.post_organization_id == post_organization_id
        ).order_by(PostOrganizationAction.due_date).all()
        
        df_data = []
        for a in actions:
            df_data.append({
                'id': a.id,
                'post_organization_id': a.post_organization_id,
                'action_type': a.action_type,
                'due_date': a.due_date,
                'status': a.status,
                'notes': a.notes,
                'completed_at': a.completed_at,
                'ordem': a.ordem
            })
        
        return pd.DataFrame(df_data)
        
    except Exception as e:
        print(f"Erro ao buscar ações: {str(e)}")
        return pd.DataFrame()


def update_post_organization_action(session, action_id, status, notes=None, due_date=None):
    """
    Atualiza uma ação de pós-organização.
    
    Args:
        session: Sessão do banco de dados
        action_id: ID da ação
        status: Novo status ('PENDENTE', 'FEITO', 'CANCELADO')
        notes: Observações (opcional)
        due_date: Data de vencimento (opcional)
        
    Returns:
        dict com informações da ação atualizada ou None se erro
    """
    try:
        action = session.query(PostOrganizationAction).filter(
            PostOrganizationAction.id == action_id
        ).first()
        
        if not action:
            return None
        
        action.status = status
        if notes is not None:
            action.notes = notes
        if due_date is not None:
            action.due_date = due_date
        
        if status == 'FEITO':
            action.completed_at = datetime.now()
        
        session.commit()
        
        # Verificar conclusão automática
        _check_post_organization_completion(session, action.post_organization_id)
        
        return {
            'id': action.id,
            'action_type': action.action_type,
            'status': action.status,
            'post_organization_id': action.post_organization_id
        }
        
    except Exception as e:
        session.rollback()
        print(f"Erro ao atualizar ação: {str(e)}")
        raise e


def _check_post_organization_completion(session, post_organization_id):
    """
    Verifica se todas as ações obrigatórias estão concluídas e marca a pós-organização como CONCLUIDO.
    Ações obrigatórias: agradecimento, acompanhamento, ajuste_fino, feedback, continuidade
    """
    try:
        acoes_obrigatorias = ['agradecimento', 'acompanhamento', 'ajuste_fino', 'feedback', 'continuidade']

        acoes = session.query(PostOrganizationAction).filter(
            PostOrganizationAction.post_organization_id == post_organization_id,
            PostOrganizationAction.action_type.in_(acoes_obrigatorias)
        ).all()

        todas_feitas = all(a.status == 'FEITO' for a in acoes)

        if todas_feitas and len(acoes) > 0:
            post_org = session.query(PostOrganization).filter(
                PostOrganization.id == post_organization_id
            ).first()

            if post_org:
                post_org.status = 'CONCLUIDO'
                session.commit()
                print(f"Pós-organização {post_organization_id} marcada como CONCLUIDA")

    except Exception as e:
        print(f"Erro ao verificar conclusão: {str(e)}")


def add_retorno_tecnico_action(session, usuario_id, post_organization_id, due_date):
    """
    Adiciona uma ação de RETORNO_TECNICO manualmente.
    Chamado quando o usuário marca FOLLOW_UP como FEITO e indica necessidade de retorno.
    
    Args:
        session: Sessão do banco de dados
        usuario_id: ID do usuário
        post_organization_id: ID da pós-organização
        due_date: Data prevista para o retorno (entre 15 e 30 dias)
        
    Returns:
        int: ID da ação criada ou None se erro
    """
    try:
        action = PostOrganizationAction(
            post_organization_id=post_organization_id,
            action_type='retorno_tecnico',
            due_date=due_date,
            status='PENDENTE',
            usuario_id=usuario_id
        )
        session.add(action)
        session.commit()
        
        return action.id
        
    except Exception as e:
        session.rollback()
        print(f"Erro ao criar retorno técnico: {str(e)}")
        raise e


def get_pending_post_actions_for_dashboard(session, usuario_id):
    """
    Retorna ações pendentes para exibição no Dashboard.
    Filtro: status=PENDENTE, ações de acompanhamento (Agradecimento, Manutenção, Follow-up)
    Mostra ações vencidas e próximas (até 3 dias)
    
    Args:
        session: Sessão do banco de dados
        usuario_id: ID do usuário
    
    Returns:
        DataFrame com ações pendentes para alerta
    """
    try:
        hoje = datetime.now().date()
        limite = hoje + timedelta(days=3)
        
        actions = session.query(PostOrganizationAction).join(
            PostOrganization
        ).filter(
            PostOrganization.usuario_id == usuario_id,
            PostOrganizationAction.status == 'PENDENTE',
            PostOrganizationAction.due_date <= limite,
            PostOrganizationAction.action_type.in_(['agradecimento', 'acompanhamento', 'ajuste_fino', 'feedback', 'continuidade', 'retorno_tecnico'])
        ).order_by(PostOrganizationAction.due_date).all()
        
        df_data = []
        for a in actions:
            post_org = session.query(PostOrganization).filter(
                PostOrganization.id == a.post_organization_id
            ).first()
            
            cliente = session.query(Cliente).filter(
                Cliente.id == post_org.cliente_id
            ).first() if post_org else None
            
            proposta = session.query(Proposta).filter(
                Proposta.id == post_org.proposta_id
            ).first() if post_org else None
            
            df_data.append({
                'action_id': a.id,
                'action_type': a.action_type,
                'due_date': a.due_date,
                'cliente_nome': cliente.nome if cliente else 'N/A',
                'cliente_telefone': cliente.telefone if cliente else None,
                'proposta_numero': proposta.numero if proposta else 'N/A',
                'post_organization_id': a.post_organization_id
            })
        
        return pd.DataFrame(df_data)
        
    except Exception as e:
        print(f"Erro ao buscar ações pendentes: {str(e)}")
        return pd.DataFrame()


def get_post_org_templates(session):
    """
    Retorna todos os templates de mensagem de pós-organização.
    
    Args:
        session: Sessão do banco de dados

    Returns:
        dict: {etapa: {nome, dias_apos, emoji, texto, gratuito, hint}} ou {} se erro
    """
    try:
        templates = session.query(PostOrgTemplate).order_by(PostOrgTemplate.dias_apos).all()
        result = {}
        for t in templates:
            result[t.etapa] = {
                'nome': t.nome,
                'dias_apos': t.dias_apos,
                'emoji': t.emoji or '',
                'texto': t.texto,
                'gratuito': t.gratuito,
                'hint': t.hint
            }
        return result
    except Exception as e:
        print(f"Erro ao buscar templates: {str(e)}")
        return {}
