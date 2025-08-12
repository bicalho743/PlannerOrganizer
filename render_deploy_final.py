#!/usr/bin/env python3
"""
Script final para deploy no Render - garantir sidebar sempre visível
"""
import os
import shutil

def setup_render_deploy():
    """Configuração final para deploy no Render com sidebar garantida"""
    
    print("🚀 Configurando deploy final para Render...")
    
    # 1. Forçar configuração da sidebar
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
primaryColor = "#1E366F"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[global]
developmentMode = false
dataFrameSerialization = "legacy"
"""
    
    # Sobrescrever configuração
    with open(".streamlit/config.toml", "w") as f:
        f.write(config_content)
    print("✅ Configuração da sidebar sobrescrita")
    
    # 2. Definir variáveis de ambiente críticas
    env_vars = {
        'STREAMLIT_CLIENT_SHOW_SIDEBAR_NAVIGATION': 'true',
        'STREAMLIT_CLIENT_SIDEBAR_STATE': 'expanded',
        'STREAMLIT_UI_HIDE_SIDEBAR_NAV': 'false',
        'STREAMLIT_SERVER_HEADLESS': 'true',
        'STREAMLIT_SERVER_ENABLE_CORS': 'true',
        'STREAMLIT_BROWSER_GATHER_USAGE_STATS': 'false'
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"✅ {key} = {value}")
    
    # 2.1 Criar arquivo de configuração adicional para Render
    render_config = """[server]
headless = true
port = $PORT
address = "0.0.0.0"
enableCORS = true

[client]
showSidebarNavigation = true
sidebarState = "expanded"

[ui]
hideSidebarNav = false
hideTopBar = false
"""
    
    # Sobrescrever TODOS os arquivos de config
    config_files = [".streamlit/config.toml", ".streamlit/config_render.toml"]
    for config_file in config_files:
        with open(config_file, "w") as f:
            f.write(render_config)
        print(f"✅ {config_file} atualizado para Render")
    
    # 3. Criar arquivo HTML de inicialização para injetar CSS
    init_html = '''
    <script>
    console.log("🔧 Render Deploy - Forçando sidebar...");
    
    // CSS crítico injetado via JavaScript
    const criticalCSS = `
        section[data-testid="stSidebar"] {
            display: block !important;
            visibility: visible !important;
            width: 250px !important;
            min-width: 250px !important;
            opacity: 1 !important;
            flex: 0 0 250px !important;
        }
        
        section[data-testid="stSidebar"] > div {
            display: block !important;
            visibility: visible !important;
        }
        
        .main { margin-left: 250px !important; }
    `;
    
    const style = document.createElement('style');
    style.textContent = criticalCSS;
    document.head.appendChild(style);
    
    function forceShow() {
        const sidebar = document.querySelector('[data-testid="stSidebar"]');
        if (sidebar) {
            sidebar.style.cssText = 'display:block!important;visibility:visible!important;width:250px!important;opacity:1!important;';
        }
    }
    
    forceShow();
    setInterval(forceShow, 1000);
    </script>
    '''
    
    with open(".streamlit/render_init.html", "w") as f:
        f.write(init_html)
    print("✅ HTML de inicialização criado")
    
    return True

if __name__ == "__main__":
    setup_render_deploy()
    print("✅ Deploy para Render configurado com sucesso!")