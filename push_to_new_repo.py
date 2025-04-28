"""
Script para enviar o código para um novo repositório no GitHub
Este script é útil quando você está enfrentando problemas com a integração
Git no Render e precisa de uma solução alternativa.
"""

import os
import sys
import subprocess
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Você precisa substituir estes valores
NOVO_REPO = "https://github.com/SEU_USUARIO/PlannerOrganizer-Deploy.git"

def run_command(cmd, desc=None):
    """Executa um comando e retorna o resultado"""
    if desc:
        logger.info(f"Executando: {desc}")
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            check=False
        )
        
        if result.stdout:
            logger.info(f"Saída: {result.stdout.strip()}")
        if result.stderr:
            logger.warning(f"Erro: {result.stderr.strip()}")
            
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Erro executando comando: {e}")
        return False

def setup_git():
    """Configura o Git com informações básicas"""
    return (
        run_command(
            ["git", "config", "user.name", "Deploy Bot"], 
            "Configurando nome do usuário"
        ) and 
        run_command(
            ["git", "config", "user.email", "deploy@plannerorganiza.com.br"], 
            "Configurando email do usuário"
        )
    )

def push_to_new_repo():
    """Envia o código para o novo repositório"""
    # Verificar token
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        logger.error("Token do GitHub (GITHUB_TOKEN) não encontrado nas variáveis de ambiente")
        return False
    
    # URL do repositório com token
    repo_url_with_token = NOVO_REPO.replace(
        "https://", 
        f"https://x-access-token:{github_token}@"
    )
    
    # Configurar Git
    if not setup_git():
        logger.error("Falha ao configurar Git")
        return False
    
    # Adicionar o novo repositório como remote
    if not run_command(
        ["git", "remote", "add", "novo_repo", repo_url_with_token], 
        "Adicionando novo repositório como remote"
    ):
        # Talvez o remote já exista, tente remover e adicionar novamente
        run_command(["git", "remote", "remove", "novo_repo"], "Removendo remote existente")
        if not run_command(
            ["git", "remote", "add", "novo_repo", repo_url_with_token], 
            "Adicionando novo repositório como remote (nova tentativa)"
        ):
            logger.error("Falha ao adicionar remote")
            return False
    
    # Forçar push para o novo repositório
    if not run_command(
        ["git", "push", "-f", "novo_repo", "main"], 
        "Enviando código para o novo repositório"
    ):
        logger.error("Falha ao enviar código para o novo repositório")
        return False
    
    logger.info("Código enviado com sucesso para o novo repositório!")
    return True

def main():
    """Função principal"""
    logger.info("Iniciando push para novo repositório...")
    
    # Verificar se NOVO_REPO foi alterado
    if "SEU_USUARIO" in NOVO_REPO:
        logger.error("Você precisa editar o script e substituir 'SEU_USUARIO' pelo seu nome de usuário do GitHub")
        return 1
    
    if push_to_new_repo():
        logger.info("Operação concluída com sucesso!")
        logger.info(f"Acesse o Render e conecte ao repositório: {NOVO_REPO}")
        return 0
    else:
        logger.error("Falha na operação. Verifique os erros acima.")
        return 1

if __name__ == "__main__":
    sys.exit(main())