#!/usr/bin/env python3
"""
Script para garantir que a sidebar funcione corretamente no Render
"""
import os
import shutil

def fix_sidebar_config():
    """Corrige a configuração da sidebar para produção no Render"""
    
    # Copiar configuração específica do Render
    source_config = ".streamlit/config_render.toml"
    dest_config = ".streamlit/config.toml"
    
    if os.path.exists(source_config):
        shutil.copy2(source_config, dest_config)
        print(f"✅ Configuração da sidebar copiada: {source_config} -> {dest_config}")
    else:
        print(f"⚠️ Arquivo de configuração do Render não encontrado: {source_config}")
    
    # Verificar se o arquivo de configuração tem a sidebar habilitada
    if os.path.exists(dest_config):
        with open(dest_config, 'r') as f:
            content = f.read()
            if 'showSidebarNavigation = true' in content:
                print("✅ Sidebar habilitada na configuração")
            else:
                print("⚠️ Sidebar pode não estar habilitada")
    
    # Definir variáveis de ambiente específicas para sidebar
    os.environ['STREAMLIT_CLIENT_SHOW_SIDEBAR_NAVIGATION'] = 'true'
    os.environ['STREAMLIT_CLIENT_SIDEBAR_STATE'] = 'expanded'
    os.environ['STREAMLIT_UI_HIDE_SIDEBAR_NAV'] = 'false'
    
    # Adicionar JavaScript para forçar sidebar no HTML
    js_fix = """
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        // Forçar sidebar visível
        const sidebar = document.querySelector('[data-testid="stSidebar"]');
        if (sidebar) {
            sidebar.style.display = 'block !important';
            sidebar.style.visibility = 'visible !important';
            sidebar.style.opacity = '1 !important';
        }
        
        // Garantir que não esteja colapsada
        const collapseButton = document.querySelector('[data-testid="collapsedControl"]');
        if (collapseButton && sidebar && sidebar.style.width === '0px') {
            collapseButton.click();
        }
    });
    </script>
    """
    
    # Salvar o JavaScript em um arquivo para ser injetado
    with open('.streamlit/sidebar_fix.js', 'w') as f:
        f.write(js_fix.strip())
    
    print("✅ Variáveis de ambiente da sidebar configuradas")
    print("✅ JavaScript de correção da sidebar criado")
    
    return True

if __name__ == "__main__":
    print("🔧 Iniciando correção da sidebar para Render...")
    success = fix_sidebar_config()
    if success:
        print("✅ Correção da sidebar concluída com sucesso!")
    else:
        print("❌ Erro na correção da sidebar")