# Planner Organizer - Sistema de Gestão

## Overview
Sistema de gestão avançado para profissionais brasileiros, com foco em propostas, clientes e relatórios. O projeto visa otimizar a gestão de negócios através de uma interface intuitiva e funcionalidades robustas para controle financeiro, de vendas e relacionamento com o cliente.

## User Preferences
- Todas as respostas devem ser em português
- Preferência por componentes Streamlit nativos (st.expander, st.write)
- Correções de interface devem manter funcionalidade original
- Texto deve ser sempre visível e legível

## System Architecture

### Estrutura Principal
A aplicação é composta por `app.py` como arquivo principal, `pages/` para páginas modulares, `utils/` para utilitários e helpers, `.streamlit/style.css` para estilos customizados e `api/` para serviços FastAPI.

### Módulos Principais
O sistema inclui módulos para:
- **Dashboard**: Visão geral com propostas em aberto e estatísticas.
- **Propostas**: Gestão completa de propostas, incluindo exclusão com limpeza de dados relacionados. Seção "Itens & Custos" redesenhada com navegação lateral fixa (4 categorias: Produtos, Fornecedores, Assistentes, Outros), contadores e subtotais ao vivo, empty states visuais, e total geral sempre visível.
- **Clientes**: Cadastro e gestão de clientes.
- **Vendas**: Controle de vendas com botão "+ Nova Venda" inline no topo, lista de vendas e análise por período como abas diretas (sem sub-abas). Módulo de Produtos movido para Cadastros.
- **Cadastros**: Cadastro e gestão de clientes, fornecedores, parceiros, assistentes e **produtos** (nova aba 📦 Produtos com cadastro individual + importação em massa).
- **Financeiro**: Relatórios financeiros detalhados, incluindo fluxo de caixa mensal com categorias de receitas e despesas.

### UI/UX e Design
A interface é construída com Streamlit, focando em um design responsivo mobile-first. As decisões de UI/UX incluem:
- Layouts limpos para páginas como login e dashboard.
- Utilização de cards com bordas e sombras para destaque visual.
- Efeitos hover em elementos interativos.
- Padronização de cores e fontes para melhor contraste e legibilidade (e.g., texto branco em fundos azuis, texto escuro em fundos claros).
- Aplicação de gradientes e layouts de cards para seções como "Aniversariantes".
- Padronização de espaçamentos e alturas de botões via CSS e JavaScript para consistência visual.
- Componentes personalizados para mensagens informativas com fundo branco.

