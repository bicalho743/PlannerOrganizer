# Planner Organiza

Sistema de gestão para **personal organizers**: precificação, propostas com a marca da organizer, agenda,
retornos às clientes (pós-organização), financeiro, impostos do MEI/Simples, vendas e relatórios.

Este repositório tem o **sistema web** (Streamlit) e a **API do app de celular** (FastAPI). Os dois usam o mesmo
banco e as mesmas regras (`utils/`): uma correção vale para a web e para o app ao mesmo tempo.

> Atualizado em novembro de 2026. As pendências estão no fim deste arquivo.

---

## 1. O ecossistema

| Parte | Tecnologia | Onde roda | Repositório |
|---|---|---|---|
| Sistema web | Python, Streamlit | Render: `PlannerOrganizer`, em **app.plannerorganiza.com.br** | este |
| API do app | Python, FastAPI (`api/router.py`) | Render: `plannerorganiza-api.onrender.com` | este |
| Banco de dados | PostgreSQL 16 | Render: `PlannerOrganizer_db` (plano Basic 256 MB) | — |
| App Android e iPhone | Expo SDK 54, React Native 0.81, TypeScript | Google Play e App Store (build pelo EAS) | `bicalho743/planner-app` |
| Página de vendas | React + Vite + Express | Render: `Pagina_de_vendas_planner`, em **plannerorganiza.com.br** e www | `bicalho743/LandingPage_Planner` |
| Site da Tâmara | HTML estático | Locaweb (FTP por GitHub Action) | `bicalho743/tamara-site` |

```
                  Usuárias
   ┌────────────────┬───────────────────┬──────────────────┐
 App celular      Sistema web          Página de vendas    Site da Tâmara
 (Expo)           (Streamlit)          (React)             (estático)
   │ token          │                    │ "Começar grátis" ──► sistema web
   ▼ Firebase       │
 API (FastAPI)      │
   └──────┬─────────┘
          ▼
   PostgreSQL (um banco, as duas pontas)

 Firebase Auth (login) · Stripe (assinatura) · Brevo (e-mail) · Expo Push (avisos)
 GitHub Actions: lembretes diários e cópia semanal do banco
```

Domínios (DNS na Locaweb): `plannerorganiza.com.br` e `www` → página de vendas; `app.` → sistema web;
`promo.` → redireciona (301) para o domínio principal, mantendo os parâmetros dos anúncios.

## 2. Como as partes funcionam

### Login
- **Firebase Auth**: e-mail e senha, Google e Apple (iPhone). A mesma conta vale no celular e na web.
- O app manda o token do Firebase em toda chamada. A API confere com o Firebase (`accounts:lookup`) e guarda a
  resposta por 5 minutos (`verify_firebase_token`).

### Dados de cada usuária
- Toda tabela tem `usuario_id` (o UID do Firebase).
- `utils/database.py` acrescenta **"só desta usuária"** em toda consulta do SQLAlchemy (evento `do_orm_execute`
  com `with_loader_criteria`): mesmo que uma tela esqueça o filtro, ninguém vê dados de outra conta.
- Colunas e tabelas novas são criadas sozinhas quando o sistema sobe (`ALTER TABLE ... IF NOT EXISTS` em
  `utils/database.py`).

### Assinatura e teste grátis
- A conta tem **um plano só**, assinado em um de três lugares (`perfis.assinatura_origem`, em `utils/assinatura.py`):
  - **site**, no Stripe (links de pagamento mensal e anual em `pages/perfil.py`, com o UID em `client_reference_id`);
  - **app Android**, pelo Google Play; **app iPhone**, pela App Store. As duas lojas passam pelo **RevenueCat**
    (o app entra com o UID do Firebase; acesso `pro`). O RevenueCat avisa a API em `/webhook/revenuecat`
    (cabeçalho Authorization = `REVENUECAT_WEBHOOK_AUTH`) e o app chama `/assinatura/sincronizar` logo depois de
    comprar (consulta com `REVENUECAT_SECRET_KEY`), para liberar na hora.
  - Cada canal só tira o acesso que ele mesmo deu: a assinatura antiga do site que termina não bloqueia quem passou a
    pagar pelo celular. Cada assinatura é **gerenciada onde foi feita** (Plano e cobrança mostra o caminho certo).
  - Preço igual nos três: mensal R$ 39,90 e anual R$ 297. Sem cupom.
