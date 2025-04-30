"""
Script para modificar o arquivo pages/propostas.py no ambiente Render
Este script substitui a chamada de finalização de proposta pela versão segura
que utiliza SQL direto para evitar problemas de tipo no PostgreSQL.
"""
import os
import logging
import re
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def modificar_arquivo_propostas():
    """
    Modifica o arquivo pages/propostas.py para usar a função finalizar_proposta_sql
    em vez da implementação original que pode falhar no Render.
    
    Returns:
        bool: True se a modificação foi bem-sucedida, False caso contrário
    """
    arquivo_propostas = Path('pages/propostas.py')
    
    # Verificar se o arquivo existe
    if not arquivo_propostas.exists():
        logger.error(f"Arquivo {arquivo_propostas} não encontrado")
        return False
    
    try:
        # Ler o conteúdo do arquivo
        with open(arquivo_propostas, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        # Verificar se o arquivo já foi modificado
        if "from utils.finalizar_proposta_fix import finalizar_proposta_segura" in conteudo:
            logger.info(f"Arquivo {arquivo_propostas} já foi modificado anteriormente")
            return True
        
        # Adicionar import da função finalizar_proposta_segura
        padrao_import = re.compile(r'(import streamlit as st.*?)(from utils import)',
                                  re.DOTALL)
        if padrao_import.search(conteudo):
            conteudo_modificado = padrao_import.sub(
                r'\1# Import para função de finalização segura\nfrom utils.finalizar_proposta_fix import finalizar_proposta_segura\n\n\2',
                conteudo
            )
        else:
            # Se não encontrar o padrão específico, adicionar após os imports
            padrao_import_alt = re.compile(r'(import .*?)(\n\n)', re.DOTALL)
            if padrao_import_alt.search(conteudo):
                conteudo_modificado = padrao_import_alt.sub(
                    r'\1\n\n# Import para função de finalização segura\nfrom utils.finalizar_proposta_fix import finalizar_proposta_segura\2',
                    conteudo
                )
            else:
                logger.error("Não foi possível encontrar um local adequado para adicionar o import")
                return False
        
        # Substituir chamadas de db.finalizar_proposta por finalizar_proposta_segura
        padrao_finalizar = re.compile(r'db\.finalizar_proposta\((.*?)\)')
        if padrao_finalizar.search(conteudo_modificado):
            conteudo_modificado = padrao_finalizar.sub(r'finalizar_proposta_segura(\1)', conteudo_modificado)
            logger.info("Substituídas chamadas para db.finalizar_proposta por finalizar_proposta_segura")
        else:
            logger.warning("Nenhuma chamada para db.finalizar_proposta encontrada")
        
        # Substituir chamadas alternativas, como database.finalizar_proposta
        padrao_finalizar_alt = re.compile(r'database\.finalizar_proposta\((.*?)\)')
        if padrao_finalizar_alt.search(conteudo_modificado):
            conteudo_modificado = padrao_finalizar_alt.sub(r'finalizar_proposta_segura(\1)', conteudo_modificado)
            logger.info("Substituídas chamadas para database.finalizar_proposta por finalizar_proposta_segura")
        
        # Criar backup do arquivo original
        backup_path = arquivo_propostas.with_suffix('.py.bak')
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        logger.info(f"Backup do arquivo original criado em {backup_path}")
        
        # Salvar o arquivo modificado
        with open(arquivo_propostas, 'w', encoding='utf-8') as f:
            f.write(conteudo_modificado)
        logger.info(f"Arquivo {arquivo_propostas} modificado com sucesso")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao modificar arquivo {arquivo_propostas}: {str(e)}")
        return False

if __name__ == "__main__":
    modificar_arquivo_propostas()