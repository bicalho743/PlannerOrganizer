# Planner Organizer - Sistema de Gestão

## Overview
Sistema de gestão avançado para profissionais brasileiros com interface Streamlit, autenticação Firebase, banco PostgreSQL e funcionalidades de propostas, clientes e relatórios.

## Tecnologias Principais
- Streamlit (interface web)
- FastAPI (backend services)
- PostgreSQL com SQLAlchemy ORM
- Firebase Authentication
- Google Analytics
- Design responsivo mobile-first

## User Preferences
- Todas as respostas devem ser em português
- Preferência por componentes Streamlit nativos (st.expander, st.write)
- Correções de interface devem manter funcionalidade original
- Texto deve ser sempre visível e legível

## Project Architecture

### Estrutura Principal
- `app.py` - Aplicação principal
- `pages/` - Páginas modulares do sistema
- `utils/` - Utilitários e helpers
- `.streamlit/style.css` - Estilos customizados
- `api/` - Serviços FastAPI

### Módulos Principais
- Dashboard - Visão geral com propostas em aberto
- Propostas - Gestão completa de propostas
- Clientes - Cadastro e gestão de clientes
- Vendas - Controle de vendas
- Financeiro - Relatórios financeiros

## Recent Changes

### 2025-07-25
- **DIAGNOSTICADO**: Problema crítico - vendas geradas automaticamente de propostas não salvavam itens
- **IDENTIFICADO**: Função `_registrar_venda_produtos` estava criando itens sem campo `usuario_id` 
- **CORRIGIDO**: Adicionado `usuario_id` obrigatório nos ItemVenda para manter multi-tenancy
- **CORRIGIDO**: Método get_itens_venda para tratar produtos sem preço_custo usando getattr()
- **CORRIGIDO**: Selectbox de vendas com visibilidade de texto e formato "ID - Cliente (Data)"
- **REMOVIDO**: Input manual para ID de venda - interface mais limpa com apenas selectbox
- **IMPLEMENTADO**: Botões de ação (EDITAR, GERAR, EXCLUIR) aparecem para todas as vendas
- **DESCOBERTO**: Vendas manuais (25, 29, 31, 32) têm itens, vendas automáticas (14, 19-23, 33) não tinham
- **CORRIGIDO**: Sistema agora criará corretamente itens para futuras vendas automáticas de propostas
- **CORRIGIDO**: Loop infinito "Your app is starting" removendo st.rerun() desnecessários
- **REMOVIDO**: st.rerun() de login, navegação, logout e modais que causavam loops
- **CORRIGIDO**: Selectbox de vendas com CSS robusto para visibilidade perfeita do texto
- **APLICADO**: Mesmo padrão CSS de outros selectboxes funcionais para módulo vendas
- **CORRIGIDO**: Problema de login duplo - adicionado refresh automático após autenticação
- **REMOVIDO**: JavaScript de refresh automático que causava loop no preview
- **CORRIGIDO**: Lógica de transição pós-login sem refresh forçado
- **MELHORADO**: Sistema define Dashboard automaticamente após autenticação bem-sucedida
- **IMPLEMENTADO**: Correção extrema para selectbox invisível com JavaScript e CSS força absoluta
- **ADICIONADO**: Borda visível e múltiplas tentativas de correção para garantir visibilidade
- **REMOVIDO**: JavaScript global que causava loop infinito "Your app is starting"
- **CORRIGIDO**: CSS malformado no app.py que impedia carregamento normal
- **ESTABILIZADO**: Aplicação deve carregar sem loops após remoção do JavaScript problemático
- **CORRIGIDO**: Login agora usa st.rerun() único para completar transição para dashboard
- **MELHORADO**: Estado da página alterado antes da mensagem de sucesso para transição imediata
- **CORRIGIDO**: Tag `</style>` solta no dashboard que aparecia como texto na tela
- **REMOVIDO**: HTML malformado que causava exibição incorreta de CSS como texto
- **CORRIGIDO**: CSS malformado no dashboard.py que exibia `</style>` como texto
- **REMOVIDO**: Blocos CSS redundantes que causavam problemas de renderização
- **MELHORADO**: Seções "Propostas em Aberto" e "Aniversariantes" com títulos consistentes
- **PADRONIZADO**: Layout do dashboard seguindo versão de produção com ícones e formatação
- **IMPLEMENTADO**: Seção "Aniversariantes" com design igual à versão de produção
- **APLICADO**: Gradientes azuis e layout de cards para aniversariantes (Hoje, Mês, Próximos 7 dias)
- **CORRIGIDO**: Fontes dos cards de métricas forçadas para branco seguindo versão de produção
- **MELHORADO**: Visibilidade de texto em todos os cards com color: white explícito
- **CORRIGIDO**: Fontes dos cards forçadas com !important para garantir cor branca
- **PADRONIZADO**: Barras de aniversariantes com cor da barra lateral (#1E366F, #2A4D8F)
- **APLICADO**: Mesmo estilo de mensagem vazia para alertas de retorno ao cliente
- **PADRONIZADO**: Mensagens informativas com fundo cinza claro e bordas consistentes
- **CORRIGIDO**: Erro crítico "name 'st' is not defined" em utils/force_spacing_fix.py
- **RESTAURADO**: Dashboard funcionando normalmente após correção da importação do streamlit
- **CORRIGIDO**: CSS malformado no app.py que causava erro "invalid decimal literal"
- **REMOVIDO**: Blocos CSS soltos que estavam fora de strings causando erro de sintaxe
- **ESTABILIZADO**: Aplicação deve carregar sem erros após limpeza do CSS problemático
- **CORRIGIDO**: Sidebar mostrando todos os arquivos de páginas ao invés dos módulos principais
- **RECONFIGURADO**: Arquivo .streamlit/pages.toml para ocultar navegação automática
- **APLICADO**: Sistema usa apenas navegação customizada com MENU_PRINCIPAL definido no app.py
- **ADICIONADO**: CSS força absoluta para ocultar navegação automática do Streamlit
- **CONFIGURADO**: .streamlit/config.toml com showSidebarNavigation = false e hideTopBar = true

### 2025-07-24
- **ADICIONADO**: Nova aba "Fluxo de Caixa" no módulo Gestão Financeira
- **CRIADO**: Módulo utils/fluxo_caixa_module.py com classes MonthCashFlow e CashFlowModule
- **IMPLEMENTADO**: Interface completa para gestão de fluxo de caixa mensal
- **CATEGORIAS**: Receitas (Previsão vendas, Contas a receber, Outros) e Despesas (Fornecedores, MEI, Marketing, etc.)
- **FUNCIONALIDADES**: Saldo inicial configurável, cálculos automáticos, visão consolidada
- **VISUALIZAÇÕES**: Gráficos de evolução do saldo, comparativo receitas vs despesas
- **CONTROLES**: Edição de valores por categoria, recálculo automático de saldos
- **CORRIGIDO**: Erro de sintaxe na linha 732 do financeiro.py (código Python malformado)
- **CORRIGIDO**: Problema de login lento - adicionado st.rerun() após autenticação bem-sucedida
- **MELHORADO**: Processo de login agora carrega interface principal automaticamente

### 2025-07-23
- **CORRIGIDO**: Problema de elementos azuis no módulo Vendas substituindo st.info() por custom_info()
- **CRIADO**: Componente global utils/custom_components.py com fundo branco consistente
- **SUBSTITUÍDO**: Todos st.info() no módulo Vendas por custom_info() com estilo unificado
- **OTIMIZADO**: API FastAPI configurada sem reload e com processo Python estável
- **ESTABILIZADO**: Sistema funcionando sem desconexões automáticas em alterações
- **CORRIGIDO**: Espaçamento inconsistente dos botões da sidebar entre módulos Dashboard/Propostas
- **REMOVIDO**: CSS conflitante inline dos módulos Vendas e Propostas
- **APLICADO**: Força absoluta CSS + JavaScript para espaçamento uniforme de 2px entre botões
- **PADRONIZADO**: Altura fixa de 38px para todos os botões da navegação lateral
- **CORRIGIDO**: Loop infinito causado por st.rerun() desnecessários no app.py
- **REMOVIDO**: st.rerun() dos botões de navegação do login que causavam loop
- **ESTABILIZADO**: Aplicação carregando normalmente sem loops de inicialização

### 2025-07-22
- **CORRIGIDO**: Loops infinitos de inicialização causados por st.rerun() desnecessários
- **REMOVIDO**: st.rerun() das funções show_termos(), show_politica(), show_planos(), show_enviar_manual()
- **REMOVIDO**: st.rerun() em handlers de erro de importação de páginas
- **REMOVIDO**: st.rerun() em botão "Atualizar Dados" do debug de propostas
- **LIMPO**: Workflows desnecessários - mantidos apenas "API FastAPI" e "Start application"
- **ESTABILIZADO**: Aplicação principal rodando estável na porta 5000 com HTTP 200 OK
- **VERIFICADO**: Login funcionando corretamente com Firebase Auth
- **CONFIRMADO**: Sistema multi-tenant operacional com filtragem por usuario_id
- **TESTADO**: Dashboard carregando propostas em aberto corretamente
- **CORRIGIDO**: Visibilidade de texto em selectbox do módulo vendas/produtos (#1e1e1e em fundo #f8f9fa)
- **CORRIGIDO**: Botões com texto branco (#ffffff) em fundo azul (#3a75c4) para melhor contraste
- **PADRONIZADO**: CSS para botões primary/secondary com hover em azul escuro (#2B547E)

### 2025-07-21
- **CORRIGIDO**: Erros de API do Streamlit impedindo carregamento
- **ATUALIZADO**: st.experimental_rerun() → st.rerun()
- **CORRIGIDO**: st.components.v1.html → components.html com importação correta
- **IMPLEMENTADO**: Edição completa de vendas com salvamento automático
- **ADICIONADO**: Salvamento automático ao alterar quantidade e preço (on_change)
- **ADICIONADO**: Métodos update_item_venda() e remove_item_venda() no banco
- **REMOVIDO**: Botões de salvar - não são mais necessários
- **MELHORADO**: Interface de edição com cabeçalhos organizados
- **CORRIGIDO**: Cálculo total produtos em propostas (linha 1716)
- **REDUZIDO**: Tamanho da imagem em enviar_manual.py de 300px para 150px
- **CORRIGIDO**: Botões relatórios com type="primary" e "secondary" + use_container_width=True
- **CORRIGIDO**: Importações PDF usando gerar_pdf_proposta disponível
- **MELHORADO**: Selectbox propostas mostra cliente e descrição
- **CORRIGIDO**: Botões download PDF com cores e largura completa
- **ATUALIZADO**: Geração de relatório usando utils/relatorio_servico_novo.py para formato "relatório_1"
- **CORRIGIDO**: Importações PDF agora usam gerar_pdf_relatorio_servico do módulo correto
- **CORRIGIDO**: CSS adicionado para botões primários e secundários com cores visíveis
- **ADICIONADO**: Estilos específicos para baseButton-primary e baseButton-secondary
- **CORRIGIDO**: Relatório interno usa pdf_generator_interno_melhorado.py com análise financeira completa
- **ATUALIZADO**: Geração PDF interno com custo total cliente e receita líquida projeto
- **CORRIGIDO**: Valor de comissão em PDF interno calcula valor real ao invés de fixo R$ 100
- **MELHORADO**: CSS para botões com visibilidade forçada e cores adequadas
- **ATUALIZADO**: Nova imagem profissional (professional_business_woman.png) com tamanho otimizado
- **CORRIGIDO**: Cores dos botões - Primary: #3a75c4 (azul brilhante), Secondary: #2B547E (azul escuro)
- **MELHORADO**: CSS específico para botões dentro de expanders com cores corretas
- **CORRIGIDO**: Botão "Limpar Carrinho" no módulo vendas com cor #3a75c4 específica
- **MODIFICADO**: Interface de vendas com três botões: "EDITAR VENDAS", "GERAR RELATÓRIO DE VENDAS", "EXCLUIR VENDAS"
- **REMOVIDO**: Expander "Gerenciar Vendas" substituído por confirmação inline de exclusão
- **PADRONIZADO**: Todos os três botões de vendas com type="primary" (cor azul)
- **CORRIGIDO**: Visibilidade de texto em labels/rótulos com cor #1e1e1e e font-weight: 600
- **ADICIONADO**: Fundo cinza claro (#f8f9fa) em todos os campos de entrada
- **MELHORADO**: Contraste geral de texto no módulo de vendas

### 2025-06-27
- **CORRIGIDO**: Problema de visibilidade de texto nos expanders do dashboard
- **ADICIONADO**: CSS específico para cor de texto nos expanders (#262730)
- **MANTIDO**: Formato original st.expander com st.write
- **LOCALIZAÇÃO**: Seção "Propostas em Aberto" do dashboard

### Correções de Interface
- Restaurado formato st.expander original após testes com botões customizados
- Adicionado CSS para garantir contraste adequado do texto
- Mantida funcionalidade de expansão/contração das propostas

## Known Issues
- Warnings de ScriptRunContext em modo bare (podem ser ignorados - não afetam funcionalidade)
- Erro de permissão Firebase ao carregar perfil (não impede login/funcionamento)

## System Status
- ✅ Aplicação principal estável na porta 5000
- ✅ Firebase Authentication funcionando
- ✅ PostgreSQL conectado e operacional
- ✅ Sistema multi-tenant ativo
- ✅ Dashboard e módulos carregando corretamente
- ✅ Espaçamento de botões da sidebar padronizado com CSS força absoluta

## Database Schema
Multi-tenant com filtragem por usuario_id:
- clientes, propostas, vendas, financeiro
- produtos_organizadores, andamento_propostas
- assistentes, parceiros, fornecedores

## Development Notes
- Sistema usa multi-tenancy com session_state.usuario_id
- Debug logs disponíveis para troubleshooting
- Adaptadores numpy registrados para PostgreSQL