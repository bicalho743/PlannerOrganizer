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
- **Propostas**: Gestão completa de propostas, incluindo exclusão com limpeza de dados relacionados.
- **Clientes**: Cadastro e gestão de clientes.
- **Vendas**: Controle de vendas, com integração automática de propostas e edição de itens.
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
- **Correção Crítica Botão Colapso Deploy (Agosto 2025)**: Resolvido problema crítico onde o botão de reabrir a sidebar desaparecia após deploy. Implementação de múltiplas camadas de proteção: CSS com seletores robustos sem dependência de `:has()`, JavaScript com fallbacks para diferentes seletores de botão, observer de DOM para mudanças dinâmicas, posicionamento fixo forçado com z-index alto, e injeção combinada de scripts tanto para desenvolvimento quanto produção.
- **Correção Navegação Automática e Autenticação (Agosto 2025)**: Resolvidos problemas críticos de navegação automática aparecendo antes do login e aplicação pulando tela de login. Soluções implementadas: desabilitado `showSidebarNavigation` no config.toml, criada tela de login temporária funcional, corrigido erro de importação em gerar_lancamentos_propostas.py, aplicado CSS abrangente para esconder navegação automática, implementada verificação de autenticação robusta que impede acesso ao dashboard sem login.

## External Dependencies
- **Streamlit**: Para a construção da interface web.
- **FastAPI**: Para os serviços de backend.
- **PostgreSQL**: Como banco de dados relacional, com ORM SQLAlchemy.
- **Firebase Authentication**: Para o sistema de autenticação de usuários.
- **Google Analytics**: Para análise de uso (mencionado nas tecnologias, mas não detalhado na implementação).