# Solução para Problemas de Finalização de Propostas no Render

Este documento contém as instruções para resolver os problemas de finalização de propostas e exclusão de clientes no ambiente Render.

## Instruções de Aplicação

1. Faça login no Console do Render (dashboard.render.com)
2. Acesse seu serviço web onde o aplicativo está hospedado
3. Vá para a guia "Shell" para acessar o console
4. Execute o arquivo `fix_render_type_errors.py` com o comando:
   ```
   python fix_render_type_errors.py
   ```
5. Verifique se a saída do script mostra "CORREÇÃO CONCLUÍDA COM SUCESSO"
6. Reinicie o serviço no Render para aplicar todas as alterações

## O que Este Script Corrige

1. **Finalização de Propostas**: Corrige o problema de propostas que não podem ser finalizadas na interface
   - Cria uma função SQL `finalizar_proposta(proposta_id)` que pode ser chamada diretamente
   - Usa o campo `data_fim` em vez de `data_finalizacao` que não existe no schema

2. **Exclusão de Clientes**: Permite excluir clientes que possuem propostas associadas
   - Cria uma função SQL `desassociar_propostas_cliente(cliente_id)` que transfere propostas para um cliente genérico

3. **Consistência de Dados**: 
   - Cria um trigger para manter a relação entre propostas e lançamentos financeiros
   - Garante que o campo `usuario_id` seja corretamente propagado

4. **Normalização de Dados**:
   - Corrige valores inconsistentes em propostas
   - Preenche dados de clientes que estão nulos
   - Corrige telefones com formato inválido

## Uso da Solução

Após aplicar o script, você poderá:

1. Finalizar uma proposta via SQL (se ainda houver problemas na interface):
   ```sql
   SELECT finalizar_proposta(ID_DA_PROPOSTA);
   ```

2. Excluir um cliente com propostas associadas:
   ```sql
   SELECT desassociar_propostas_cliente(ID_DO_CLIENTE);
   -- Em seguida, exclua o cliente normalmente pela interface
   ```

## Verificar se a Solução foi Aplicada

Execute estas consultas SQL para verificar se a solução foi aplicada:

```sql
-- Verificar se a função finalizar_proposta existe
SELECT exists(SELECT * FROM pg_proc WHERE proname = 'finalizar_proposta');

-- Verificar se a função desassociar_propostas_cliente existe
SELECT exists(SELECT * FROM pg_proc WHERE proname = 'desassociar_propostas_cliente');

-- Verificar se o trigger de consistência existe
SELECT exists(SELECT * FROM pg_trigger WHERE tgname = 'financeiro_usuario_id_trigger');
```

Se todas as consultas retornarem `true`, a solução foi aplicada corretamente.