// Script inteligente para gerenciar sidebar no deploy
(function() {
    'use strict';
    
    let customToggleButton = null;
    
    // Função para detectar estado da sidebar
    function getSidebarState() {
        const sidebar = document.querySelector('[data-testid="stSidebar"]');
        if (!sidebar) return 'unknown';
        
        const style = window.getComputedStyle(sidebar);
        const width = parseInt(style.width) || sidebar.offsetWidth;
        
        return width <= 50 ? 'collapsed' : 'expanded';
    }
    
    // Função para criar botão customizado de reabrir
    function createCustomToggleButton() {
        if (customToggleButton) return;
        
        customToggleButton = document.createElement('div');
        customToggleButton.innerHTML = '☰';
        customToggleButton.style.cssText = `
            position: fixed !important;
            top: 15px !important;
            left: 15px !important;
            z-index: 10000 !important;
            background-color: rgba(30, 31, 54, 0.9) !important;
            border: 1px solid rgba(255, 255, 255, 0.3) !important;
            border-radius: 6px !important;
            padding: 8px 10px !important;
            cursor: pointer !important;
            color: white !important;
            font-size: 16px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            width: 32px !important;
            height: 32px !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
            transition: all 0.3s ease !important;
            font-family: monospace !important;
        `;
        
        customToggleButton.addEventListener('click', function() {
            expandSidebar();
        });
        
        customToggleButton.addEventListener('mouseenter', function() {
            this.style.backgroundColor = 'rgba(30, 31, 54, 1) !important';
            this.style.transform = 'scale(1.05) !important';
        });
        
        customToggleButton.addEventListener('mouseleave', function() {
            this.style.backgroundColor = 'rgba(30, 31, 54, 0.9) !important';
            this.style.transform = 'scale(1) !important';
        });
        
        document.body.appendChild(customToggleButton);
    }
    
    // Função para expandir sidebar
    function expandSidebar() {
        const sidebar = document.querySelector('[data-testid="stSidebar"]');
        if (sidebar) {
            sidebar.style.width = '250px !important';
            sidebar.style.minWidth = '250px !important';
            sidebar.style.display = 'block !important';
            sidebar.style.visibility = 'visible !important';
            sidebar.style.opacity = '1 !important';
            
            // Remover classe de colapsado
            document.body.classList.remove('sidebar-collapsed');
            
            // Remover botão customizado
            if (customToggleButton) {
                customToggleButton.remove();
                customToggleButton = null;
            }
            
            // Tentar encontrar e restaurar o botão nativo do Streamlit
            setTimeout(restoreNativeCollapseButton, 100);
        }
    }
    
    // Função para gerenciar estado da sidebar
    function manageSidebarState() {
        const state = getSidebarState();
        const isAuthenticated = document.querySelector('.nav-buttons') !== null;
        
        if (!isAuthenticated) {
            // Usuário não autenticado - esconder tudo
            if (customToggleButton) {
                customToggleButton.style.display = 'none';
            }
            document.body.classList.remove('sidebar-collapsed');
            return;
        }
        
        if (state === 'collapsed') {
            // Sidebar colapsada - mostrar botão customizado
            document.body.classList.add('sidebar-collapsed');
            createCustomToggleButton();
            customToggleButton.style.display = 'flex';
        } else {
            // Sidebar expandida - esconder botão customizado
            document.body.classList.remove('sidebar-collapsed');
            if (customToggleButton) {
                customToggleButton.style.display = 'none';
            }
        }
    }
    
    // Função para restaurar botão nativo do Streamlit
    function restoreNativeCollapseButton() {
        const selectors = [
            '[data-testid="collapsedControl"]',
            'button[aria-label*="collapse" i]',
            'button[title*="collapse" i]',
            'button[kind="minimal"]'
        ];
        
        selectors.forEach(selector => {
            const buttons = document.querySelectorAll(selector);
            buttons.forEach(button => {
                if (button && !button.hasAttribute('data-enhanced')) {
                    button.setAttribute('data-enhanced', 'true');
                    
                    // Interceptar clique para gerenciar estado
                    const originalClick = button.onclick;
                    button.onclick = function(e) {
                        if (originalClick) originalClick.call(this, e);
                        setTimeout(manageSidebarState, 100);
                    };
                    
                    button.addEventListener('click', function() {
                        setTimeout(manageSidebarState, 100);
                    });
                }
            });
        });
    }
    
    // Observer para mudanças no DOM
    const observer = new MutationObserver(function(mutations) {
        manageSidebarState();
        restoreNativeCollapseButton();
    });
    
    // Inicialização
    function initialize() {
        manageSidebarState();
        restoreNativeCollapseButton();
        
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['style', 'class']
        });
        
        // Verificar estado periodicamente
        setInterval(manageSidebarState, 1000);
    }
    
    // Executar quando DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }
    
    // Executar também quando página completamente carregada
    window.addEventListener('load', function() {
        setTimeout(initialize, 500);
    });
    
})();