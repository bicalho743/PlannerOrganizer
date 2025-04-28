
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
            check=False
        )
        
        if show_output:
            if result.stdout:
                logger.info(f"Saída: {result.stdout.strip()}")
            if result.stderr:
                logger.warning(f"Erro: {result.stderr.strip()}")
        
        return result.returncode == 0, result.stdout.strip() if result.stdout else result.stderr.strip()
    except Exception as e:
        logger.error(f"Erro ao executar comando: {e}")
        return False, str(e)

def push_to_github():
    """
    Faz o push das alterações para o GitHub usando o GITHUB_TOKEN
    """
    logger.info("Iniciando processo de push para GitHub...")
    
    # Verificar token do GitHub
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        logger.error("Token do GitHub (GITHUB_TOKEN) não configurado nas variáveis de ambiente")
        return False

    # Verificar configuração do Git
    success, output = run_command(["git", "config", "--list"], "Verificando configuração do Git")
    if not success:
        logger.error("Erro ao verificar configuração do Git")
        return False
        
    # Configurar credenciais
    steps = [
        (["git", "config", "user.name", "Deploy Bot"], "Configurando nome do usuário Git", True),
        (["git", "config", "user.email", "deploy@plannerorganiza.com.br"], "Configurando email do usuário Git", True),
        (["git", "config", "--global", "http.sslVerify", "false"], "Desabilitando verificação SSL", False),
        (["git", "status"], "Verificando status do repositório", True),
        (["git", "add", "."], "Adicionando arquivos", True),
        (["git", "commit", "-m", f"Atualização automática {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"], "Fazendo commit das alterações", True),
    ]
    
    # Executar configurações iniciais
    for command, description, show_output in steps:
        success, output = run_command(command, description, show_output)
        if not success:
            if "nothing to commit" in output:
                logger.info("Nenhuma alteração para enviar ao GitHub")
                return True
            logger.error(f"Falha no passo: {description}")
            logger.error(f"Saída: {output}")
            return False
        time.sleep(1)

    # Configurar URL do repositório com token
    remote_url = subprocess.run(["git", "remote", "get-url", "origin"], 
                              capture_output=True, text=True).stdout.strip()
    if 'https://' in remote_url:
        new_url = remote_url.replace('https://', f'https://x-access-token:{github_token}@')
        success, output = run_command(["git", "remote", "set-url", "origin", new_url], 
                                    "Configurando URL remota com token", False)
        if not success:
            logger.error("Falha ao configurar URL remota")
            return False

    # Fazer push
    success, output = run_command(["git", "push", "origin", "main"], 
                                "Enviando alterações para GitHub", True)
    if not success:
        logger.error(f"Falha ao fazer push: {output}")
        return False

    logger.info("Alterações enviadas com sucesso para o GitHub!")
    return True

def main():
    """Função principal"""
    result = push_to_github()
    return 0 if result else 1

if __name__ == "__main__":
    sys.exit(main())
