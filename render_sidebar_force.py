#!/usr/bin/env python3
"""
Correção específica da sidebar para Render - força absoluta
Este arquivo é executado ANTES do app.py no Render
"""
import os
import sys
import subprocess

def force_render_sidebar():
    """Força configuração da sidebar especificamente para o ambiente Render"""
    
    print("🔧 RENDER: Aplicando correções definitivas da sidebar...")
    
    # 1. Criar configuração específica do Render
    render_config = """[server]
headless = true
port = $PORT
address = "0.0.0.0"
enableCORS = true
enableWebsocketCompression = true
fileWatcherType = "none"
runOnSave = false

[client]
showSidebarNavigation = true
sidebarState = "expanded"
showErrorDetails = false

[ui]
hideSidebarNav = false
hideTopBar = false

[browser]
gatherUsageStats = false
serverAddress = "0.0.0.0"

[theme]
primaryColor = "#1E366F"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[global]
developmentMode = false
"""
    
    # 2. Sobrescrever TODAS as configurações
    os.makedirs(".streamlit", exist_ok=True)
    
    config_files = [
        ".streamlit/config.toml",
        ".streamlit/config_render.toml", 
        ".streamlit/config_production.toml"
    ]
    
    for config_file in config_files:
        with open(config_file, "w") as f:
            f.write(render_config)
        print(f"✅ {config_file} sobrescrito para Render")
    
    # 3. Definir variáveis de ambiente do sistema
    critical_env_vars = {
        'STREAMLIT_CLIENT_SHOW_SIDEBAR_NAVIGATION': 'true',
        'STREAMLIT_CLIENT_SIDEBAR_STATE': 'expanded',
        'STREAMLIT_UI_HIDE_SIDEBAR_NAV': 'false',
        'STREAMLIT_SERVER_HEADLESS': 'true',
        'STREAMLIT_SERVER_ENABLE_CORS': 'true',
        'RENDER': 'true',
        'PRODUCTION': 'true'
    }
    
    for key, value in critical_env_vars.items():
        os.environ[key] = value
        print(f"✅ ENV: {key} = {value}")
    
    # 4. Criar arquivo de inicialização JavaScript 
    js_sidebar_fix = """
<script type="text/javascript">
console.log("🔧 RENDER: Iniciando correção forçada da sidebar...");

// Executa imediatamente quando o DOM estiver pronto
(function() {
    let sidebarForced = false;
    let attempts = 0;
    const maxAttempts = 20;
    
    function forceSidebarExpansion() {
        if (sidebarForced || attempts >= maxAttempts) return;
        
        attempts++;
        console.log(`🔍 RENDER: Tentativa ${attempts} de forçar sidebar...`);
        
        // Procura por elementos da sidebar colapsada
        const collapsedControl = document.querySelector('[data-testid="collapsedControl"]');
        const sidebarCollapsed = document.querySelector('[data-testid="stSidebar"][aria-expanded="false"]');
        
        if (collapsedControl && sidebarCollapsed) {
            console.log("✅ RENDER: Sidebar colapsada encontrada, expandindo...");
            collapsedControl.click();
            sidebarForced = true;
            return;
        }
        
        // Verifica se sidebar já está expandida
        const sidebarExpanded = document.querySelector('[data-testid="stSidebar"][aria-expanded="true"]');
        if (sidebarExpanded) {
            console.log("✅ RENDER: Sidebar já está expandida");
            sidebarForced = true;
            return;
        }
        
        // Força via CSS se necessário
        const sidebar = document.querySelector('[data-testid="stSidebar"]');
        if (sidebar) {
            sidebar.style.transform = 'translateX(0px)';
            sidebar.style.visibility = 'visible';
            sidebar.style.display = 'block';
            sidebar.setAttribute('aria-expanded', 'true');
            console.log("✅ RENDER: Sidebar forçada via CSS");
        }
        
        // Tenta novamente se necessário
        if (!sidebarForced) {
            setTimeout(forceSidebarExpansion, 300);
        }
    }
    
    // Executa quando DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', forceSidebarExpansion);
    } else {
        forceSidebarExpansion();
    }
    
    // Executa também quando a página carregar completamente
    window.addEventListener('load', forceSidebarExpansion);
    
    // Observa mudanças no DOM para reagir a atualizações do Streamlit
    const observer = new MutationObserver(function(mutations) {
        if (!sidebarForced) {
            forceSidebarExpansion();
        }
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
})();
</script>
"""
    
    # Salva o JavaScript em arquivo para injeção posterior
    with open("render_sidebar_fix.js", "w") as f:
        f.write(js_sidebar_fix)
    print("✅ JavaScript de correção da sidebar criado")
    
    print("🚀 RENDER: Configuração da sidebar finalizada!")
    return True

if __name__ == "__main__":
    force_render_sidebar()