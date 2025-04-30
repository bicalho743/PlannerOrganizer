# Instruções para Resolver Problemas com o Banco de Dados no Render

Este guia contém instruções para resolver o erro `column clientes.usuario_id does not exist` no Render, mesmo após confirmar que a coluna existe no banco de dados.

## Problema

O erro acontece porque o SQLAlchemy mantém um cache de metadados que não atualiza automaticamente quando o esquema do banco de dados é alterado. Mesmo que a coluna tenha sido adicionada diretamente no banco, o SQLAlchemy continua usando seu cache desatualizado.

## Solução

### Opção 1: Atualizar o Render via Upload dos Arquivos

1. Baixe o arquivo ZIP `fix_render_db.zip` que foi criado
2. Acesse o painel do Render
3. Selecione seu serviço web
4. Vá para a aba "Files" (ou "Arquivos")
5. Faça upload dos seguintes arquivos do ZIP:
   - `utils/database.py` (substitua o arquivo existente)
   - `correcao_banco.py` (arquivo novo)
   - `render_no_cache.py` (arquivo novo)
6. Vá para a aba "Settings" e altere o comando "Build Command" para:
   ```
   pip install -r requirements.txt && python render_no_cache.py
   ```
7. Na mesma aba, altere o "Start Command" para:
   ```
   streamlit run app.py
   ```
8. Clique em "Save Changes"
9. Vá para a aba "Manual Deploy" e clique em "Clear build cache & deploy"

### Opção 2: Executar Script Direto no Console do Render

Se preferir executar diretamente no console do Render:

1. Acesse o painel do Render
2. Selecione seu serviço web
3. Vá para a aba "Shell"
4. Cole e execute o conteúdo de `correcao_banco.py`
5. Reinicie seu serviço após executar o script

## Explicação das Mudanças

1. **Modificações no `utils/database.py`**:
   - Desativação do cache de conexões usando `NullPool`
   - Configuração para garantir que as conexões não sejam reutilizadas
   - Adição de um método para forçar atualização de metadados

2. **Novo arquivo `correcao_banco.py`**:
   - Script que verifica a estrutura do banco de dados
   - Verifica se a coluna `usuario_id` existe e a adiciona se não existir
   - Corrige dados faltantes na coluna

3. **Novo arquivo `render_no_cache.py`**:
   - Script de inicialização específico para o Render
   - Executa a correção do cache e depois inicia o aplicativo normalmente

## Verificação

Após aplicar estas alterações, o erro `column clientes.usuario_id does not exist` não deve mais aparecer. Se o problema persistir, verifique os logs do Render para encontrar informações adicionais sobre o erro.

## Importante

- Sempre faça backup de seus dados antes de aplicar estas alterações
- Este é um problema temporário causado pela incompatibilidade de cache
- As alterações não afetam o funcionamento normal do aplicativo, apenas resolvem o problema de cache