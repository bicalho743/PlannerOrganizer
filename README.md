# Planner Organiza

Sistema de gerenciamento de negócios com foco em propostas, clientes e finanças.

**Versão atual: 3.0.0 (07-05-2025)**
**Última atualização: Otimização do sistema para produção e melhoria no desempenho**

## Funcionalidades

- Gerenciamento de Clientes
- Criação e Acompanhamento de Propostas
- Controle Financeiro (Pendências e Histórico)
- Relatórios e Dashboards Interativos
- Importação e Exportação de Dados
- Geração de PDFs personalizados
- Controle de Vendas com Cálculo de Lucro

## Requisitos

- Python 3.11+
- PostgreSQL
- Dependências listadas no arquivo `requirements.txt`

## Variáveis de Ambiente

Para o sistema funcionar corretamente, você precisará configurar as seguintes variáveis de ambiente:

- `DATABASE_URL`: URL de conexão com o banco de dados PostgreSQL
- `JWT_SECRET`: Chave secreta para geração de tokens JWT
- `FIREBASE_API_KEY`: Chave da API do Firebase (autenticação)
- `SENDGRID_API_KEY`: (Opcional) Chave da API do SendGrid para envio de e-mails

## Como Executar Localmente

1. Clone o repositório
2. Instale as dependências: `pip install -r requirements.txt`
3. Configure as variáveis de ambiente necessárias
4. Execute: `streamlit run app.py`

## Deployment

Este projeto está configurado para deploy no Render através do arquivo `render.yaml`.

Para realizar o deploy:

1. Conecte sua conta GitHub ao Render
2. No dashboard do Render, clique em "New" > "Blueprint"
3. Selecione o repositório com o código do projeto
4. Aguarde a criação dos serviços conforme definido no arquivo render.yaml
5. Configure as variáveis de ambiente necessárias (DATABASE_URL, JWT_SECRET, etc.)
6. O deploy automático será acionado a cada novo commit no branch principal

### Solução para problema de deploy no Render

Se o Render mostrar erro "No commits found" ao tentar fazer deploy:

1. Verifique se o token de acesso do GitHub está ativo
2. Reconecte o repositório ao Render nos Settings do serviço 
3. Tente fazer deploy manual com o commit mais recente
4. Se necessário, faça uma pequena alteração no código e um novo push para gerar um commit detectável