# Instruções para Atualizar o Banco de Dados no Render

Estes passos são necessários para corrigir o problema em que a aplicação no Render mostra erros como:
```
column clientes.usuario_id does not exist
```

## Passos para Atualização

### 1. Acesse o Dashboard do Render

1. Faça login no [Render Dashboard](https://dashboard.render.com/)
2. Vá para o serviço PostgreSQL usado pelo seu aplicativo

### 2. Acesse o Console do Banco de Dados

1. No serviço PostgreSQL, procure por "Connect" ou "Console"
2. Abra a interface SQL do banco de dados (normalmente é um botão "psql console")

### 3. Execute o Script de Alteração do Schema

1. Copie todo o conteúdo do arquivo `update_schema.sql` fornecido
2. Cole e execute o script na interface SQL do Render
3. Verifique se o script foi executado sem erros
4. Você deve ver uma lista das tabelas que agora têm a coluna `usuario_id`

### 4. Execute o Script para Popular usuario_id (Se Necessário)

Se você tiver dados existentes nas tabelas:

1. Edite o arquivo `populate_usuario_id.sql` e substitua `SEU_ID_USUARIO_FIREBASE` pelo seu ID real do Firebase
   - Exemplo: `7Be1aICPHZdrS4ghnHZxc9Jp3Yt1`
2. Copie todo o conteúdo do arquivo modificado
3. Cole e execute o script na interface SQL do Render
4. Verifique se o script foi executado sem erros
5. Você deve ver uma contagem dos registros atualizados por tabela

### 5. Reinicie o Serviço Web

1. Volte para o dashboard do Render
2. Acesse seu serviço Web (o aplicativo Streamlit)
3. Clique em "Manual Deploy" e selecione "Clear build cache & deploy"
4. Aguarde o deploy ser concluído
5. Acesse o aplicativo novamente e teste as funcionalidades

## Verificação Final

Após executar os passos acima, acesse o aplicativo e verifique se os erros de `column clientes.usuario_id does not exist` ou similares foram resolvidos.

Se você continuar tendo problemas, verifique os logs do serviço no Render para identificar a causa.

## Caso Ainda Haja Problemas

Se ainda houver problemas mesmo após esses passos, considere:

1. Verificar se todos os comandos SQL foram executados com sucesso
2. Verificar se o deploy foi completo após a atualização do banco
3. Confirmar se as variáveis de ambiente como DATABASE_URL estão definidas corretamente
4. Como último recurso, considere recriar o banco de dados do zero

## Notas Adicionais

- A adição da coluna `usuario_id` é essencial para o funcionamento do isolamento multi-tenant do sistema
- Estes scripts adicionam colunas sem modificar ou excluir dados existentes
- Se você tiver grandes volumes de dados, o processo de atualização pode levar algum tempo