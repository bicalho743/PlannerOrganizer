# Instruções de Instalação para o Render

Este pacote contém todos os arquivos necessários para corrigir problemas de finalização de propostas e exclusão de clientes no ambiente Render. A solução é automática e não requer intervenções manuais após a instalação inicial.

## Arquivos incluídos neste pacote

1. `fix_render_type_errors.py` - Correção para problemas de tipos no PostgreSQL
2. `modifica_propostas.py` - Script para modificar o arquivo pages/propostas.py
3. `render_startup.py` - Script de inicialização automática para o Render
4. `utils/finalizar_proposta_fix.py` - Implementação segura da função finalizar_proposta
5. `solucao_render.md` - Documentação detalhada sobre a solução

## Passos para instalação

1. **Faça login no painel do Render**
2. **Navegue até o serviço da sua aplicação**
3. **Vá para a aba "Shell"**
4. **Execute os seguintes comandos:**

```bash
# Criar diretório temporário
mkdir -p /tmp/render_fix

# Descompactar os arquivos
cd /tmp/render_fix
unzip /path/to/fix_render_final.zip

# Copiar arquivos para o diretório da aplicação
cp -r * /opt/render/project/src/

# Limpar diretório temporário
cd /
rm -rf /tmp/render_fix

# Verificar se os arquivos foram copiados corretamente
ls -la /opt/render/project/src/fix_render_type_errors.py
ls -la /opt/render/project/src/render_startup.py
ls -la /opt/render/project/src/utils/finalizar_proposta_fix.py

# Executar teste do script de inicialização
cd /opt/render/project/src/
python render_startup.py
```

5. **Reinicie o serviço no Render**
6. **Verifique os logs para confirmar que as correções foram aplicadas**

## Como a solução funciona

Quando a aplicação é iniciada no Render, o arquivo `app.py` detecta automaticamente o ambiente Render e executa o script `render_startup.py`, que por sua vez:

1. Aplica as correções no banco de dados usando `fix_render_type_errors.py`
2. Modifica o arquivo `pages/propostas.py` para usar a implementação segura de finalização

Para mais detalhes sobre o funcionamento da solução, consulte o arquivo `solucao_render.md`.

## Resolução de problemas

Se encontrar problemas após a instalação, verifique:

1. **Logs da aplicação**
   - Procure por mensagens de erro relacionadas aos scripts de correção

2. **Arquivo de log do script de inicialização**
   - Verifique o arquivo `render_startup.log` que é criado no diretório raiz

3. **Banco de dados**
   - Use a console SQL do Render para verificar se as funções e triggers foram criados corretamente
   - Execute `SELECT * FROM pg_proc WHERE proname IN ('finalizar_proposta', 'desassociar_propostas_cliente');` para verificar as funções SQL
   - Execute `SELECT * FROM pg_trigger WHERE tgname = 'atualizar_usuario_id_financeiro_trigger';` para verificar o trigger

4. **Modificação do código**
   - Verifique se o arquivo `pages/propostas.py` foi modificado para usar a função `finalizar_proposta_segura`

## Suporte

Se precisar de suporte adicional, entre em contato com o desenvolvedor.