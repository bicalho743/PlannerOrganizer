
// Garante que o botão de colapso apareça apenas para usuários autenticados
function showSidebarToggle() {
    const navButtons = document.querySelector('.nav-buttons');
    const toggleBtn = document.querySelector('div[data-testid="stSidebarCollapseButton"] button[data-testid="stBaseButton-headerNoPadding"]');
    
    if (navButtons && toggleBtn) {
        // Usuário autenticado - mostrar botão
        toggleBtn.style.display = 'flex';
        toggleBtn.style.visibility = 'visible';
        toggleBtn.style.position = 'fixed';
        toggleBtn.style.top = '15px';
        toggleBtn.style.left = '15px';
        toggleBtn.style.zIndex = '9999';
        toggleBtn.style.backgroundColor = 'rgba(30, 31, 54, 0.9)';
        toggleBtn.style.border = '1px solid rgba(255, 255, 255, 0.3)';
        toggleBtn.style.borderRadius = '6px';
        toggleBtn.style.padding = '8px';
        toggleBtn.style.width = '32px';
        toggleBtn.style.height = '32px';
        console.log('✅ Botão de colapso da sidebar ativado para usuário autenticado');
    } else if (!navButtons && toggleBtn) {
        // Usuário não autenticado - esconder botão
        toggleBtn.style.display = 'none';
        toggleBtn.style.visibility = 'hidden';
        console.log('🚫 Botão de colapso escondido - usuário não autenticado');
    }
}

// Força o botão a aparecer no carregamento
document.addEventListener('DOMContentLoaded', showSidebarToggle);

// Executa após um pequeno delay para garantir que o Streamlit tenha carregado
setTimeout(showSidebarToggle, 1000);
setTimeout(showSidebarToggle, 3000);

// Observa mudanças no DOM para reativar o botão se sumir
const observer = new MutationObserver(() => {
    showSidebarToggle();
});

observer.observe(document.body, { 
    childList: true, 
    subtree: true,
    attributes: true,
    attributeFilter: ['style', 'class']
});

// Verifica periodicamente se o botão ainda está visível
setInterval(() => {
    const toggleBtn = document.querySelector('div[data-testid="stSidebarCollapseButton"] button[data-testid="stBaseButton-headerNoPadding"]');
    if (toggleBtn) {
        const styles = window.getComputedStyle(toggleBtn);
        if (styles.display === 'none' || styles.visibility === 'hidden') {
            showSidebarToggle();
            console.log('🔧 Botão de colapso reativado automaticamente');
        }
    }
}, 2000);

console.log('🔧 Sistema de monitoramento do botão de colapso da sidebar ativado');
