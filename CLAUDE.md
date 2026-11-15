# Planner Organiza: API (FastAPI) e sistema web (Streamlit)

Responda em português, passo a passo e sem jargão. O README.md tem arquitetura, rotas e variáveis em detalhe.

## Publicação (Render)
- API `plannerorganiza-api.onrender.com` (`api/router.py`): publica sozinha a cada push na `main`.
- Web `app.plannerorganiza.com.br` (`app.py`, `pages/`): deploy **manual** (Render > PlannerOrganizer >
  Manual Deploy). Avise a usuária sempre que mudar algo da web.
- Trabalhe na branch da sessão e leve para a `main` com os testes passando.

## Testes
- `DATABASE_URL=postgresql://postgres@127.0.0.1:5499/sinal_teste python -m pytest -q tests`
- O Postgres de teste precisa de SSL ligado e do schema criado por `utils.database.Base.metadata.create_all`.
- Dependências: `requirements.txt` (o pacote `sib-api-v3-sdk` falha no pip; instale sem ele).

## Assinatura: um plano por conta, três canais
- `perfis.plano` + `perfis.assinatura_origem` (`stripe` | `google` | `apple`) + `assinatura_expira_em`.
  Um canal só derruba o plano que ele mesmo deu (`utils/assinatura.py`).
- Stripe (site): links de pagamento mensal R$ 39,90 e anual R$ 297, **sem códigos promocionais**; o código
  ORGANIZA está inativo (cupom 49hDR0oH mantido). Conta Stripe "Coruja Labs".
- Lojas pelo RevenueCat (projeto `proj1aebd2c2`, acesso `pro`):
  - `POST /webhook/revenuecat`: confere o Authorization com `REVENUECAT_WEBHOOK_AUTH` (aceita com ou sem
    "Bearer "). O evento TEST responde `{"status":"teste"}`.
  - `POST /assinatura/sincronizar`: consulta o RevenueCat (API v1) com `REVENUECAT_SECRET_KEY`.
  - Google: notificações em tempo real ligadas pelo tópico `projects/planner-organizer-68a23/topics/play-notificacoes`.
- Web: topo do menu mostra o e-mail conectado e o selo do plano; em Plano e cobrança o botão de gerenciar mostra o
  símbolo da loja (`pages/plano.py`).

## Avisos no celular
- `/tarefas/lembretes-diarios` (GitHub Actions `lembretes-diarios.yml`, 08h07 Brasília, segredo `TAREFAS_CHAVE`):
  um resumo por celular por dia (`push_tokens.ultimo_resumo`), abre o Início ao tocar.

## PDFs de proposta
- Proposta Comercial sai como "Proposta de Serviço"; todos os PDFs mostram `propostas.numero` (não o id interno) e
  o status legível (`utils/proposta_status.label_for`).

## Pendências (15/11/2026)
- Deploy manual da web no Render para levar o topo com conta/plano e o ícone da loja.
- Recebimento da Apple: conta Itaú em BRL exige cadastro na StoneX; alternativa: conta USD da Wise no nome do titular.