### Technical Implementations
- Autenticação e sistema multi-tenant utilizando `session_state.usuario_id` para filtrar dados por usuário.
- Otimização do FastAPI para rodar sem reload e com processo Python estável.
- Gerenciamento de estado otimizado para evitar loops infinitos em recarregamentos do Streamlit.
- Geração de relatórios em PDF com análise financeira detalhada (custo total, receita líquida, comissão).
- Sistema de vendas com salvamento automático de itens (quantidade, preço) e métodos `update_item_venda()`, `remove_item_venda()`.
- Integração vendas-financeiro: Vendas criam automaticamente entradas financeiras via função `add_venda()`.
- Fluxo de caixa com visualização de mês e ano completos para melhor organização temporal.
- Correção de bugs do `st.download_button()` em formulários para conformidade com regras do Streamlit.
- **Nova funcionalidade**: Análise por Período no módulo de vendas com filtros de data, agrupamento por período (dia/semana/mês/trimestre/ano), métricas de resumo, gráficos visuais e análise de produtos mais vendidos.
- Correções de CSS para visibilidade de texto em botões com aplicação específica nos seletores `.stButton > button` e `.stFormSubmitButton > button`.
- **Correções de Janeiro 2025**: Problemas de loop da aplicação resolvidos, método `get_itens_venda()` corrigido para usar campo `descricao` quando `produto_id` é NULL, geração de PDF de vendas estabilizada com nomes únicos de arquivo.
- **Sistema de autenticação**: Firebase Auth funcionando corretamente com usuários multi-tenant (65 propostas carregadas para usuário Tâmara).
- **Correção de Bug em Produtos (Agosto 2025)**: Corrigido erro "Database object has no attribute 'adicionar_produto'" - método correto é `add_produto`. Removido `time.sleep()` que causava erro de variável local.
- **Correção Sidebar Render Deploy (Agosto 2025)**: Problema da barra lateral não aparecer no deploy do Render resolvido. Alterado `showSidebarNavigation = false` para `true` no config.toml, criado config_render.toml específico para produção, adicionado script render_sidebar_fix.py, removida cor vermelha confusa da seta de colapso (agora branca/neutra), configuradas variáveis de ambiente específicas da sidebar no render.yaml.
- **Correções de Interface Agosto 2025**: Formas de pagamento simplificadas para apenas "Cartão" e "PIX". Formato de data de aniversário corrigido para DD/MMM em todos os campos (cadastro e edição). Campo de edição de data convertido de date_input para text_input para manter consistência com formato DD/MMM. Adicionado botão "🔄 Atualizar Lista" nos cadastros para resolver problemas de cache. Loop infinito da aplicação resolvido removendo workflow API conflitante.
- **Correção Toggle Sidebar (Outubro 2025)**: Resolvido problema do botão de toggle desaparecer após deploy. Solução implementada: habilitado `showSidebarNavigation = true` no config.toml, removidas regras CSS conflitantes que ocultavam o toggle, simplificada estilização do botão para apenas aparência (vermelho com borda branca). Toggle agora funciona corretamente tanto localmente quanto em produção, permitindo expandir/colapsar a sidebar naturalmente.
- **Correção Projeção Financeira (Agosto 2025)**: Resolvido erro "Cannot cast ufunc 'lstsq' input" na análise de projeção financeira dos relatórios. Corrigido tratamento de tipos de dados para np.polyfit(), implementado cálculo manual de diferença de dias, e adicionado tratamento robusto para tipos Timestamp vs date. Sistema de projeção agora funciona corretamente com fallbacks apropriados.
- **Campo Observações Personalizadas (Agosto 2025)**: Implementado campo de observações personalizadas no perfil do usuário para relatórios de propostas. Adicionada coluna `observacoes_relatorio` na tabela Perfil, interface de edição no perfil com texto padrão, métodos de salvamento no banco de dados e integração no gerador de PDF. PDFs agora usam observações personalizadas do usuário quando disponíveis, mantendo observações padrão como fallback. Implementado sistema completo de descrições sem limite de linhas em PDFs.
- **Rodapé Personalizado em PDFs (Agosto 2025)**: Padronização do rodapé em todos os relatórios PDF para usar dados do perfil do usuário. Adicionado campo `cargo` na tabela Perfil. Formato padrão: "Nome da Empresa | Cargo/Função | Instagram" centralizado com Instagram clicável. Integração completa nos geradores `pdf_generator_melhorado.py` e `pdf_generator_interno_melhorado.py`. Fallback para dados padrão quando perfil não configurado. Rodapé totalmente centralizado com data de geração embaixo.
- **Redesign Completo de PDFs (Março 2026)**: Todos os relatórios PDF do sistema redesenhados com novo design profissional Navy/Gold. Criado módulo base compartilhado `utils/pdf_base.py` com paleta de cores (NAVY #0D1B2A, GOLD #C9A84C), funções reutilizáveis: `header()`, `info_cards()`, `section_title()`, `table_rows()`, `total_row()`, `margem_block()`, `footer()`. Atualizados: Relatório Interno (`pdf_generator_interno_melhorado.py`), Relatório de Fornecedores (`pdf_generator_fornecedores.py`), Relatório de Serviço (`pdf_generator_servico_padronizado.py`), Relatório de Venda (`pdf_generator_venda_fixed.py`), Proposta de Serviço (`gerar_pdf_fechamento_novo` em `pdf_generator_melhorado.py`). Todos compartilham: cabeçalho Navy 52mm com número ghost em destaque, linha gold de acento, cards de info arredondados, tabelas com linhas alternadas arredondadas, rodapé cinza com dados do perfil.
- **Padronização Botões Download PDF (Agosto 2025)**: Todos os botões de download de PDF agora têm fundo verde escuro (#1B5E20 - #2E7D32) mais escuro que mensagens de sucesso. Aplicado via CSS centralizado em `.streamlit/style.css` com efeitos hover e texto branco garantido. Módulo `pdf_footer_helper.py` criado para unificar rodapés em todos relatórios (Vendas, Interno, Serviço, Propostas).
- **Módulo Pós-Organização (Janeiro 2026)**: Implementado módulo completo de acompanhamento pós-serviço. Quando uma proposta é finalizada, o sistema cria automaticamente um registro de pós-organização com 5 ações padrão: Agradecimento (D+1), Manutenção (D+2), Follow-up (D+7), Feedback (D+7), Oportunidade (D+10). Interface em `pages/pos_organizacao.py` com lista e detalhes de ações. Sistema de conclusão automática quando ações obrigatórias (Agradecimento, Follow-up, Feedback) são marcadas como FEITO. Ação especial RETORNO_TECNICO pode ser agendada quando Follow-up indica necessidade de ajuste (15-30 dias). Alertas no Dashboard para ações vencidas. Modelos ORM: `PostOrganization`, `PostOrganizationAction`. Funções CRUD: `create_post_organization()`, `get_post_organizations()`, `get_post_organization_actions()`, `update_post_organization_action()`, `add_retorno_tecnico_action()`, `get_pending_post_actions_for_dashboard()`.

## External Dependencies
- **Streamlit**: Para a construção da interface web.
- **FastAPI**: Para os serviços de backend.
- **PostgreSQL**: Como banco de dados relacional, com ORM SQLAlchemy.
- **Firebase Authentication**: Para o sistema de autenticação de usuários.
- **Google Analytics**: Para análise de uso (mencionado nas tecnologias, mas não detalhado na implementação).