- O Stripe avisa a API em `/webhook/stripe`:
  - `checkout.session.completed`: ativa o plano pela conta do UID e guarda o **código do cliente** do Stripe
    (`perfis.stripe_customer_id`);
  - `invoice.paid`, `customer.subscription.updated`, `customer.subscription.deleted`: acham a conta **pelo código do
    cliente** (o e-mail é só o último recurso). Pagar com outro e-mail não quebra mais renovação nem cancelamento.
- **Teste grátis de 7 dias** (`utils/trial.py`). Depois, sem assinatura, a conta fica em **modo consulta**: vê tudo,
  mas não grava nem gera PDF (a API responde **402**; a web usa `utils/somente_leitura.py`).
- `TRIAL_ISENTOS` (variável no Render): e-mails sempre liberados (dono e conta de revisão da Apple).
- **Excluir conta** (`POST /conta/excluir`): cancela as assinaturas no Stripe e apaga os dados de todas as tabelas
  com `usuario_id`; o app apaga o login no Firebase. Exigência da App Store e da Google Play.

### PDFs
- Gerados **na API** com ReportLab (`utils/pdf_generator_v2.py`), com o logo e as cores do perfil:
  proposta comercial, fechamento para a cliente, relatório interno, produtos e fornecedores, venda.

### Avisos no celular
- O app registra o token do celular (`POST /push/token`) e remove ao sair da conta (`/push/remover`).
- Todo dia às **08:07 (Brasília)** o GitHub Actions (`.github/workflows/lembretes-diarios.yml`) chama
  `POST /tarefas/lembretes-diarios` (protegida por `TAREFAS_CHAVE`). A API monta o "Para fazer" de cada conta com
  a mesma função da tela Início (`_montar_inicio`) e envia um resumo pelo **Expo Push**: aniversários, retornos de
  cliente, valores a receber e contas a pagar do dia. Sem nada para hoje, não envia. Contas em modo consulta
  ficam de fora; celulares desinstalados saem da lista sozinhos.

### Aniversário das clientes
- Só **dia e mês**, guardado como `14/jun`. `utils/agenda.py` (`normalizar_aniversario`, `dia_mes_aniversario`)
  entende `1406`, `14/06`, `14/jun`, `14/06/1990` e recusa datas impossíveis. Web, API e tela Início usam a mesma leitura.

### Cópia de segurança do banco
- O Render guarda os últimos dias do banco (recuperação "ponto no tempo" nos planos pagos), mas **não guarda nada
  se o banco for apagado**.
- Cópia **semanal** fora do Render: `.github/workflows/backup-banco.yml` (domingo, 03:17), `pg_dump`
  criptografado (AES-256), guardado 90 dias nos artefatos do GitHub. Como restaurar está no próprio arquivo.

## 3. Funcionalidades

| Área | O que faz |
|---|---|
| Início | lucro do mês, a receber e a pagar, conversão de propostas; "Para fazer" com WhatsApp pronto, Feito e Adiar; propostas em andamento; aniversariantes do mês |
| Propostas | criar, itens (produtos, fornecedores, assistentes, cômodos), acréscimos, status (em aberto → aprovada → em execução → finalizada/recusada), sinal na aprovação, finalizar o projeto, PDFs |
| Agenda | semana ou mês: compromissos, serviços, retornos, aniversários e vencimentos; "Recebi" lança no financeiro |
| Pós-organização | retornos criados ao finalizar a proposta (agradecimento, acompanhamento, ajuste fino, feedback), com WhatsApp, concluir e adiar |
| Financeiro | receitas e despesas, a receber e a pagar, filtros e status |
| Impostos | MEI (DAS mês a mês, limite anual, DASN-SIMEI), Simples (alíquota da contadora), outros regimes |
| Precificação | hora mínima e sugerida a partir da renda desejada e dos custos; preço de um projeto por ambiente, complexidade e assistentes |
| Cadastros | clientes (com origem e aniversário), fornecedores, parceiros, assistentes e produtos |
| Vendas | venda de produtos do catálogo, forma de pagamento, PDF |
| Relatórios | propostas por status, comparativo mensal, categorias de receita, origem das clientes, ticket médio |
| Perfil e marca | dados da empresa, logo e cores (web), textos padrão dos PDFs, excluir conta |
| Só na web | assinatura e portal do Stripe, envio do logo, importação de clientes por planilha, manual em PDF |

