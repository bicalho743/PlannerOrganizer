# Guia de Deploy Manual para o Render com Erro de Integração GitHub

Se você está enfrentando erros de integração entre GitHub e Render, como mensagens "No commits found", siga este guia alternativo para realizar o deploy.

## Método 1: Configurar Nova Integração com GitHub

### 1. Gerar um novo token de acesso pessoal no GitHub

1. Acesse [GitHub Settings > Developer Settings > Personal Access Tokens](https://github.com/settings/tokens)
2. Clique em "Generate new token (classic)"
3. Dê um nome como "Render Deploy Token"
4. Selecione os seguintes escopos:
   - `repo` (acesso completo)
   - `workflow`
   - `admin:repo_hook`
5. Clique em "Generate token"
6. **IMPORTANTE**: Copie o token gerado e guarde em um local seguro, pois ele não será mostrado novamente

### 2. Configurar o novo token no Replit

1. No seu projeto Replit, clique em "Secrets" (ícone de cadeado) no painel lateral esquerdo
2. Adicione uma nova variável de ambiente:
   - Chave: `GITHUB_TOKEN`
   - Valor: Cole o token que você gerou no GitHub
3. Clique em "Add new secret"

### 3. Executar o script de push para GitHub

1. Execute o script `git_push.py` para fazer o push das alterações com o novo token:
   ```
   python git_push.py
   ```

### 4. Criar serviço no Render com nova conexão GitHub

1. No dashboard do Render, clique em "New +" e selecione "Web Service"
2. Selecione "Connect account" e escolha GitHub
3. Autorize o Render a acessar seu repositório
4. Selecione o repositório `bicalho743/PlannerOrganizer`
5. Continue com as configurações conforme descrito no guia principal de deploy

## Método 2: Deploy via Arquivo ZIP (Sem Git)

Se a integração com GitHub continuar falhando, você pode fazer o deploy usando um arquivo ZIP:

### 1. Preparar o arquivo ZIP para deploy

1. Execute a aplicação para criar um pacote de deploy:
   ```
   streamlit run create_deployment_zip.py
   ```
2. Isso abrirá uma interface Streamlit onde você pode clicar em "Criar ZIP de Deployment"
3. Baixe o arquivo ZIP gerado

### 2. Criar serviço no Render sem Git

1. No dashboard do Render, clique em "New +" e selecione "Web Service"
2. Em vez de escolher GitHub, role para baixo e selecione "Upload Files"
3. Faça upload do arquivo ZIP que você baixou
4. Configure as informações:
   - **Name**: planner-organiza
   - **Region**: Escolha a região mais próxima de seus usuários
   - **Runtime**: Python 3
   - **Build Command**:
     ```
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```
     python render_deploy_helper.py && python render_startup.py && streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
     ```
5. Na seção "Advanced", adicione as mesmas variáveis de ambiente:
   - **DATABASE_URL**: URL do banco de dados PostgreSQL
   - **JWT_SECRET**: String aleatória para segurança
   - **PYTHON_VERSION**: 3.11.0

6. Clique em "Create Web Service"

## Método 3: Deploy via Conexão Manual de Repositório

Se as opções anteriores não funcionarem, você pode criar um repositório temporário para o deploy:

### 1. Criar novo repositório no GitHub

1. Acesse [GitHub New Repository](https://github.com/new)
2. Crie um novo repositório privado (ex: `PlannerOrganizer-Deploy`)
3. Não adicione README ou outros arquivos iniciais

### 2. Enviar código para o novo repositório

1. No Replit, crie um arquivo `push_to_new_repo.py` com o seguinte conteúdo:
   ```python
   import os
   import subprocess
   
   # Configurar novo repositório
   NOVO_REPO = "https://github.com/SEU_USUARIO/PlannerOrganizer-Deploy.git"
   TOKEN = os.environ.get("GITHUB_TOKEN")
   
   if not TOKEN:
       print("GITHUB_TOKEN não configurado")
       exit(1)
   
   # URL com token
   repo_url_com_token = NOVO_REPO.replace("https://", f"https://x-access-token:{TOKEN}@")
   
   # Comandos
   comandos = [
       ["git", "remote", "add", "novo_repo", repo_url_com_token],
       ["git", "push", "-f", "novo_repo", "main"]
   ]
   
   for cmd in comandos:
       print(f"Executando: {' '.join(cmd)}")
       try:
           resultado = subprocess.run(cmd, capture_output=True, text=True)
           print(resultado.stdout)
           if resultado.stderr:
               print(f"ERRO: {resultado.stderr}")
       except Exception as e:
           print(f"Erro ao executar {cmd}: {e}")
   ```

2. Substitua `SEU_USUARIO` pelo seu nome de usuário do GitHub
3. Execute o script: `python push_to_new_repo.py`

### 3. Conectar ao Render

1. No dashboard do Render, crie um novo serviço web
2. Conecte ao novo repositório que você criou
3. Configure o serviço seguindo as mesmas instruções do método anterior

## Verificação Final

Após configurar o deploy por qualquer um dos métodos:

1. Aguarde a conclusão do processo de deploy (5-10 minutos)
2. Acesse a URL fornecida pelo Render
3. Verifique se o aplicativo está funcionando corretamente
4. Teste o login e outras funcionalidades principais

## Problemas Comuns e Soluções

### Erro durante o push para GitHub

Se você receber erros como "reference already exists" ou "unable to update local ref":

```bash
# Tente criar um novo branch e fazer push dele
git checkout -b render-deploy
git push -f origin render-deploy
```

Depois, no Render, aponte para o branch `render-deploy` em vez de `main`.

### Erro de conexão com o banco de dados

Verifique se a URL do banco de dados inclui `?sslmode=require` no final. O Render requer conexões SSL para seus bancos de dados.