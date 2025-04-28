"""
Script para fazer push de alterações para o GitHub usando token
"""
import os
import subprocess
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
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
    """Faz push das alterações para o GitHub"""
    logger.info("Iniciando push para GitHub...")

    # Verificar token
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        logger.error("Token do GitHub não encontrado nas variáveis de ambiente")
        return False

    # Configurar Git
    run_command(["git", "config", "--global", "user.name", "Deploy Bot"], "Configurando nome do usuário Git")
    run_command(["git", "config", "--global", "user.email", "deploy@plannerorganiza.com.br"], "Configurando email do usuário Git")

    # Verificar status
    success, output = run_command(["git", "status"], "Verificando status do repositório")
    if not success:
        logger.error("Erro ao verificar status do Git")
        return False

    # Adicionar alterações
    success, output = run_command(["git", "add", "."], "Adicionando arquivos")
    if not success:
        logger.error("Erro ao adicionar arquivos")
        return False

    # Criar commit
    commit_msg = f"Atualização automática {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    success, output = run_command(["git", "commit", "-m", commit_msg], "Fazendo commit das alterações")
    if not success and "nothing to commit" not in output:
        logger.error(f"Erro ao criar commit: {output}")
        return False
    elif "nothing to commit" in output:
        logger.info("Nenhuma alteração para enviar ao GitHub")
        return True


    # Configurar URL remota com token
    remote_url = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        capture_output=True,
        text=True
    ).stdout.strip()

    if remote_url:
        if 'https://' in remote_url:
            new_url = f'https://x-access-token:{github_token}@github.com/{remote_url.split("github.com/")[1]}'
            success, output = run_command(["git", "remote", "set-url", "origin", new_url], "Configurando URL remota com token")
            if not success:
                logger.error("Falha ao configurar URL remota")
                return False

    # Fazer push
    success, output = run_command(["git", "push", "origin", "main"], "Enviando alterações para GitHub")
    if not success:
        logger.error(f"Erro ao fazer push: {output}")
        return False

    logger.info("Push realizado com sucesso!")
    return True

if __name__ == "__main__":
    success = push_to_github()
    exit(0 if success else 1)