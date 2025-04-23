// Script para injetar no cabeçalho HTML para corrigir problemas de importação no Render

// Tornando "window" disponível como "global" para evitar erros de referência
if (typeof window !== 'undefined') {
  window.global = window;
}

// Criando um objeto process.env vazio para compatibilidade
if (typeof process === 'undefined') {
  window.process = { env: {} };
}

// Função para carregamento alternativo de scripts quando type="module" falha
function loadScript(src, async = false, defer = false) {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = src;
    script.async = async;
    script.defer = defer;
    script.onload = resolve;
    script.onerror = reject;
    document.head.appendChild(script);
  });
}

// Detectar falhas em carregamento de scripts
window.addEventListener('error', function(event) {
  if (event.target && event.target.tagName === 'SCRIPT' && event.target.src.includes('index.')) {
    console.log('Módulo falhou ao carregar, tentando método alternativo:', event.target.src);
    
    // Extrair URL do script que falhou
    const scriptUrl = event.target.src;
    
    // Remover atributo type="module" e recarregar
    event.target.removeAttribute('type');
    loadScript(scriptUrl, true, true)
      .then(() => console.log('Script recarregado com sucesso:', scriptUrl))
      .catch(e => console.error('Falha no carregamento alternativo:', e));
  }
}, true);

// Adicionar elemento para debug
const debugElement = document.createElement('div');
debugElement.id = 'render-debug';
debugElement.style.display = 'none';
debugElement.textContent = 'Correção de importação de módulos ativa';
document.addEventListener('DOMContentLoaded', function() {
  document.body.appendChild(debugElement);
});

console.log('Fix para módulos instalado');