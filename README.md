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

---

## Análise Comparativa do Ecossistema (Web & Mobile)

### 1. Visão Geral da Arquitetura

O sistema é desenhado de forma híbrida: a aplicação web também atua como servidor central de APIs (Backend) para o aplicativo móvel. Ambos se conectam a uma única fonte da verdade (banco de dados PostgreSQL e autenticação via Firebase).

```mermaid
graph TD
    %% Nós de Clientes
    subgraph Frontend_Clients ["Clientes (Interfaces)"]
        Web["Interface Web (Streamlit)<br/>C:\\APLICATIVOS\\PlannerOrganizer"]
        App["Aplicativo Android (React Native / Expo)<br/>C:\\APLICATIVOS\\planner-app"]
    end

    %% Nós de Backend & Dados
    subgraph Backend_Services ["Servidores & Serviços de Dados"]
        API["FastAPI Backend (api/router.py)<br/>Hospedado no Render"]
        DB[(Banco de Dados PostgreSQL)]
        Firebase["Firebase Auth (Multi-Tenant)"]
    end

    %% Fluxos de Conexão
    Web -->|Leitura/Escrita Direta| DB
    Web -->|Autenticação| Firebase
    App -->|Chamadas REST com Token Bearer| API
    App -->|Autenticação Direct| Firebase
    API -->|Consulta SQL (SQLAlchemy)| DB
    API -->|Validação de Token| Firebase
```

---

### 2. Análise dos Projetos

#### 2.1. Backend & Web App: `PlannerOrganizer`
* **Local:** `c:\APLICATIVOS\PlannerOrganizer`
* **Tecnologias:** Python 3.11, Streamlit, FastAPI, SQLAlchemy, PostgreSQL.
* **Função Dupla:**
  1. **Interface Administrativa (Streamlit):** Interface administrativa web voltada para desktops e navegadores.
  2. **Servidor API (FastAPI em `api/router.py`):** Expõe as rotas REST necessárias para o aplicativo móvel consumir e manipular dados.
* **Segurança e Isolamento Multi-Tenant:**
  * O FastAPI intercepta as requisições do aplicativo móvel usando a função `verify_firebase_token`. Ele recebe o cabeçalho `Authorization: Bearer <ID_TOKEN>`, valida com a API do Google Firebase e extrai o `localId` (UID) do usuário.
  * Esse UID é repassado ao inicializar a classe `Database(usuario_id=uid)` em `utils/database.py`, garantindo que todas as consultas SQL executadas filtrem os registros correspondentes apenas ao usuário logado.

#### 2.2. Aplicativo Móvel: `planner-app`
* **Local:** `c:\APLICATIVOS\planner-app`
* **Tecnologias:** React Native, Expo 54 (Expo SDK 54, React 19, React Native 0.81), Expo Router, Axios para requisições.
* **API Utilizada:** `https://plannerorganiza-api.onrender.com` (API hospedada no Render do Web App).
* **Autenticação:** Login direto no Firebase no dispositivo móvel (`src/services/firebase.ts`). O token ID JWT do Firebase é obtido localmente no aplicativo e anexado a cada chamada de API REST via interceptador do Axios em `src/services/api.ts`.

---

### 3. Mapeamento de Funcionalidades e Telas

As funcionalidades do Web App (Streamlit) encontram reflexo direto nas telas nativas do aplicativo mobile (Expo) através de chamadas na API FastAPI:

| Funcionalidade | Página Web (Streamlit) | Tela Mobile (React Native / Expo) | Endpoint da API (`api/router.py`) |
| :--- | :--- | :--- | :--- |
| **Dashboard** | `pages/dashboard.py` | `src/screens/DashboardScreen.tsx` | `GET /dashboard` |
| **Clientes** | `pages/cadastros.py` (Aba Clientes) | `src/screens/ClientesScreen.tsx` | `GET`, `POST`, `PUT`, `DELETE /clientes` |
| **Cadastros Gerais** | `pages/cadastros.py` (Fornecedores/Parceiros/Produtos) | `src/screens/CadastrosScreen.tsx` | `GET /fornecedores`, `/assistentes`, `/parceiros`, `/produtos` |
| **Propostas** | `pages/propostas_unificado.py` | `src/screens/PropostasScreen.tsx` | `GET`, `POST`, `PUT /propostas` |
| **Execução de Proposta** | `pages/propostas_unificado.py` (Seção Itens) | `src/screens/PropostaExecucaoScreen.tsx` | `GET/POST /propostas/{id}/produtos`, `/acrescimos` |
| **Vendas** | `pages/vendas.py` | `src/screens/VendasScreen.tsx` | `GET`, `POST /vendas` |
| **Financeiro** | `pages/financeiro.py` | `src/screens/FinanceiroScreen.tsx` | `GET`, `POST`, `PUT`, `DELETE /financeiro` |
| **Pós-Organização** | `pages/pos_organizacao.py` | `src/screens/PosOrganizacaoScreen.tsx` | `GET /pos-organizacao`, `GET/PUT /pos-organizacao/acoes` |
| **Relatórios** | `pages/relatorios.py` | `src/screens/RelatoriosScreen.tsx` | `GET /relatorios` |
| **PDFs** | `pages/relatorios.py` (Botões de Download) | `src/screens/PDFScreen.tsx` | Geração remota de PDF pelo backend com visualização em webview local. |
| **Perfil & Planos** | `pages/perfil.py` e `pages/planos.py` | `src/screens/PerfilScreen.tsx` | `GET /perfil` |
