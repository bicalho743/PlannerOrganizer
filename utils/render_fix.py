"""
Módulo para adicionar correções de compatibilidade com o Render
Este módulo fornece funções para injetar scripts JavaScript que corrigem problemas
de carregamento de módulos no Render.com
"""
import streamlit as st


def inject_render_compatibility_fix():
    """
    Injeta script JavaScript para corrigir problemas de carregamento de módulos no Render
    
    Esta função deve ser chamada no início do app.py antes de qualquer outro código
    """
    # JavaScript para correção de problemas de módulos ES6
    js_code = """
    <script>
        // Configuração
        const CONFIG = {
          debug: true,
          moduleFixEnabled: true,
          specificModules: ['index.CC6uDm-p.js', 'index.B-cSXLfy.js'],
          checkInterval: 1500,
          useXHRFallback: true
        };

        // Registro de eventos para debug
        function logDebug(...args) {
          if (CONFIG.debug) {
            console.log('[ModuleFix]', ...args);
          }
        }

        // Inicialização
        logDebug('Inicializando fix para importação de módulos ES6');

        // Tornando "window" disponível como "global" para evitar erros de referência
        if (typeof window !== 'undefined') {
          window.global = window;
          logDebug('Definido window.global');
        }

        // Criando um objeto process.env vazio para compatibilidade
        if (typeof process === 'undefined') {
          window.process = { env: {} };
          logDebug('Definido window.process.env');
        }

        // Cache de módulos já processados
        window._moduleCache = window._moduleCache || {};

        // Função para carregamento alternativo de scripts
        function loadScript(src, async = false, defer = false) {
          // Verificar se já está no cache
          if (window._moduleCache[src]) {
            logDebug(`Script já carregado, retornando do cache: ${src}`);
            return Promise.resolve();
          }
          
          logDebug(`Carregando script: ${src}`);
          return new Promise((resolve, reject) => {
            // Primeira tentativa: carregamento normal
            const script = document.createElement('script');
            script.src = src;
            script.async = async;
            script.defer = defer;
            script.onload = function() {
              logDebug(`Script carregado com sucesso: ${src}`);
              window._moduleCache[src] = true;
              resolve();
            };
            script.onerror = function(e) {
              logDebug(`Erro ao carregar script, tentando XHR: ${src}`, e);
              
              if (CONFIG.useXHRFallback) {
                // Segunda tentativa: usar XHR para obter o conteúdo e injetar inline
                const xhr = new XMLHttpRequest();
                xhr.open('GET', src);
                xhr.onload = function() {
                  if (xhr.status === 200) {
                    logDebug(`XHR bem-sucedido para: ${src}`);
                    const scriptContent = xhr.responseText;
                    
                    try {
                      // Criar um novo script com o conteúdo obtido
                      const newScript = document.createElement('script');
                      newScript.textContent = scriptContent;
                      document.head.appendChild(newScript);
                      
                      logDebug(`Script injetado inline: ${src}`);
                      window._moduleCache[src] = true;
                      resolve();
                    } catch (execError) {
                      logDebug(`Erro ao executar script: ${src}`, execError);
                      reject(execError);
                    }
                  } else {
                    logDebug(`XHR falhou com status ${xhr.status} para: ${src}`);
                    reject(new Error(`Falha ao carregar ${src} via XHR: ${xhr.status}`));
                  }
                };
                xhr.onerror = function(xhrError) {
                  logDebug(`Erro XHR para: ${src}`, xhrError);
                  reject(xhrError);
                };
                xhr.send();
              } else {
                reject(e);
              }
            };
            document.head.appendChild(script);
          });
        }

        // Interceptar a criação de elementos <script>
        if (CONFIG.moduleFixEnabled) {
          const originalCreateElement = document.createElement;
          document.createElement = function(tag) {
            const element = originalCreateElement.call(document, tag);
            
            if (tag.toLowerCase() === 'script') {
              // Interceptar a definição do atributo type="module"
              const originalSetAttribute = element.setAttribute;
              element.setAttribute = function(name, value) {
                if (name === 'type' && value === 'module') {
                  logDebug('Convertendo script type="module" para script normal');
                  // Deixar o script sem o type="module"
                  return element;
                }
                
                // Se for src e estiver em nossa lista de módulos específicos
                if (name === 'src' && CONFIG.specificModules.some(mod => value.includes(mod))) {
                  logDebug(`Detectado módulo específico: ${value}`);
                  element.dataset.fixedModule = 'true';
                }
                
                return originalSetAttribute.call(this, name, value);
              };
            }
            
            return element;
          };
          logDebug('Interceptação de createElement instalada');
        }

        // Sobrescrever fetch para lidar com módulos específicos
        const originalFetch = window.fetch;
        window.fetch = function(url, options) {
          if (typeof url === 'string' && CONFIG.specificModules.some(mod => url.includes(mod))) {
            logDebug(`Interceptando fetch para: ${url}`);
            
            // Tentar buscar com outras opções de cache
            return originalFetch(url, {
              ...options,
              cache: 'no-cache',
              mode: 'cors',
              credentials: 'same-origin'
            }).catch(err => {
              logDebug(`Falha ao carregar via fetch: ${url}`, err);
              
              if (CONFIG.useXHRFallback) {
                // Tentar com XHR como último recurso
                return new Promise((resolve) => {
                  const xhr = new XMLHttpRequest();
                  xhr.open('GET', url);
                  xhr.responseType = 'text';
                  xhr.onload = function() {
                    if (xhr.status === 200) {
                      logDebug(`XHR bem-sucedido para: ${url}`);
                      const blob = new Blob([xhr.response], { type: 'application/javascript' });
                      resolve(new Response(blob));
                    } else {
                      logDebug(`XHR falhou com status ${xhr.status} para: ${url}`);
                      resolve(Response.error());
                    }
                  };
                  xhr.onerror = function() {
                    logDebug(`Erro XHR para: ${url}`);
                    resolve(Response.error());
                  };
                  xhr.send();
                });
              }
              
              throw err;
            });
          }
          
          return originalFetch(url, options);
        };
        logDebug('Interceptação de fetch instalada');

        // Detectar falhas em carregamento de scripts
        window.addEventListener('error', function(event) {
          if (event.target && event.target.tagName === 'SCRIPT') {
            const scriptUrl = event.target.src;
            
            // Verificar se o script é um dos módulos que queremos interceptar
            if (CONFIG.specificModules.some(mod => scriptUrl.includes(mod)) || 
                (scriptUrl.includes('index.') && scriptUrl.includes('.js'))) {
              logDebug(`Erro detectado em script: ${scriptUrl}`);
              event.preventDefault();
              
              // Remover script original para evitar duplicação de erros
              event.target.parentNode.removeChild(event.target);
              
              // Tentar carregar via loadScript com suporte a fallback
              loadScript(scriptUrl, true, true)
                .then(() => logDebug(`Script recuperado com sucesso: ${scriptUrl}`))
                .catch(e => logDebug(`Todas as tentativas falharam para: ${scriptUrl}`, e));
            }
          }
        }, true);
        logDebug('Detector de erros de script instalado');

        // Verificar periodicamente scripts com problemas
        setInterval(function() {
          // Encontrar scripts de módulos que podem estar com problemas
          const failedScripts = Array.from(document.querySelectorAll('script[src*="index."][src$=".js"]')).filter(script => 
            !script.hasAttribute('data-fixed') && 
            (script.hasAttribute('type') && script.getAttribute('type') === 'module')
          );
          
          if (failedScripts.length > 0) {
            logDebug(`Encontrados ${failedScripts.length} scripts potencialmente problemáticos`);
            
            failedScripts.forEach(script => {
              logDebug(`Corrigindo script: ${script.src}`);
              script.setAttribute('data-fixed', 'true');
              
              // Criar um novo script sem type="module"
              const newSrc = script.src;
              const newScript = document.createElement('script');
              newScript.src = newSrc;
              newScript.async = true;
              
              // Substituir o script original
              script.parentNode.replaceChild(newScript, script);
              logDebug(`Script substituído: ${newSrc}`);
            });
          }
        }, CONFIG.checkInterval);

        // Adicionar elemento para debug
        document.addEventListener('DOMContentLoaded', function() {
          const debugElement = document.createElement('div');
          debugElement.id = 'module-fix-debug';
          debugElement.style.display = 'none';
          debugElement.textContent = 'Fix v2.0 para importação de módulos ativo';
          document.body.appendChild(debugElement);
          logDebug('Elemento de debug adicionado');
        });

        logDebug('Sistema de correção de importação de módulos inicializado');
    </script>
    """
    
    # Injetar o código JavaScript no aplicativo Streamlit
    st.components.v1.html(js_code, height=0, width=0)