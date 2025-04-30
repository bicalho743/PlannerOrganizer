import os
import subprocess
import sys

def push_changes():
    """
    Faz o push das alterações para o GitHub usando o GITHUB_TOKEN
    """
    try:
        # Configurar credenciais
        token = os.environ.get('GITHUB_TOKEN')
        if not token:
            print("GITHUB_TOKEN não encontrado nas variáveis de ambiente")
            return False
            
        # Configura o usuário e email para o commit
        subprocess.run(["git", "config", "--global", "user.name", "Planner Organizer Dev"])
        subprocess.run(["git", "config", "--global", "user.email", "dev@plannerorganizer.com.br"])
        
        # Adiciona as alterações
        result = subprocess.run(["git", "add", "pages/financeiro.py"], 
                      capture_output=True, text=True)
        print(f"Adicionando arquivos: {result.stdout} {result.stderr}")
        
        # Cria o commit
        msg = "Simplificar filtro no histórico financeiro para mostrar apenas Receita e Despesa"
        result = subprocess.run(["git", "commit", "-m", msg], 
                      capture_output=True, text=True)
        print(f"Commit: {result.stdout} {result.stderr}")
        
        # Configura a URL remota com o token
        remote_url = subprocess.run(["git", "remote", "get-url", "origin"], 
                           capture_output=True, text=True).stdout.strip()
        
        if 'https://' in remote_url:
            # Formata: https://user:token@github.com/user/repo.git
            new_url = remote_url.replace('https://', f'https://x-access-token:{token}@')
            subprocess.run(["git", "remote", "set-url", "origin", new_url])
            print("URL remota configurada com o token")
        
        # Faz o push
        result = subprocess.run(["git", "push", "origin", "main"], 
                      capture_output=True, text=True)
        print(f"Push: {result.stdout} {result.stderr}")
        
        return "Alterações enviadas com sucesso para o GitHub" in result.stdout or result.returncode == 0
        
    except Exception as e:
        print(f"Erro ao enviar para o GitHub: {str(e)}")
        return False

if __name__ == "__main__":
    if push_changes():
        print("Push para o GitHub realizado com sucesso!")
    else:
        print("Falha ao realizar o push para o GitHub.")
        sys.exit(1)