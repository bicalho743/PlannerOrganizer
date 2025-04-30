# Instruções para Deploy no Render.com

## Passos para Realizar o Deploy no Render

### 1. Preparação do Projeto

Antes de realizar o deploy no Render, certifique-se de que o projeto está pronto:

- Todos os arquivos necessários estão no repositório
- O ambiente local está funcionando corretamente
- Os scripts de inicialização foram incluídos (`render_startup.py`)
- O arquivo `app.py` está configurado para detectar o ambiente Render

### 2. Criar uma Conta no Render

1. Acesse [render.com](https://render.com/)
2. Clique em "Sign Up" e crie uma conta usando GitHub, GitLab, ou e-mail

### 3. Criar um Novo Serviço

1. No Dashboard do Render, clique em "New +"
2. Selecione "Web Service"
3. Conecte seu repositório ou faça upload do código fonte

### 4. Configuração do Serviço

Configure o serviço com as seguintes informações:

- **Nome**: Um nome para identificar seu serviço (ex: "planner-organizer")
- **Região**: Escolha a região mais próxima dos seus usuários
- **Tipo de Ambiente**: Selecione "Python"
- **Versão do Python**: Selecione "3.11" (ou a versão que seu projeto usa)
- **Comando de Build**: `pip install -r requirements.txt`
- **Comando de Start**: `python app.py`

### 5. Configuração de Variáveis de Ambiente

No Render, vá para a seção "Environment Variables" e adicione:

- `DATABASE_URL`: URL do seu banco de dados PostgreSQL
- `JWT_SECRET`: Sua chave secreta para JWT
- `FIREBASE_API_KEY`: Sua chave de API do Firebase
- `RENDER`: true (para indicar que estamos no ambiente Render)

### 6. Configuração do Banco de Dados

1. No Dashboard do Render, vá para "New +" e selecione "PostgreSQL"
2. Configure o banco de dados:
   - **Nome**: Um nome para identificar seu banco (ex: "planner-db")
   - **Versão do PostgreSQL**: Selecione a versão compatível
3. Anote as credenciais fornecidas para configurar a variável `DATABASE_URL`
4. Configure a variável `DATABASE_URL` no formato:  
   `postgresql://username:password@host:port/database`

### 7. Deploy da Aplicação

1. Clique em "Create Web Service" para iniciar o deploy
2. Aguarde enquanto o Render constrói e inicia sua aplicação
3. Acompanhe o progresso nos logs para verificar se tudo está funcionando corretamente

### 8. Verificação e Solução de Problemas

Após o deploy, se você encontrar problemas:

1. Verifique os logs no Dashboard do Render:
   - Selecione seu serviço
   - Vá para a guia "Logs"
   - Procure por mensagens de erro

2. Se houver problemas com a inicialização ou conexão com o banco de dados:
   - Verifique as credenciais do banco de dados
   - Confira se o script `render_startup.py` está sendo executado
   - Verifique o arquivo de log `render_startup.log` para mensagens de erro

3. Se houver problemas com finalização de propostas:
   - Faça login no console SQL do banco de dados
   - Verifique se as funções SQL mencionadas na documentação foram criadas

### 9. Atualização do Domínio (Opcional)

Para configurar um domínio personalizado:

1. No Render, vá para seu serviço web
2. Clique na guia "Settings"
3. Vá para "Custom Domain"
4. Siga as instruções para configurar seu domínio personalizado

### 10. Manutenção Contínua

Depois do deploy:

1. Monitore regularmente os logs da aplicação
2. Faça backups periódicos do banco de dados
3. Quando fizer atualizações no código, elas serão implantadas automaticamente

## Recuperação de Erros

Se você encontrar erros críticos após o deploy:

1. Verifique os logs completos no Dashboard do Render
2. Se necessário, reverta para uma versão anterior no histórico de implantações
3. Em último caso, você pode excluir o serviço e fazer o deploy novamente

Lembre-se: O script `render_startup.py` aplicará automaticamente as correções necessárias durante a inicialização.

## Melhores Práticas

- Mantenha o arquivo `requirements.txt` atualizado
- Use variáveis de ambiente para todas as configurações sensíveis
- Implemente monitoramento de desempenho
- Faça backups regulares do banco de dados
- Documente todas as mudanças significativas