import streamlit as st
import pandas as pd
import os
import sys

# Adicionar o diretório raiz ao path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)

from utils.database import Database
from utils.filtro_propostas import get_propostas_finalizadas, load_propostas

# Iniciar o banco de dados
db = Database()

# Obter todas as propostas
print("Obtendo todas as propostas...")
propostas = db.get_propostas()
print(f"Total de propostas: {len(propostas)}")
print("Colunas disponíveis:")
print(propostas.columns.tolist())
print("\nAmostra de propostas:")
print(propostas[['id', 'cliente_nome', 'descricao', 'valor', 'status', 'status_execucao']].head())

# Testar a função load_propostas
print("\nTestando filtro com status='Finalizada'...")
propostas_status_finalizada = load_propostas(db, status="Finalizada")
print(f"Propostas com status='Finalizada': {len(propostas_status_finalizada)}")
print(propostas_status_finalizada[['id', 'cliente_nome', 'descricao', 'valor', 'status', 'status_execucao']].head())

# Testar a função get_propostas_finalizadas
print("\nTestando função get_propostas_finalizadas...")
propostas_finalizadas = get_propostas_finalizadas(db)
print(f"Propostas finalizadas (status='Finalizada' e status_execucao='Finalizada' ou status='Recusada'): {len(propostas_finalizadas)}")
print(propostas_finalizadas[['id', 'cliente_nome', 'descricao', 'valor', 'status', 'status_execucao']].head())

# Verificar cada proposta com status Finalizada para identificar os valores de status_execucao
print("\nDetalhes de cada proposta com status='Finalizada':")
propostas_finalizadas_status = propostas[propostas['status'] == 'Finalizada']
for idx, proposta in propostas_finalizadas_status.iterrows():
    print(f"ID: {proposta['id']}, Status: {proposta['status']}, Status Execução: {proposta['status_execucao']}")

print("\nDetalhes de cada proposta com status_execucao='Finalizada':")
propostas_finalizadas_exec = propostas[propostas['status_execucao'] == 'Finalizada']
for idx, proposta in propostas_finalizadas_exec.iterrows():
    print(f"ID: {proposta['id']}, Status: {proposta['status']}, Status Execução: {proposta['status_execucao']}")