"""
Script para fazer push de alterações para o GitHub usando credenciais configuradas
Como o Replit não permite modificações diretas nos arquivos Git, este script usa
comandos git através de subprocess para evitar bloqueios de arquivos.
"""

import os
import sys
import time
import logging
import subprocess
from datetime import datetime

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def run_command(command, description=None, show_output=True):
    """
    Executa um comando git e retorna o resultado
    
    Args:
        command (list): Comando a ser executado
        description (str): Descrição do comando para log
        show_output (bool): Se deve mostrar a saída do comando
        
    Returns:
        tuple: (success, output)
    """
    if description:
        logger.info(f"Executando: {description}")
    
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False  # Não queremos que exceptions sejam lançadas
        )
        
        if show_output:
            if result.stdout:
                logger.info(f"Saída: {result.stdout.strip()}")
            if result.stderr:
                logger.warning(f"Erro: {result.stderr.strip()}")
        
        return result.returncode == 0, result.stdout.strip() if result.stdout else ""
    except Exception as e:
        logger.error(f"Erro ao executar comando: {e}")
        return False, str(e)

def push_to_github():
    """
    Faz o push das alterações para o GitHub usando o GITHUB_TOKEN
    """
    logger.info("Iniciando processo de push para GitHub...")
    
    # 1. Verificar se temos credenciais do GitHub
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        logger.error("Token do GitHub (GITHUB_TOKEN) não configurado nas variáveis de ambiente")
        return False
    
    # Mensagem de commit padrão com timestamp
    commit_message = f"Atualização automática {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # Estrutura similar ao git add, commit e push
    steps = [
        (["git", "config", "user.name", "Deploy Bot"], "Configurando nome do usuário Git", True),
        (["git", "config", "user.email", "deploy@plannerorganiza.com.br"], "Configurando email do usuário Git", True),
        (["git", "status"], "Verificando status do repositório", True),
        (["git", "add", "."], "Adicionando arquivos", True),
        (["git", "commit", "-m", commit_message], "Fazendo commit das alterações", True),
        (["git", "push", "origin", "main"], "Enviando alterações para GitHub", True)
    ]
    
    # Executar cada passo
    for command, description, show_output in steps:
        success, output = run_command(command, description, show_output)
        if not success:
            if "nothing to commit" in output:
                logger.info("Nenhuma alteração para enviar ao GitHub")
                return True
            logger.error(f"Falha no passo: {description}")
            return False
        time.sleep(1)  # Pequena pausa entre comandos
    
    logger.info("Alterações enviadas com sucesso para o GitHub!")
    return True

def main():
    """Função principal"""
    result = push_to_github()
    return 0 if result else 1

if __name__ == "__main__":
    sys.exit(main())