
// Garante que o botão de colapso da sidebar sempre apareça
function showSidebarToggle() {
    const toggleBtn = document.querySelector('button[data-testid="collapsedControl"]');
    if (toggleBtn) {
        toggleBtn.style.display = 'flex';
        toggleBtn.style.visibility = 'visible';
        toggleBtn.style.position = 'fixed';
        toggleBtn.style.top = '15px';
        toggleBtn.style.left = '15px';
        toggleBtn.style.zIndex = '9999';
        console.log('✅ Botão de colapso da sidebar forçado a aparecer');
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
    const toggleBtn = document.querySelector('button[data-testid="collapsedControl"]');
    if (toggleBtn) {
        const styles = window.getComputedStyle(toggleBtn);
        if (styles.display === 'none' || styles.visibility === 'hidden') {
            showSidebarToggle();
            console.log('🔧 Botão de colapso reativado automaticamente');
        }
    }
}, 2000);

console.log('🔧 Sistema de monitoramento do botão de colapso da sidebar ativado');
