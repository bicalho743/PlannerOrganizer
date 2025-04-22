# Guia de Deploy do Planner Organizer no Render

Este guia contém instruções para fazer o deploy do sistema Planner Organizer no Render e configurá-lo com seu domínio personalizado da Locaweb.

## Pré-requisitos

- Uma conta no [Render](https://render.com)
- Um repositório no GitHub com o código do projeto
- Seu domínio da Locaweb (plannerorganiza.com.br)
- Os segredos/variáveis de ambiente necessários (DATABASE_URL, JWT_SECRET)

## Passo 1: Preparar o repositório GitHub

1. Certifique-se de que seu repositório GitHub contém os seguintes arquivos:
   - `requirements.txt` - Lista de dependências
   - `Procfile` - Instruções para iniciar a aplicação
   - `render.yaml` - Configuração do serviço no Render
   - `render_startup.py` - Script de inicialização
   - `runtime.txt` - Especificação da versão do Python

2. Faça commit e push dessas alterações para seu repositório no GitHub.

## Passo 2: Configurar o serviço no Render

1. Faça login em sua conta do Render.

2. Clique em "New" e selecione "Blueprint" para usar o arquivo render.yaml para configuração.

3. Conecte sua conta GitHub e selecione o repositório onde seu código está.

4. Render detectará automaticamente o arquivo render.yaml e mostrará os serviços a serem criados.

5. Clique em "Apply Blueprint" para criar o serviço web e o banco de dados.

6. Aguarde enquanto o Render provisiona o banco de dados e configura o ambiente.

## Passo 3: Configurar as variáveis de ambiente

1. Depois que o serviço web for criado, acesse-o no painel do Render.

2. Vá para a guia "Environment" e configure as seguintes variáveis:

   - `DATABASE_URL`: A URL de conexão com o banco de dados PostgreSQL. Se você criou um banco de dados pelo Render, este valor será definido automaticamente.
   
   - `JWT_SECRET`: Uma chave secreta para geração de tokens JWT. Você pode gerar uma usando:
     ```
     openssl rand -hex 32
     ```

3. Clique em "Save Changes" para aplicar as configurações.

## Passo 4: Verificar o deploy

1. Após salvar as variáveis de ambiente, Render fará o redeploy automático da aplicação.

2. Aguarde a conclusão do build e verifique se a aplicação está em execução sem erros.

3. Você pode acessar os logs para diagnosticar problemas clicando em "Logs" no painel lateral.

## Passo 5: Configurar o domínio personalizado

1. No painel do seu serviço web no Render, vá para a guia "Settings".

2. Role para baixo até "Custom Domain" e clique em "Add Custom Domain".

3. Digite seu domínio: `www.plannerorganiza.com.br`

4. Render fornecerá instruções específicas para configurar registros DNS para verificar seu domínio:

   - Você precisará adicionar um registro CNAME no painel de controle DNS da Locaweb:
     ```
     CNAME  www  [seu-app].onrender.com
     ```

5. Para o domínio raiz (sem www), você pode:
   - Adicionar um registro A direcionando para os IPs do Render, ou
   - Configurar um redirecionamento para a versão www no painel da Locaweb

6. Aguarde a propagação do DNS (até 24-48 horas, mas geralmente é mais rápido).

## Passo 6: Verificar o SSL

1. Render configurará automaticamente certificados SSL/HTTPS para seu domínio personalizado.

2. Você não precisa fazer nada além de aguardar a verificação do domínio e a emissão do certificado.

## Solução de problemas comuns

### A aplicação não inicia

- Verifique os logs para identificar o problema específico
- Confirme se as variáveis de ambiente estão configuradas corretamente
- Garanta que o banco de dados esteja acessível

### Problemas com o banco de dados

- Verifique se a URL do banco de dados está correta
- Confirme que o banco de dados está ativo e não foi pausado por inatividade
- Verifique se as tabelas foram criadas corretamente

### Erros de DNS no Banco de Dados PostgreSQL

Se você encontrar erros como:
```
could not translate host name "dpg-xxxx" to address: Name or service not known
```

Este é um problema comum no ambiente do Render, especialmente após a criação inicial do serviço ou depois de longos períodos de inatividade. Algumas soluções:

1. **Reconectar o banco de dados**:
   - No dashboard do Render, vá até seu banco de dados
   - Na aba "Info", clique em "Reset Database Credentials"
   - Aguarde a operação concluir e atualize sua variável de ambiente DATABASE_URL

2. **Permitir mais tempo para resolução de DNS**:
   - O script `render_startup.py` já foi modificado para tentar por mais tempo a resolução do DNS
   - Pode ser necessário um redeploy manual para aplicar essas mudanças

3. **Entre em contato com o suporte do Render**:
   - Se o problema persistir após várias tentativas de deploy, abra um chamado com o suporte do Render

### Domínio personalizado não funciona

- Confirme que os registros DNS estão configurados corretamente
- Verifique se houve tempo suficiente para a propagação do DNS
- Revise as configurações no painel da Locaweb

## Observações importantes

- Aplicações no plano gratuito do Render serão pausadas após 15 minutos de inatividade.
- O banco de dados no plano gratuito tem limite de 1GB de armazenamento.
- Para evitar pausas e obter maior disponibilidade, considere fazer upgrade para um plano pago.

---

Para suporte adicional, consulte a [documentação oficial do Render](https://render.com/docs).