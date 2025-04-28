# Alterações Pendentes para Envio ao Repositório

## Arquivos Modificados
- `utils/database.py`: Adicionados métodos `create_perfil` e `get_perfil_by_email` para salvar perfis no PostgreSQL em vez do Firebase Realtime Database
- `pages/registrar.py`: Corrigido botão "Voltar ao login" que não estava funcionando corretamente

## Novos Arquivos
- `update_schema.sql`: Script SQL para adicionar colunas usuario_id às tabelas no banco de dados do Render
- `populate_usuario_id.sql`: Script SQL para popular as colunas usuario_id nas tabelas existentes
- `INSTRUCOES_RENDER_DATABASE.md`: Instruções detalhadas para atualizar o banco de dados no Render

## Procedimento para Atualização
1. Baixe o arquivo `alteracoes.zip` criado nesta sessão
2. Extraia o conteúdo
3. No seu ambiente local (onde você tem acesso ao git):
   - Substitua os arquivos existentes 
   - Adicione os novos arquivos
   - Execute os seguintes comandos git:
```
git add utils/database.py pages/registrar.py update_schema.sql populate_usuario_id.sql INSTRUCOES_RENDER_DATABASE.md
git commit -m "Adicionados métodos para perfis no PostgreSQL e scripts para atualização do banco"
git push origin main
```
4. Siga as instruções em `INSTRUCOES_RENDER_DATABASE.md` para atualizar o banco de dados no Render

## Alterações Detalhadas

### utils/database.py
Adicionados os métodos:
- `create_perfil(self, uid, email, nome_completo)`: Cria um perfil de usuário no PostgreSQL
- `get_perfil_by_email(self, email)`: Recupera um perfil pelo email

### pages/registrar.py
Corrigido o botão "Voltar ao login" para usar `st.session_state.login_page = True` em vez de `current_page = "login"`

### update_schema.sql
Script SQL para adicionar colunas `usuario_id` às tabelas no banco de dados:
- clientes
- produtos
- categorias_financeiro
- lancamentos_financeiro

### populate_usuario_id.sql
Script para popular as colunas `usuario_id` com um valor padrão ou a partir de relacionamentos existentes.

### INSTRUCOES_RENDER_DATABASE.md
Instruções detalhadas passo a passo para aplicar as alterações no banco de dados do Render.