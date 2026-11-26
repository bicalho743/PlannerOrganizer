# Briefing comum: redesenho do site do Planner Organiza (Streamlit)

Repositório: /home/user/PlannerOrganizer (site em Streamlit; `app.py` faz o roteamento, telas em `pages/`).
A dona aprovou protótipos em HTML/PNG em /tmp/claude-0/-home-user/ac9bca1e-440f-585e-897d-28876c56361c/scratchpad/prototipo/
(cada tela tem `<nome>.html` e `<nome>.png`; `comum.css`, `base.css`, `side.css`, `wiz.css` são os estilos deles).
Ela pediu: "deve ser feito igual aos protótipos". Leia o PNG E o HTML da sua tela antes de começar.

## Já pronto, use como referência (não edite)
- `pages/dashboard.py` (Início) e `pages/agenda.py` (Agenda): já seguem os protótipos inicio2/agenda2. Copie dali o jeito
  de fazer cabeçalho (eyebrow dourado + título serifado + traço dourado + subtítulo + botão dourado à direita em
  `st.container(key="cta_...")`), cartões brancos (borda #E7E2D6, raio 14-16px), seções (`.ini-secao`), cartões
  clicáveis (`utils.ui.cartao_clicavel`), botões só-texto dourados, CSS responsivo.
- `utils/visual.py`: `hoje()` (horário de Brasília: use sempre, nunca `datetime.now().date()`), `saudacao()`, `esc()`
  (escape de HTML: use em todo nome/título vindo do banco), `pilula(status)` + `CSS_PILULA` (escala aprovada de situação
  da proposta: ○ Em aberto contorno dourado · ● Aprovada dourado · ▶ Em execução azul-marinho · ✓ Concluída verde),
  `icone(nome)` (ícones de traço SVG; NÃO use emoji nem símbolos de texto como ↻ ✉ 🎂 como ícone).
- `utils/precificacao.py`: `orcamento_completo(...)`, `TIPOS_SERVICO`, `CAIXAS_POR_COMODO`, `materiais(p)`,
  `MATERIAIS_PADRAO`, `caixas_por_area`, mais os cálculos antigos (`hora_minima`, `hora_sugerida`, `preco_projeto`,
  `AMBIENTES_PADRAO`, `COMPLEXIDADE`, `PADROES`). Parâmetros da organizer: `st.session_state.db.get_precificacao()` /
  `salvar_precificacao(dict)` (JSON em perfis.precificacao).
- Cores: navy #0D1B2A, dourado #C9A84C (escuro #9C7A22 / #B8943D), dourado claro #F6EDD3, fundo #F7F5F0,
  texto secundário #5B6B80, verde #2F6B4F (claro #E3F1E8), vermelho #9B2C2C (claro #FBE9E7). Um só destaque: dourado.

## Regras
- Só edite os arquivos da SUA tarefa (listados no seu pedido). NÃO edite `app.py`, `.streamlit/style.css`,
  `utils/visual.py`, `utils/database.py`, `utils/precificacao.py`, nem telas de outras tarefas: outras pessoas estão
  editando ao mesmo tempo. Se precisar de ícone novo, defina SVG no seu próprio arquivo. Se precisar de método novo no
  banco, crie em um módulo novo seu (ex.: `utils/<sua_tela>_dados.py`) usando `st.session_state.db` ou
  `utils.database.engine`, ou relate no fim.
- Mantenha TODA a função que a tela tem hoje (formulários, editar, excluir, diálogos, PDFs, WhatsApp, integrações com
  Financeiro/Pós-organização etc.). O protótipo muda a aparência e a organização; não remova recurso sem dizer.
  Não invente dado que o sistema não tem (se o protótipo mostra algo que não existe no banco, faça com o que existe
  ou deixe de fora e relate).
- Textos em português do Brasil, simples. Sem travessão longo (—) em textos novos da tela.
- Nada de git commit/push. Não publique nada.
- Escape com `esc()` tudo que vier do banco dentro de HTML.

## Como testar visualmente (obrigatório)
1. Banco de teste: Postgres local na porta 5499. Se não responder (`pg_isready -h 127.0.0.1 -p 5499`), inicie:
   `PGBIN=$(ls -d /usr/lib/postgresql/*/bin | tail -1); cd /var/tmp/pgteste/data && su postgres -c "setsid nohup $PGBIN/postgres -D /var/tmp/pgteste/data -p 5499 -c ssl=on -c ssl_cert_file=server.crt -c ssl_key_file=server.key > /var/tmp/pgteste/log.txt 2>&1 &"`
2. Página de teste que abre qualquer tela já logada:
   /tmp/claude-0/-home-user/ac9bca1e-440f-585e-897d-28876c56361c/scratchpad/harness/tela_geral.py
   Rode na SUA porta: `cd /home/user/PlannerOrganizer && REPO=$PWD DATABASE_URL=postgresql://postgres@127.0.0.1:5499/sinal_teste setsid nohup streamlit run <caminho>/tela_geral.py --server.port <SUA_PORTA> --server.headless true > <sua_pasta>/st.log 2>&1 &`
   Abra `http://localhost:<SUA_PORTA>/?t=<tela>&u=<SEU_USUARIO>`. O Streamlit guarda o código antigo dos módulos:
   depois de editar, mate e suba de novo (`pkill -f "streamlit run.*<SUA_PORTA>"`).
3. Crie dados de teste para o SEU usuário (id próprio, listado no seu pedido) com `utils.database.Database(usuario_id=...)`
   (add_cliente, add_proposta(status em minúsculas: em_aberto, aprovada, em_execucao, finalizada, recusada;
   gerar_transacoes_automaticas=False), update_proposta, add_transacao, salvar_compromisso, create_post_organization...).
   Rode scripts com `DATABASE_URL=postgresql://postgres@127.0.0.1:5499/sinal_teste python <script>` a partir do repo.
4. Fotos com Playwright (node; `require('playwright')` já funciona, chromium.launch() sem opções). O Streamlit rola dentro
   de um contêiner, então `fullPage` não pega tudo: use viewport alta (ex.: 1440×2200). Espere ~7 s após abrir.
   Tire fotos em 1440, 1180 e 390 de largura e COMPARE com o PNG do protótipo, lado a lado. Corrija até ficar igual.
   Verifique erros: `page.locator('[data-testid="stException"]')`.
5. Rode os testes relacionados: `cd /home/user/PlannerOrganizer && DATABASE_URL=postgresql://postgres@127.0.0.1:5499/sinal_teste python -m pytest -q tests/<arquivos>`.

## Armadilhas do Streamlit já descobertas
- No celular (<640px) o Streamlit põe `flex-direction: column` nas linhas de colunas. Se você forçar `flex-wrap: wrap`,
  force também `flex-direction: row !important`, senão a segunda coluna vai para fora da tela à direita.
- Para mirar uma linha de colunas, embrulhe em `st.container(key="x")` e use
  `.st-key-x > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"]` (> [data-testid="stColumn"]).
- Cartão que precisa reorganizar quando fica estreito: `container-type: inline-size` + `@container (max-width: ...)`.
- `st.markdown` com `<style>` e HTML: use chamadas separadas. `:material/xxx:` não funciona dentro de HTML cru.
- Pills/segmented: o selecionado tem `aria-checked="true"`; os botões são irmãos (`button:nth-of-type(n)`).
- Botão só-texto: `type="tertiary"`; o style.css global pinta tertiary de cinza, então sobrescreva com seletor do seu key.
- Container com chave `cta_...` vira botão dourado (style.css). `type="primary"` = azul-marinho.
- Navegação: `st.session_state.current_page = "<Nome>"` + `st.rerun()`. Nomes: Dashboard, Agenda, Clientes, Propostas,
  Precificacao, Vendas, Financeiro, PosOrganizacao, Relatórios, Perfil, Plano.

## Entrega (sua resposta final)
- Arquivos alterados/criados.
- Lista do que ficou igual ao protótipo e do que ficou diferente, com o motivo.
- Caminhos das fotos finais (1440, 1180, 390) e das fotos do protótipo para comparação.
- Resultado dos testes que você rodou.
