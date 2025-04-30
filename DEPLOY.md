# Guia de Deploy para o Render

Este guia explica como fazer o deploy do Planner Organizer no [Render](https://render.com).

## Pré-requisitos

1. Uma conta no [Render](https://render.com)
2. Acesso ao repositório do GitHub: [bicalho743/PlannerOrganizer](https://github.com/bicalho743/PlannerOrganizer)
3. Um banco de dados PostgreSQL (pode ser criado no próprio Render)

## Etapas para o Deploy

### 1. Crie um banco de dados PostgreSQL no Render

1. Acesse o [Dashboard do Render](https://dashboard.render.com)
2. Clique em "New +" e selecione "PostgreSQL"
3. Preencha as informações:
   - **Name**: planner-db (ou outro nome de sua preferência)
   - **Database**: planner
   - **User**: planner_user
   - **Region**: Escolha a região mais próxima de seus usuários
   - **PostgreSQL Version**: 14 ou superior
   - **Plan**: Free (ou outro plano se necessário)
4. Clique em "Create Database"
5. Aguarde a criação do banco de dados e **anote a URL de conexão**

### 2. Crie um Web Service no Render

1. No Dashboard do Render, clique em "New +" e selecione "Web Service"
2. Conecte com seu repositório GitHub ou selecione "Public Git Repository" e use a URL:
   ```
   https://github.com/bicalho743/PlannerOrganizer.git
   ```
3. Preencha as informações:
   - **Name**: planner-organiza (ou outro nome de sua preferência)
   - **Region**: Mesma região escolhida para o banco de dados
   - **Runtime**: Python 3
   - **Build Command**:
     ```
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```
     python render_deploy_helper.py && python render_startup.py && streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
     ```
4. Na seção "Advanced", adicione as variáveis de ambiente:
   - **DATABASE_URL**: Cole a URL do banco de dados PostgreSQL criado anteriormente
   - **JWT_SECRET**: Gere uma string aleatória (pode usar um [gerador online](https://passwordsgenerator.net/))
   - **PYTHON_VERSION**: 3.11.0

5. Deixe a opção "Auto-Deploy" ativada
6. Clique em "Create Web Service"

### 3. Aguarde o Deploy

1. O Render iniciará automaticamente o processo de deploy
2. Este processo pode levar de 5 a 10 minutos
3. Você pode acompanhar o progresso na aba "Logs"

### 4. Verificar o Deploy

1. Quando o deploy estiver concluído, clique no link fornecido pelo Render
2. Você deverá ver a página de login do Planner Organizer
3. Faça login com as credenciais padrão ou crie uma nova conta

## Solução de Problemas

### Erro "No commits found"

Se você encontrar erros relacionados a "No commits found" durante o deploy:

1. Verifique se o repositório do GitHub está acessível
2. Tente fazer um push manual usando o script `git_push.py`:
   ```
   python git_push.py
   ```
3. Verifique se o token do GitHub está configurado corretamente nas variáveis de ambiente

### Erro de conexão com o banco de dados

Se houver problemas de conexão com o banco de dados:

1. Verifique se a variável de ambiente `DATABASE_URL` está correta
2. Certifique-se de que o banco de dados PostgreSQL está em execução
3. Verifique se o endereço IP do seu serviço web está autorizado a acessar o banco de dados

### Logs para debug

Se precisar de mais informações para debug:
1. No dashboard do Render, acesse a aba "Logs" do seu serviço
2. Selecione "All" para ver todos os logs
3. Procure por mensagens de erro específicas

## Deploy Manual Alternativo

Se você continuar tendo problemas com a integração GitHub, você pode usar o método alternativo com arquivo ZIP:

1. Execute o script `create_deployment_zip.py` para criar um arquivo ZIP do projeto
2. No Render, escolha a opção "Upload Files" ao invés de GitHub durante a criação do serviço
3. Faça upload do arquivo ZIP gerado

## Notas Importantes

- O Render pode levar alguns minutos para disponibilizar o banco de dados após sua criação
- Mudanças de configuração como adicionar variáveis de ambiente requerem um novo deploy
- Para aplicar atualizações futuras, basta fazer push para o repositório do GitHub
- O plano gratuito do Render coloca aplicativos inativos em hibernação após 15 minutos sem uso