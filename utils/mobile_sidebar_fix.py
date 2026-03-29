"""
Correção específica para visualização da sidebar em dispositivos móveis
"""
import streamlit as st
import streamlit.components.v1 as components

def inject_mobile_sidebar_fix():
    """
    DESATIVADO - CSS da sidebar agora é controlado centralmente pelo .streamlit/style.css
    """
    return  # Função desativada para evitar conflitos
    
    mobile_fix_html = """
    <style>
    /* Força a exibição da sidebar em todos os dispositivos */
    section[data-testid="stSidebar"],
    .css-1d391kg,
    .css-1v3fvcr,
    .css-17lntkn,
    .css-1vq4p4l {
        display: block !important;
        visibility: visible !important;
        position: relative !important;
        width: auto !important;
        min-width: 250px !important;
        background-color: #0D1B2A !important;
    }
    
    /* Force sidebar visibility on all screen sizes */
    @media screen {
        section[data-testid="stSidebar"] {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
        }
    }
    
    /* Mobile specific fixes */
    @media screen and (max-width: 768px) {
        /* Container principal */
        .main .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            max-width: 100% !important;
        }
        
        /* Sidebar container */
        section[data-testid="stSidebar"] {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            height: 100vh !important;
            width: 280px !important;
            z-index: 999999 !important;
            transform: translateX(-100%) !important;
            transition: transform 0.3s ease !important;
            background-color: #0D1B2A !important;
            border-right: 2px solid #0D1B2A !important;
            box-shadow: 2px 0 10px rgba(0, 0, 0, 0.3) !important;
        }
        
        /* Sidebar aberta */
        section[data-testid="stSidebar"].sidebar-open {
            transform: translateX(0) !important;
        }
        
        /* Botão de toggle da sidebar */
        .mobile-sidebar-toggle {
            position: fixed !important;
            top: 20px !important;
            left: 20px !important;
            z-index: 1000000 !important;
            background: linear-gradient(135deg, #0D1B2A, #C9A84C) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 12px 16px !important;
            font-size: 16px !important;
            font-weight: bold !important;
            cursor: pointer !important;
            box-shadow: 0 4px 15px rgba(46, 74, 153, 0.4) !important;
            display: flex !important;
            align-items: center !important;
            gap: 8px !important;
        }
        
        .mobile-sidebar-toggle:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(46, 74, 153, 0.6) !important;
        }
        
        /* Overlay para fechar sidebar */
        .sidebar-overlay {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            background-color: rgba(0, 0, 0, 0.5) !important;
            z-index: 999998 !important;
            display: none !important;
        }
        
        .sidebar-overlay.active {
            display: block !important;
        }
        
        /* Botão de fechar dentro da sidebar */
        .sidebar-close-btn {
            position: absolute !important;
            top: 20px !important;
            right: 20px !important;
            background: rgba(255, 255, 255, 0.1) !important;
            color: white !important;
            border: none !important;
            border-radius: 50% !important;
            width: 40px !important;
            height: 40px !important;
            font-size: 18px !important;
            cursor: pointer !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
    }
    
    /* Tablets */
    @media screen and (min-width: 769px) and (max-width: 1024px) {
        section[data-testid="stSidebar"] {
            width: 260px !important;
            position: relative !important;
            transform: none !important;
        }
        
        .mobile-sidebar-toggle {
            display: none !important;
        }
    }
    
    /* Desktop */
    @media screen and (min-width: 1025px) {
        .mobile-sidebar-toggle {
            display: none !important;
        }
        
        .sidebar-overlay {
            display: none !important;
        }
    }
    </style>
    
    <script>
    // Função para detectar se está em mobile
    function isMobile() {
        return window.innerWidth <= 768;
    }
    
    // Função para criar o botão de toggle
    function createMobileToggle() {
        if (!isMobile() || document.querySelector('.mobile-sidebar-toggle')) {
            return;
        }
        
        // Criar botão de toggle
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'mobile-sidebar-toggle';
        toggleBtn.innerHTML = '☰ Menu';
        
        // Criar overlay
        const overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        
        // Adicionar ao DOM
        document.body.appendChild(toggleBtn);
        document.body.appendChild(overlay);
        
        // Função para abrir sidebar
        function openSidebar() {
            const sidebar = document.querySelector('section[data-testid="stSidebar"]');
            if (sidebar) {
                sidebar.classList.add('sidebar-open');
                overlay.classList.add('active');
                
                // Criar botão de fechar dentro da sidebar se não existir
                if (!sidebar.querySelector('.sidebar-close-btn')) {
                    const closeBtn = document.createElement('button');
                    closeBtn.className = 'sidebar-close-btn';
                    closeBtn.innerHTML = '×';
                    closeBtn.onclick = closeSidebar;
                    sidebar.appendChild(closeBtn);
                }
            }
        }
        
        // Função para fechar sidebar
        function closeSidebar() {
            const sidebar = document.querySelector('section[data-testid="stSidebar"]');
            if (sidebar) {
                sidebar.classList.remove('sidebar-open');
                overlay.classList.remove('active');
            }
        }
        
        // Event listeners
        toggleBtn.onclick = openSidebar;
        overlay.onclick = closeSidebar;
        
        // Fechar sidebar com ESC
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeSidebar();
            }
        });
    }
    
    // Executar quando a página carregar
    document.addEventListener('DOMContentLoaded', createMobileToggle);
    
    // Executar após o Streamlit carregar
    setTimeout(createMobileToggle, 1000);
    setTimeout(createMobileToggle, 3000);
    
    // Recriar em mudanças de orientação
    window.addEventListener('resize', function() {
        setTimeout(createMobileToggle, 500);
    });
    </script>
    """
    
    # Injeta o HTML com altura 0
    components.html(mobile_fix_html, height=0)