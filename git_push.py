import os
import requests
import base64
import datetime

# Função para fazer o push para o GitHub usando a API
def push_to_github():
    # Token do GitHub
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        print("GITHUB_TOKEN não encontrado.")
        return False
    
    # Nome do repositório e proprietário
    owner = "bicalho743"
    repo = "PlannerOrganizer"
    
    # Cabeçalho de autenticação
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Nome do arquivo e caminho
    file_path = "pages/financeiro.py"
    
    try:
        # 1. Obter o SHA atual do arquivo
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Erro ao obter o arquivo: {response.status_code}")
            print(response.json())
            return False
        
        file_sha = response.json().get('sha')
        
        # 2. Ler o conteúdo do arquivo local
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 3. Codificar o conteúdo em base64
        content_encoded = base64.b64encode(content.encode()).decode()
        
        # 4. Preparar os dados para o commit
        commit_data = {
            'message': 'Simplificar filtro no histórico financeiro para mostrar apenas Receita e Despesa',
            'content': content_encoded,
            'sha': file_sha,
            'branch': 'main'  # ou a branch que deseja usar
        }
        
        # 5. Enviar o commit
        response = requests.put(url, headers=headers, json=commit_data)
        
        if response.status_code in [200, 201]:
            print("Arquivo atualizado com sucesso no GitHub!")
            return True
        else:
            print(f"Erro ao atualizar o arquivo: {response.status_code}")
            print(response.json())
            return False
            
    except Exception as e:
        print(f"Erro: {str(e)}")
        return False

if __name__ == "__main__":
    print(f"Iniciando push para GitHub em {datetime.datetime.now()}")
    result = push_to_github()
    print(f"Resultado do push: {'Sucesso' if result else 'Falha'}")