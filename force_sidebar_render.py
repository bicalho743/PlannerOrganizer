#!/usr/bin/env python3
"""
Script adicional para forçar a sidebar no Render - solução definitiva
"""
import os
import shutil

def force_sidebar_render():
    """Força a configuração da sidebar especificamente para Render"""
    
    print("🔧 Forçando configuração da sidebar para Render...")
    
    # 1. Copiar configuração do Render
    if os.path.exists(".streamlit/config_render.toml"):
        shutil.copy2(".streamlit/config_render.toml", ".streamlit/config.toml")
        print("✅ Configuração do Render aplicada")
    
    # 2. Criar configuração inline caso não exista
    config_content = """[server]
headless = true
address = "0.0.0.0"
port = $PORT
runOnSave = false
fileWatcherType = "none"
maxUploadSize = 200
enableCORS = true
enableWebsocketCompression = true
enableXsrfProtection = false

[client]
showSidebarNavigation = true
showErrorDetails = false
caching = true
sidebarState = "expanded"

[ui]
hideTopBar = false
hideSidebarNav = false

[browser]
gatherUsageStats = false
serverAddress = "0.0.0.0"

[theme]
primaryColor = "#C9A84C"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#0D1B2A"
textColor = "#262730"
font = "sans serif"

[global]
developmentMode = false
"""
    
    with open(".streamlit/config.toml", "w") as f:
        f.write(config_content)
    print("✅ Configuração da sidebar forçada via arquivo")
    
    # 3. Definir todas as variáveis de ambiente possíveis
    env_vars = {
        'STREAMLIT_CLIENT_SHOW_SIDEBAR_NAVIGATION': 'true',
        'STREAMLIT_CLIENT_SIDEBAR_STATE': 'expanded',
        'STREAMLIT_UI_HIDE_SIDEBAR_NAV': 'false',
        'STREAMLIT_BROWSER_GATHER_USAGE_STATS': 'false',
        'STREAMLIT_SERVER_HEADLESS': 'true',
        'STREAMLIT_SERVER_ENABLE_CORS': 'true'
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"✅ {key} = {value}")
    
    # 4. Criar arquivo JavaScript mais robusto
    js_content = '''
    <script>
    console.log("🔧 Iniciando correção da sidebar...");
    
    function forceSidebar() {
        const sidebar = document.querySelector('[data-testid="stSidebar"]');
        const sidebarContent = document.querySelector('.css-1d391kg, .css-1lcbmhc, section[data-testid="stSidebar"] > div');
        
        if (sidebar) {
            sidebar.style.display = 'block !important';
            sidebar.style.visibility = 'visible !important';
            sidebar.style.opacity = '1 !important';
            sidebar.style.width = '250px !important';
            sidebar.style.minWidth = '250px !important';
            sidebar.style.flex = '0 0 250px !important';
            console.log("✅ Sidebar forçada a aparecer");
        }
        
        if (sidebarContent) {
            sidebarContent.style.display = 'block !important';
            sidebarContent.style.visibility = 'visible !important';
            console.log("✅ Conteúdo da sidebar forçado");
        }
        
        // Verificar se está colapsada e expandir
        const collapseButton = document.querySelector('[data-testid="collapsedControl"]');
        if (collapseButton && sidebar && sidebar.offsetWidth < 100) {
            collapseButton.click();
            console.log("✅ Sidebar expandida via botão");
        }
    }
    
    // Executar imediatamente
    forceSidebar();
    
    // Executar após DOM carregar
    document.addEventListener('DOMContentLoaded', forceSidebar);
    
    // Executar periodicamente nos primeiros segundos
    let attempts = 0;
    const interval = setInterval(() => {
        forceSidebar();
        attempts++;
        if (attempts > 10) {
            clearInterval(interval);
            console.log("🔚 Tentativas de correção da sidebar finalizadas");
        }
    }, 500);
    
    // Observer para mudanças no DOM
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                forceSidebar();
            }
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    console.log("✅ Correção da sidebar configurada com observer");
    </script>
    '''
    
    with open(".streamlit/sidebar_fix.js", "w") as f:
        f.write(js_content)
    print("✅ JavaScript de correção da sidebar atualizado")
    
    return True

if __name__ == "__main__":
    force_sidebar_render()