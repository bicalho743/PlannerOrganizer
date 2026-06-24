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

   
### MELHORIAS DA APLICAÇÃO

UX-5 — Os alertas de Pós-Organização não têm affordances de ação
Severidade: Média
Esforço: Médio
Problema
A seção "Ações Pendentes de Acompanhamento" do dashboard lista tarefas de follow-up (agradecimento, acompanhamento, etc., com cliente e data), mas cada card se apresenta como informação estática — não há nenhuma ação óbvia de "marcar como concluído", "enviar mensagem" ou "adiar" no card.
Por que importa
Este é o melhor recurso de retenção do produto, mas ele para no lembrar em vez de viabilizar a ação. O usuário ainda precisa sair do sistema para agir.
Impacto no negócio
Um diferencial entrega apenas metade do seu valor; reduz a aderência (stickiness) e a sensação de que "esta ferramenta toca o meu negócio", percepção que impulsiona a retenção.
Solução recomendada
Adicionar uma ação de um toque por card, por exemplo:
•	Enviar WhatsApp com mensagem sugerida pré-preenchida;
•	Concluir;
•	Adiar.
Os números de telefone já estão cadastrados no sistema — utilizar deep links via wa.me.
Melhor prática
Ferramentas de CRM modernas permitem concluir, reagendar ou executar tarefas diretamente da fila, sem obrigar o usuário a trocar de contexto.
________________________________________
________________________________________
________________________________________
UI-3 — Ausência de layout responsivo para dispositivos móveis
Severidade: Alta
Esforço: Alto
Problema
Ao reduzir a viewport para 390px de largura (largura típica de smartphones), o sistema manteve o menu lateral fixo e as proporções de desktop, sem adaptação para mobile.
Por que importa
Personal organizers trabalham frequentemente no local do cliente. O contexto mobile é primário, não secundário.
Um layout exclusivamente desktop em um celular implica:
•	Zoom constante;
•	Rolagem horizontal;
•	Perda de produtividade durante o atendimento.
Impacto no negócio
Uma parcela significativa do uso real do produto fica degradada, tornando-se um dos principais fatores de abandono ou churn.
Solução recomendada
Implementar breakpoints responsivos para:
•	Colapsar o menu lateral em:
o	Menu hambúrguer; ou
o	Navegação inferior (bottom navigation).
•	Empilhar colunas do Kanban verticalmente;
•	Transformar tabelas em cards no mobile;
•	Tratar dispositivos móveis como plataforma de primeira classe.
Melhor prática
Ferramentas modernas de CRM e produtividade convertem pipelines e kanbans em navegação horizontal por swipe ou coluna única em dispositivos móveis.
________________________________________
UI-4 — Linguagem visual inconsistente e excessivamente baseada em emojis
Severidade: Média
Esforço: Médio
Problema
A navegação depende fortemente de emojis do sistema operacional como mecanismo de iconografia:
•	👥
•	📝
•	🛒
•	💰
•	📋
•	📈
•	🚪
Esses elementos:
•	Renderizam de maneira diferente entre plataformas;
•	Não podem ser tematizados adequadamente;
•	Não seguem escalas consistentes;
•	Podem colidir com o texto, como observado no problema UI-1.
Por que importa
Emojis como ícones transmitem improvisação e reduzem a percepção de profissionalismo do produto.
Impacto no negócio
Redução da maturidade visual percebida e da sensação de produto premium, limitando inclusive o potencial de precificação.
Solução recomendada
Adotar uma biblioteca consistente de ícones SVG, como:
•	Lucide;
•	Heroicons;
•	Phosphor Icons.
Definir tokens de:
•	Tamanho;
•	Cor;
•	Peso visual;
•	Espaçamento.
________________________________________
UI-5 — Inconsistência de hierarquia visual e espaçamento entre módulos
Severidade: Média
Esforço: Médio
Problema
Tamanhos de títulos, espaçamentos e estilos de cards variam entre os módulos do sistema.
Exemplos:
•	Dashboard;
•	Propostas;
•	Financeiro.
Além disso, a citação inspiracional posicionada entre o cabeçalho e os KPIs compete visualmente com as informações realmente prioritárias da tela.
Por que importa
Inconsistências visuais sinalizam ausência de um design system e aumentam a carga cognitiva, obrigando o usuário a reaprender padrões a cada página.
Impacto no negócio
Percepção acumulada de falta de acabamento e redução da velocidade de escaneamento das interfaces.
Solução recomendada
Estabelecer um conjunto mínimo de design tokens, incluindo:
•	Escala tipográfica;
•	Escala de espaçamento;
•	Componente único de card;
•	Estilos padronizados de botão;
•	Hierarquia consistente de títulos.
Além disso:
•	Reposicionar ou suavizar a presença da citação motivacional;
•	Garantir que os KPIs permaneçam como o principal ponto focal do dashboard.


