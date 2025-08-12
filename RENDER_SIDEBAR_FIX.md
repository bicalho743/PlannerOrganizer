# Correção da Sidebar no Render Deploy

## Problema
A sidebar do Streamlit não aparece após deploy no Render (www.plannerorganiza.com.br), mesmo funcionando corretamente no preview local.

## Soluções Implementadas

### 1. Configurações de Arquivo
- **render_sidebar_force.py**: Script que executa ANTES do app.py no Render
- **render_deploy_final.py**: Script de configuração geral atualizado
- **.streamlit/config_render.toml**: Configuração específica para produção

### 2. Variáveis de Ambiente no render.yaml
```yaml
- key: STREAMLIT_CLIENT_SHOW_SIDEBAR_NAVIGATION
  value: true
- key: STREAMLIT_CLIENT_SIDEBAR_STATE
  value: expanded
- key: STREAMLIT_UI_HIDE_SIDEBAR_NAV
  value: false
- key: RENDER
  value: true
```

### 3. Parâmetros na Linha de Comando
```bash
streamlit run app.py \
  --client.showSidebarNavigation=true \
  --client.sidebarState=expanded \
  --ui.hideSidebarNav=false
```

### 4. JavaScript de Correção Forçada
- Detecta automaticamente ambiente Render via variável `RENDER=true`
- Busca por `[data-testid="collapsedControl"]` e clica automaticamente
- Força CSS caso necessário: `translateX(0px)` e `aria-expanded="true"`
- Usa MutationObserver para reagir a mudanças do DOM do Streamlit

### 5. Ordem de Execução no Deploy
1. `python render_sidebar_force.py` - Configurações específicas
2. `python render_deploy_final.py` - Configurações gerais  
3. `streamlit run app.py` - Execução da aplicação

## Arquivos Alterados
- `render.yaml` - Comandos de build e variáveis de ambiente
- `app.py` - JavaScript de detecção e correção automática
- `render_sidebar_force.py` - Novo script de correção
- `render_deploy_final.py` - Script atualizado
- `.streamlit/config_render.toml` - Configuração atualizada

## Teste
Após estas correções, fazer novo deploy no Render. A sidebar deve aparecer automaticamente em www.plannerorganiza.com.br

## Logs de Debug
O JavaScript mostra logs no console do navegador:
- `🔧 RENDER: Iniciando correção forçada da sidebar...`
- `✅ RENDER: Sidebar colapsada encontrada, expandindo...`
- `✅ RENDER: Sidebar já está expandida`