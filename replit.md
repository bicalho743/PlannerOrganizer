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

### 2025-07-21
- **CORRIGIDO**: Erros de API do Streamlit impedindo carregamento
- **ATUALIZADO**: st.experimental_rerun() → st.rerun()
- **CORRIGIDO**: st.components.v1.html → components.html com importação correta
- **IMPLEMENTADO**: Edição completa de vendas com salvamento automático
- **ADICIONADO**: Salvamento automático ao alterar quantidade e preço (on_change)
- **ADICIONADO**: Métodos update_item_venda() e remove_item_venda() no banco
- **REMOVIDO**: Botões de salvar - não são mais necessários
- **MELHORADO**: Interface de edição com cabeçalhos organizados

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
- Alguns workflows com arquivos inexistentes (debug_proposta_73.py, etc.)
- Warnings de ScriptRunContext em modo bare (podem ser ignorados)

## Database Schema
Multi-tenant com filtragem por usuario_id:
- clientes, propostas, vendas, financeiro
- produtos_organizadores, andamento_propostas
- assistentes, parceiros, fornecedores

## Development Notes
- Sistema usa multi-tenancy com session_state.usuario_id
- Debug logs disponíveis para troubleshooting
- Adaptadores numpy registrados para PostgreSQL