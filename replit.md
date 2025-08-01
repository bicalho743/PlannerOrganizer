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

## External Dependencies
- **Streamlit**: Para a construção da interface web.
- **FastAPI**: Para os serviços de backend.
- **PostgreSQL**: Como banco de dados relacional, com ORM SQLAlchemy.
- **Firebase Authentication**: Para o sistema de autenticação de usuários.
- **Google Analytics**: Para análise de uso (mencionado nas tecnologias, mas não detalhado na implementação).