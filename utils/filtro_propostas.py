import pandas as pd

def load_propostas(db, status=None, status_execucao=None):
    """
    Carrega propostas com filtro opcional por status e/ou status_execucao.
    
    Args:
        db: Instância do banco de dados
        status: Status da proposta para filtrar
        status_execucao: Status de execução para filtrar
        
    Returns:
        DataFrame: Propostas filtradas
    """
    # Obter todas as propostas do banco de dados
    propostas = db.get_propostas()
    
    if propostas.empty:
        return propostas
    
    # Aplicar filtro de status, se fornecido
    if status:
        propostas = propostas[propostas['status'] == status]
    
    # Aplicar filtro de status_execucao, se fornecido
    if status_execucao:
        propostas = propostas[propostas['status_execucao'] == status_execucao]
    
    return propostas

def get_propostas_finalizadas(db):
    """
    Carrega apenas propostas que foram realmente finalizadas
    Usa uma abordagem de filtro mais restritiva, exigindo que status e status_execucao
    sejam "Finalizada", ou que o status seja "Recusada"
    
    Args:
        db: Instância do banco de dados
        
    Returns:
        DataFrame: Propostas finalizadas ou recusadas
    """
    # Obter todas as propostas do banco de dados
    propostas = db.get_propostas()
    
    if propostas.empty:
        return propostas
    
    # Filtrar propostas finalizadas (status canônico) ou recusadas
    from utils.proposta_status import STATUS_FINALIZADA, STATUS_RECUSADA
    propostas_finalizadas = propostas[
        ((propostas['status'] == STATUS_FINALIZADA) & (propostas['status_execucao'] == 'Finalizada')) |
        (propostas['status'] == STATUS_RECUSADA)
    ]
    
    return propostas_finalizadas