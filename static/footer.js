// Script para criar rodapé fixo com informações completas
(function() {
    function createFooter() {
        // Remove qualquer rodapé existente
        const existingFooter = document.querySelector('.footer, .main-footer, [class*="footer"]');
        if (existingFooter) {
            existingFooter.remove();
        }
        
        // Cria o novo rodapé
        const footer = document.createElement('div');
        footer.className = 'footer';
        footer.innerHTML = `
            &copy; 2025 Planner Organizer. Todos os direitos reservados. | 
            <a href="https://plannerorganiza.com.br/?show_termos=true" target="_blank">Termos de Uso</a> | 
            <a href="https://plannerorganiza.com.br/?show_politica=true" target="_blank">Política de Privacidade</a> | 
            Contato: <a href="mailto:contato@plannerorganiza.com.br">contato@plannerorganiza.com.br</a>
        `;
        
        // Adiciona o rodapé ao body
        document.body.appendChild(footer);
    }
    
    // Executa quando o DOM estiver carregado
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', createFooter);
    } else {
        createFooter();
    }
    
    // Re-executa após mudanças no Streamlit
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                // Verifica se o rodapé ainda existe
                if (!document.querySelector('.footer')) {
                    createFooter();
                }
            }
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
})();