# Planner Organiza: API (FastAPI) e sistema web (Streamlit)

Responda em português, passo a passo e sem jargão. O README.md tem arquitetura, rotas e variáveis em detalhe.

## Publicação (Render)
- API `plannerorganiza-api.onrender.com` (`api/router.py`): publica sozinha a cada push na `main`.
- Web `app.plannerorganiza.com.br` (`app.py`, `pages/`): serviço `PlannerOrganizer`, também **publica sozinha**
  a cada push na `main` (conferido no Render em 16/11/2026, autoDeploy ligado). Avise a usuária sempre que mudar
  algo da web, pois vai ao ar na hora.
- Trabalhe na branch da sessão e leve para a `main` com os testes passando.

## Testes
- `DATABASE_URL=postgresql://postgres@127.0.0.1:5499/sinal_teste python -m pytest -q tests`
- O Postgres de teste precisa de SSL ligado e do schema criado por `utils.database.Base.metadata.create_all`.
- Dependências: `requirements.txt` (o pacote `sib-api-v3-sdk` falha no pip; instale sem ele).

## Assinatura: um plano por conta, três canais
- `perfis.plano` + `perfis.assinatura_origem` (`stripe` | `google` | `apple`) + `assinatura_expira_em`.
  Um canal só derruba o plano que ele mesmo deu (`utils/assinatura.py`).
- Stripe (site): desde 23/11/2026, links de pagamento mensal R$ 59,90, trimestral R$ 149,90 e anual R$ 479,90 (`pages/perfil.py`;
  quem assinou antes segue no preço antigo, e os links antigos de R$ 39,90 e R$ 199,90 seguem ativos só para não quebrar nada), **sem códigos promocionais**; o código
  ORGANIZA está inativo (cupom 49hDR0oH mantido). Conta Stripe "Coruja Labs".
- Lojas pelo RevenueCat (projeto `proj1aebd2c2`, acesso `pro`):
  - `POST /webhook/revenuecat`: confere o Authorization com `REVENUECAT_WEBHOOK_AUTH` (aceita com ou sem
    "Bearer "). O evento TEST responde `{"status":"teste"}`.
  - `POST /assinatura/sincronizar`: consulta o RevenueCat (API v1) com `REVENUECAT_SECRET_KEY`.
  - Google: notificações em tempo real ligadas pelo tópico `projects/planner-organizer-68a23/topics/play-notificacoes`.
- Web: topo do menu mostra o e-mail conectado e o selo do plano; em Plano e cobrança o botão de gerenciar mostra o
  símbolo da loja (`pages/plano.py`).

## Programa de afiliadas (24/11/2026)
- `utils/afiliados.py` + `pages/afiliadas.py` (menu "Indique e ganhe"). 25% do valor líquido de cada pagamento da
  indicada por 12 meses (Stripe, App Store e Google Play), liberado 30 dias depois, Pix mensal manual a partir de R$ 50
  (era 30% até 24/11/2026). A indicada ganha 10% no anual: site com o link Stripe `STRIPE_CHECKOUT_ANUAL_INDICADA`
  (R$ 429,90, price_1UfL8zIrr8YI3Ljjd7DzXHCl) em Plano e cobrança; nos apps, pendente para a 1.0.20 (produto/oferta
  própria + RevenueCat). Um CPF e uma chave Pix por inscrição. Página pública e termos: plannerorganiza.com.br/indique e /indique/termos.
- Funil de vendas (`utils/funil.py`, `pages/funil.py`, menu só para ADMIN_EMAILS): eventos conta_criada, primeiro_pdf e
  planos_vistos em `eventos_funil`; o resto vem das tabelas. Conta do app ganha perfil na API (`garantir_perfil`).
- Vínculo: link `plannerorganiza.com.br/?ref=CODIGO` (a landing guarda o `ref`, o site liga ao criar a conta) ou o código
  em "Tenho um convite" (`/convites/resgatar` aceita código de afiliada; o teste continua de 7 dias). Sem autoindicação.
- Comissão: Stripe `invoice.paid` (estorno em `charge.refunded`); lojas em `utils/assinatura._comissao_loja`
  (INITIAL_PURCHASE/RENEWAL em BRL; CANCELLATION por reembolso estorna).
- Administração (aprovar, Pix do mês, marcar pago) aparece para os e-mails em `ADMIN_EMAILS` (variável no Render).

## Avisos no celular
- `/tarefas/lembretes-diarios` (GitHub Actions `lembretes-diarios.yml`, 08h07 Brasília, segredo `TAREFAS_CHAVE`):
  um resumo por celular por dia (`push_tokens.ultimo_resumo`), abre o Início ao tocar.

## Onboarding (igual ao do app 1.0.16)
- `perfis.onboarding` (JSON: tempo, dores, formal, origem, passos ativo|fechado); API `GET/PUT /onboarding`.
- Web (`utils/onboarding_web.py`): conta nova sem resposta vê a janela de perguntas (depois vem o tutorial rápido);
  Início mostra os 5 Primeiros passos do app (o 3º é "Receba os avisos no celular", feito quando há push_tokens).
- Tutorial rápido não abre sozinho para conta que já tem proposta (`utils/tour.py`).

## PDFs (desenho novo, 25/11/2026)
- Proposta Comercial sai como "Proposta de Serviço"; todos os PDFs mostram `propostas.numero` (não o id interno) e
  o status legível (`utils/proposta_status.label_for`).
- Um só desenho, na cor da marca de cada conta (versão legível por `utils.pdf_proposta.cores_legiveis`): classe `Doc` em
  `utils/pdf_docs.py` (fechamento, interno, fornecedores, venda/produtos) e `utils/pdf_proposta.gerar_pdf_proposta`.
  `utils/pdf_generator_v2.py` só repassa (site e API usam as mesmas funções, então o app recebe o desenho novo sem build).
  Descrições antigas passam por `pdf_docs.limpar_texto` / `itens_da_descricao` (lista vira etiquetas de ambientes).
- Relatório do negócio: contas em `utils/relatorio_negocio.py` (tela Relatórios do site e API `GET /pdf/relatorio?periodo=`,
  usado pelo app desde a 1.0.20); PDF em `utils/relatorio_pdf.py`.

## Desenho novo do site (25/11/2026)
- Todas as telas seguem os protótipos aprovados (página: https://claude.ai/artifact/NeXx2Tpw2XXYVqY9CkwkUt). Peças comuns em
  `utils/visual.py`: `hoje()` (Brasília), `pilula(status)` (○ em aberto, ● aprovada, ▶ em execução, ✓ concluída), `icone()`
  (traço SVG, sem emoji), `icone_whatsapp()` (todo botão que abre o WhatsApp mostra o símbolo), `esc()`.
- Orçamento único em `utils/precificacao.orcamento_completo` (Precificação > Preço de um projeto e Nova proposta em 4 passos,
  `utils/nova_proposta.py`); materiais da organizer em `perfis.precificacao["materiais"]`. Precificação → Nova proposta pela
  chave `nova_proposta_prefill`; Clientes/Pós/Agenda escolhem a cliente com `nova_proposta_cliente_id`.
- "Colocar minha marca" saiu do Início: fica no Perfil e no passo 4 da Nova proposta. Pós-organização só marca "Enviada".
- Tarefas únicas no banco: `utils/renumerar.tarefas_unicas` (tabela `tarefas_unicas`), rodam no 1º `Database()` do processo.

## Pendências (15/11/2026)
- Recebimento da Apple: conta Itaú em BRL exige cadastro na StoneX; alternativa: conta USD da Wise no nome do titular.