## 4. Rotas da API (`api/router.py`)

| Grupo | Rotas |
|---|---|
| Conta | `GET/PUT /perfil`, `POST /conta/excluir`, `GET /stripe/portal`, `GET /api/status` |
| Início | `GET /inicio`, `GET /dashboard` |
| Clientes e cadastros | `GET/POST /clientes`, `PUT/DELETE /clientes/{id}`, `GET/POST /fornecedores`, `/parceiros`, `/assistentes`, `GET/POST /produtos`, `PUT /produtos/{id}` |
| Propostas | `GET/POST /propostas`, `PUT /propostas/{id}`, itens em `/propostas/{id}/produtos`, acréscimos em `/propostas/{id}/acrescimos` |
| Agenda | `GET /agenda`, `POST /compromissos`, `PUT/DELETE /compromissos/{id}`, `POST /compromissos/{id}/recebido` |
| Pós-organização | `GET /pos-organizacao`, `GET /pos-organizacao/{id}/acoes`, `PUT /pos-organizacao/acoes/{id}` |
| Financeiro e impostos | `GET/POST /financeiro`, `PUT/DELETE /financeiro/{id}`, `GET /impostos`, `POST /impostos/das`, `PUT /impostos/regime` |
| Precificação | `GET/PUT /precificacao` |
| Vendas | `GET/POST /vendas`, `PUT/DELETE /vendas/{id}`, `GET/PUT /vendas/{id}/itens` |
| PDFs | `/pdf/proposta/{id}/comercial`, `/cliente`, `/interno`, `/produtos`, `/fornecedores`, `/pdf/venda/{id}` |
| Relatórios | `GET /relatorios` |
| Avisos | `POST /push/token`, `POST /push/remover`, `POST /tarefas/lembretes-diarios` |
| Stripe | `POST /webhook/stripe` |

Rotas de gravação e PDFs respondem **402** no modo consulta, exceto perfil, regime de impostos, precificação,
excluir conta, avisos e webhook.

## 5. Estrutura do repositório

```
app.py                 entrada do sistema web (login, menu, páginas)
pages/                 telas da web (dashboard = Início, propostas, agenda, financeiro, plano, perfil...)
api/router.py          API do app (FastAPI)
utils/database.py      acesso ao banco, filtro por usuária, criação de colunas novas
utils/models.py        tabelas (SQLAlchemy)
utils/agenda.py        agenda e aniversários       utils/trial.py        teste grátis e modo consulta
utils/precificacao.py  cálculo de preço            utils/indicadores.py  números da tela Início
utils/pdf_generator_v2.py  PDFs                    utils/proposta_status.py  status das propostas
tests/                 testes (pytest) contra um PostgreSQL de teste
.github/workflows/     lembretes diários e cópia semanal do banco
```

## 6. Variáveis de ambiente (Render)

| Variável | Uso |
|---|---|
| `DATABASE_URL` | banco PostgreSQL |
| `FIREBASE_API_KEY` (e demais `FIREBASE_*`) | login |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | login com Google na web |
| `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` | assinatura |
| `REVENUECAT_WEBHOOK_AUTH`, `REVENUECAT_SECRET_KEY` | assinatura pelas lojas (só na API `plannerorganiza-api`) |
| `TRIAL_ISENTOS` | e-mails sempre liberados, separados por vírgula |
| `TAREFAS_CHAVE` | protege `/tarefas/lembretes-diarios` (o mesmo valor vai como segredo no GitHub) |
| `CORS_ALLOWED_ORIGINS` | origens aceitas pela API |

