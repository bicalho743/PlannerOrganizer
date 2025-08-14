// Script para garantir funcionamento da sidebar no deploy
(function() {
    'use strict';
    
    // Função para forçar visibilidade do botão de colapso
    function forceCollapseButtonVisibility() {
        const selectors = [
            '[data-testid="collapsedControl"]',
            'button[aria-label*="collapse" i]',
            'button[title*="collapse" i]',
            'button[kind="minimal"]',
            '.stSidebar button',
            'section[data-testid="stSidebar"] button'
        ];
        
        selectors.forEach(selector => {
            const buttons = document.querySelectorAll(selector);
            buttons.forEach(button => {
                if (button) {
                    // Forçar estilos inline para garantir visibilidade
                    button.style.cssText = `
                        display: flex !important;
                        visibility: visible !important;
                        position: fixed !important;
                        top: 15px !important;
                        left: 15px !important;
                        z-index: 9999 !important;
                        background-color: rgba(30, 31, 54, 0.9) !important;
                        border: 1px solid rgba(255, 255, 255, 0.3) !important;
                        border-radius: 6px !important;
                        padding: 8px !important;
                        cursor: pointer !important;
                        align-items: center !important;
                        justify-content: center !important;
                        width: 32px !important;
                        height: 32px !important;
                        opacity: 1 !important;
                        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
                    `;
                    
                    // Garantir que o botão seja clicável
                    button.style.pointerEvents = 'auto';
                    
                    // Adicionar event listener se não existe
                    if (!button.hasAttribute('data-collapse-fixed')) {
                        button.setAttribute('data-collapse-fixed', 'true');
                        
                        button.addEventListener('click', function(e) {
                            e.preventDefault();
                            e.stopPropagation();
                            
                            // Lógica para toggle da sidebar
                            const sidebar = document.querySelector('[data-testid="stSidebar"]');
                            if (sidebar) {
                                const isCollapsed = sidebar.style.width === '0px' || 
                                                  sidebar.style.display === 'none' ||
                                                  sidebar.offsetWidth === 0;
                                
                                if (isCollapsed) {
                                    // Expandir sidebar
                                    sidebar.style.width = '250px';
                                    sidebar.style.display = 'block';
                                    sidebar.style.visibility = 'visible';
                                    sidebar.style.opacity = '1';
                                } else {
                                    // Colapsar sidebar
                                    sidebar.style.width = '0px';
                                    sidebar.style.display = 'none';
                                }
                            }
                        });
                    }
                }
            });
        });
    }
    
    // Função para observar mudanças no DOM
    function observeForCollapseButton() {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList') {
                    forceCollapseButtonVisibility();
                }
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        // Executar também periodicamente
        setInterval(forceCollapseButtonVisibility, 2000);
    }
    
    // Executar quando DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(forceCollapseButtonVisibility, 100);
            observeForCollapseButton();
        });
    } else {
        setTimeout(forceCollapseButtonVisibility, 100);
        observeForCollapseButton();
    }
    
    // Executar também quando a página estiver completamente carregada
    window.addEventListener('load', function() {
        setTimeout(forceCollapseButtonVisibility, 500);
    });
    
})();