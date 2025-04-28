# Instruções para Resolver Erro de Coluna no Render

Este guia contém instruções para resolver o erro `column clientes.usuario_id does not exist` que ocorre no Render, mesmo após confirmar que a coluna existe no banco de dados.

## O Problema

O erro ocorre porque o SQLAlchemy mantém um cache de metadados que não é atualizado quando você altera o banco diretamente via SQL. Isso faz com que a aplicação continue reportando que a coluna não existe, mesmo quando você já a adicionou.

## Solução

### 1. Atualizar o Startup Command no Render

Acesse o painel do Render e altere o comando de inicialização:

1. Faça login no [dashboard do Render](https://dashboard.render.com/)
2. Selecione seu serviço web
3. Vá para a aba "Settings"
4. Altere o "Start Command" de:
   ```
   streamlit run app.py --server.port 10000 --server.address 0.0.0.0
   ```
   para:
   ```
   python render_no_cache.py
   ```
5. Clique em "Save Changes"

### 2. Fazer Upload dos Arquivos de Correção

Faça upload dos seguintes arquivos para o seu repositório:

- `fix_render_schema.py` - Script que verifica e corrige o esquema do banco 
- `fix_render_database.sql` - Script SQL para corrigir o banco diretamente
- `render_no_cache.py` - Script de inicialização alternativo para o Render

### 3. Deploy Limpo

1. No painel do Render, vá para a aba "Manual Deploy"
2. Clique no botão "Clear build cache & deploy"
3. Aguarde o término do deploy e verifique os logs para conferir se o script de correção foi executado

## Verificação

Depois de aplicar as correções, acesse a aplicação e verifique:

1. Se consegue fazer login normalmente
2. Se os clientes estão sendo exibidos corretamente
3. Se as propostas podem ser criadas e editadas

## Reversão

Se algo der errado, você pode:

1. Voltar ao comando de inicialização original
2. Fazer um novo deploy limpo
3. Se necessário, restaurar o banco de dados a partir de um backup

## Outras Considerações

- Esses scripts não afetam os dados existentes, apenas corrigem o esquema
- O script `render_no_cache.py` irá executar a correção de esquema em cada inicialização da aplicação
- As correções não são necessárias em ambiente local, somente no Render