Segredos do GitHub (Settings → Secrets and variables → Actions): `TAREFAS_CHAVE`, `BACKUP_DATABASE_URL`, `BACKUP_SENHA`.

## 7. Rodar e testar

```bash
pip install -r requirements.txt
export DATABASE_URL=postgresql://usuario@localhost:5432/planner   # banco de teste, nunca o de produção
streamlit run app.py                                   # web
uvicorn api.router:api --port 8000                     # API
python -m pytest -q tests                              # testes
```

## 8. Publicação

- Trabalho no branch de desenvolvimento e envio ao `main` com os testes passando.
- **API**: publica sozinha a cada envio ao `main`.
- **Web**: hoje publica **manualmente** (Render → PlannerOrganizer → Manual Deploy). Ver pendências.
- **App**: `npx eas-cli build --platform android|ios --profile production` no repositório `planner-app`.

---

## Pendências

**Configurações que faltam (o código já está pronto)**
- [ ] **Publicação automática da web**: Render → PlannerOrganizer → Settings → *Auto-Deploy* = *On Commit*, para a web e a API publicarem juntas.
- [ ] **Aviso da manhã**: criar `TAREFAS_CHAVE` (texto longo e aleatório) no Render (plannerorganiza-api) e o mesmo valor como segredo no GitHub; no EAS, enviar a chave FCM V1 do Firebase (Android) e criar a chave de push da Apple no próximo build do iPhone.
- [ ] **Cópia do banco**: segredos `BACKUP_DATABASE_URL` (URL externa do banco no Render) e `BACKUP_SENHA` no GitHub; rodar uma vez em Actions → Backup do banco → *Run workflow* e guardar a senha num lugar seguro.

**Lojas e app**
- [x] App Store: app publicado; página de vendas com o selo da App Store.
- [ ] **Assinatura pelas lojas**: Small Business Program da Apple; contrato de apps pagos e dados bancários/fiscais
      na App Store Connect e no Play Console; produtos `planner_mensal` (R$ 39,90) e `planner_anual` (R$ 297) nas duas
      lojas, sem período grátis; RevenueCat com o acesso `pro` e a oferta `default`; no Render (API),
      `REVENUECAT_WEBHOOK_AUTH` e `REVENUECAT_SECRET_KEY`; no EAS, as chaves públicas do RevenueCat; desativar o cupom
      ORGANIZA nos links de pagamento do Stripe.
- [ ] Android: próximo build com excluir conta, aniversário dia/mês, e-mail sem correção automática, avisos pelo servidor.
- [ ] Logo e cores só podem ser enviados pela web.
- [ ] Tela de login do app ainda no visual antigo (azul-marinho).

**Domínios e marketing**
- [ ] Trocar o link dos anúncios do Meta de `promo.` para o domínio principal e, depois de 1 a 2 semanas, remover `promo` no Render e na Locaweb.
- [ ] Depoimentos reais com autorização (a página mostra "Nossos compromissos" no lugar).
- [ ] Perfil @plannerorganiza no Instagram, conversas da Tâmara e teste de anúncios (ver plano de marketing).

**Produto (próximos passos sugeridos)**
- [ ] Modelos prontos (mensagens de WhatsApp, checklist de visita, contrato).
- [ ] Escola do Planner: aulas curtas da Tâmara dentro do app.
- [ ] Comunidade: validar primeiro fora do app (WhatsApp) antes de construir.
- [ ] Expansão para Portugal (preços em euro no Stripe).

**Técnico**
- [ ] Teste visual antigo `fluxo_inicio` (fora do repositório) espera o mês de outubro.
- [ ] Abrir CNPJ (previsto para abril/2027) e revisar impostos com contador.
