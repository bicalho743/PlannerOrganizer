"""
Script para testar a função de reabertura de propostas com as correções realizadas.
Vai testar se apenas o lançamento original da proposta é mantido após a reabertura.
"""
import os
import sys
import pandas as pd
from reabrir_proposta import reabrir_proposta_finalizada
from utils.database import Database
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Adicionar diretório raiz ao path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)

def obter_lancamentos(db, proposta_id):
    """Recupera os lançamentos financeiros da proposta especificada"""
    try:
        query = f"""
        SELECT id, proposta_id, descricao, tipo, valor, categoria, subcategoria, data
        FROM financeiro
        WHERE proposta_id = {proposta_id}
        ORDER BY id
        """
        result = db.execute_query(query)
        if result and not result.empty:
            return result
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Erro ao obter lançamentos: {e}")
        return pd.DataFrame()

def main():
    print("\n=== TESTE DE REABERTURA DE PROPOSTAS ===\n")
    
    # Proposta a testar
    proposta_id = 62
    
    # Inicializar banco de dados
    db = Database()
    
    # Verificar status atual da proposta
    query = f"SELECT id, numero, status, status_execucao FROM propostas WHERE id = {proposta_id}"
    proposta = db.execute_query(query)
    
    if proposta.empty:
        print(f"Proposta {proposta_id} não encontrada!")
        return
    
    print(f"Status inicial da proposta #{proposta_id}:")
    print(f"Status: {proposta.iloc[0]['status']}")
    print(f"Status Execução: {proposta.iloc[0]['status_execucao']}")
    print("\n")
    
    # Mostrar lançamentos antes da reabertura
    print("Lançamentos antes da reabertura:")
    lancamentos_antes = obter_lancamentos(db, proposta_id)
    if not lancamentos_antes.empty:
        print(f"Total de lançamentos: {len(lancamentos_antes)}")
        print(lancamentos_antes[['id', 'descricao', 'tipo', 'valor', 'categoria', 'subcategoria']].to_string())
    else:
        print("Nenhum lançamento encontrado para esta proposta.")
    
    print("\n" + "="*50 + "\n")
    
    # Executar a reabertura
    print(f"Reabrindo proposta #{proposta_id}...")
    resultado = reabrir_proposta_finalizada(proposta_id)
    
    # Mostrar resultado da operação
    status = resultado.get('status', 'erro')
    print(f"Resultado: {status}")
    print(f"Mensagem: {resultado.get('mensagem', 'N/A')}")
    
    if 'alerta' in resultado:
        print(f"Alerta: {resultado['alerta']}")
    
    if 'lancamentos_encontrados' in resultado:
        print(f"Lançamentos encontrados: {resultado['lancamentos_encontrados']}")
        print(f"Lançamentos excluídos: {resultado.get('lancamentos_excluidos', 0)}")
    
    print("\n" + "="*50 + "\n")
    
    # Verificar status da proposta após reabertura
    query = f"SELECT id, numero, status, status_execucao FROM propostas WHERE id = {proposta_id}"
    proposta_apos = db.execute_query(query)
    
    if not proposta_apos.empty:
        print(f"Status da proposta #{proposta_id} após reabertura:")
        print(f"Status: {proposta_apos.iloc[0]['status']}")
        print(f"Status Execução: {proposta_apos.iloc[0]['status_execucao']}")
    
    # Mostrar lançamentos após a reabertura
    print("\nLançamentos após a reabertura:")
    lancamentos_depois = obter_lancamentos(db, proposta_id)
    if not lancamentos_depois.empty:
        print(f"Total de lançamentos restantes: {len(lancamentos_depois)}")
        print(lancamentos_depois[['id', 'descricao', 'tipo', 'valor', 'categoria', 'subcategoria']].to_string())
    else:
        print("Todos os lançamentos foram removidos da proposta.")

if __name__ == "__main__":
    main()