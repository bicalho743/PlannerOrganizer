"""
Módulo para adicionar correções de compatibilidade com o Render
Este módulo fornece funções para injetar scripts JavaScript que corrigem problemas
de carregamento de módulos no Render.com
"""
import streamlit as st
import logging

# Configuração de logging
logger = logging.getLogger(__name__)

def inject_render_compatibility_fix():
    """
    Injeta script JavaScript para corrigir problemas de carregamento de módulos no Render
    e aplicar melhorias visuais em elementos da interface
    
    Esta função deve ser chamada no início do app.py antes de qualquer outro código
    """
    logger.info("Injetando script de compatibilidade para Render")
    
    # JavaScript para correção de problemas de módulos ES6
    js_code = """
    <script>
        // Configuração
        const CONFIG = {
          debug: true,
          moduleFixEnabled: true,
          specificModules: [
            'index.CC6uDm-p.js', 
            'index.CdkbqTPi.js', 
            'index.DsopOKvk.js', 
            'index.6w1bxtr_.js',
            'index.BUT1S9DN.js',
            'index.B4xKWXb9.js',
            'index.Bl-BqJMM.js',
            'index.Y1tjChmn.js',
            'index.B-cSXLfy.js'
          ],
          checkInterval: 1000,
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
          // Estratégia 1: Encontrar scripts de módulos que podem estar com problemas
          const failedModuleScripts = Array.from(document.querySelectorAll('script[src*="index."][src$=".js"]')).filter(script => 
            !script.hasAttribute('data-fixed') && 
            (script.hasAttribute('type') && script.getAttribute('type') === 'module')
          );
          
          // Estratégia 2: Procurar qualquer script que seja para plannerorganiza.com.br
          const plannerScripts = Array.from(document.querySelectorAll('script[src*="plannerorganiza.com.br"]')).filter(script => 
            !script.hasAttribute('data-fixed')
          );
          
          // Estratégia 3: Verificar todos os scripts com tipo "module"
          const moduleScripts = Array.from(document.querySelectorAll('script[type="module"]')).filter(script => 
            !script.hasAttribute('data-fixed') && script.hasAttribute('src')
          );
          
          // Combinar todos os scripts problemáticos
          const allFailedScripts = [...new Set([...failedModuleScripts, ...plannerScripts, ...moduleScripts])];
          
          if (allFailedScripts.length > 0) {
            logDebug(`Encontrados ${allFailedScripts.length} scripts potencialmente problemáticos`);
            
            allFailedScripts.forEach(script => {
              logDebug(`Corrigindo script: ${script.src}`);
              script.setAttribute('data-fixed', 'true');
              
              try {
                // Criar um novo script sem type="module"
                const newSrc = script.src;
                const newScript = document.createElement('script');
                newScript.src = newSrc;
                newScript.async = true;
                newScript.setAttribute('data-fixed-module', 'true');
                newScript.crossOrigin = 'anonymous';
                
                // Definir cabeçalhos de cache para evitar problemas de CORS
                if (newSrc.includes('plannerorganiza.com.br')) {
                  newScript.setAttribute('referrerpolicy', 'origin');
                }
                
                // Substituir o script original
                script.parentNode.replaceChild(newScript, script);
                logDebug(`Script substituído: ${newSrc}`);
                
                // Como segunda camada de proteção, também carregar via XHR
                if (CONFIG.useXHRFallback && (CONFIG.specificModules.some(mod => newSrc.includes(mod)) || newSrc.includes('plannerorganiza.com.br'))) {
                  loadScript(newSrc, true, true)
                    .then(() => logDebug(`Script adicional carregado via XHR: ${newSrc}`))
                    .catch(e => logDebug(`Falha no carregamento adicional via XHR: ${newSrc}`, e));
                }
              } catch (e) {
                logDebug(`Erro ao tentar substituir script: ${e.message}`);
              }
            });
          }
        }, CONFIG.checkInterval);

        // Adicionar elemento para debug
        document.addEventListener('DOMContentLoaded', function() {
          const debugElement = document.createElement('div');
          debugElement.id = 'module-fix-debug';
          debugElement.style.display = 'none';
          debugElement.textContent = 'Fix v2.1 para importação de módulos ativo';
          debugElement.setAttribute('data-modules', CONFIG.specificModules.join(','));
          document.body.appendChild(debugElement);
          logDebug('Elemento de debug adicionado');
          
          // Adicionar um diagnóstico geral para a página
          setTimeout(() => {
            const scriptTags = document.querySelectorAll('script[src*="index."][src$=".js"]');
            logDebug(`Diagnóstico: ${scriptTags.length} scripts de módulos encontrados na página`);
            
            // Verificar se estamos na versão de produção
            if (window.location.hostname === 'plannerorganiza.com.br') {
              logDebug('Detectado ambiente de produção');
              
              // Força o precarregamento dos módulos críticos
              CONFIG.specificModules.forEach(mod => {
                const preloadLink = document.createElement('link');
                preloadLink.rel = 'preload';
                preloadLink.as = 'script';
                preloadLink.href = `/static/js/${mod}`;
                preloadLink.crossOrigin = 'anonymous';
                document.head.appendChild(preloadLink);
                logDebug(`Preload adicionado para: ${mod}`);
              });
            }
          }, 1000);
        });

        logDebug('Sistema de correção de importação de módulos inicializado');
        
        // Script para melhorias visuais da interface
        document.addEventListener('DOMContentLoaded', function() {
            // Definir um intervalo para manipulação do DOM após o carregamento completo
            const interfaceInterval = setInterval(function() {
                // Encontrar todos os botões da barra lateral
                const sidebarButtons = document.querySelectorAll('[data-testid="stSidebar"] [data-testid="stButton"] button[kind="secondary"]');
                
                if (sidebarButtons && sidebarButtons.length > 0) {
                    logDebug(`Encontrados ${sidebarButtons.length} botões do menu para estilizar`);
                    
                    // Força JavaScript adicional para espaçamento consistente
                    sidebarButtons.forEach(button => {
                        // Aplicar espaçamento forçado
                        button.style.margin = '0';
                        button.style.marginTop = '0';
                        button.style.marginBottom = '0';
                        button.style.height = '38px';
                        
                        // Forçar container pai também
                        if (button.parentElement && button.parentElement.classList.contains('stButton')) {
                            button.parentElement.style.margin = '2px 0';
                            button.parentElement.style.marginTop = '2px';
                            button.parentElement.style.marginBottom = '2px';
                        }
                        button.style.fontWeight = '500';
                        button.style.color = '#1E366F';
                        button.style.transition = 'all 0.2s ease';
                        
                        // Adicionar evento hover
                        button.addEventListener('mouseenter', function() {
                            this.style.backgroundColor = '#E3F2FD';
                            this.style.transform = 'translateY(-2px)';
                            this.style.boxShadow = '0 4px 8px rgba(30, 54, 111, 0.15)';
                        });
                        
                        button.addEventListener('mouseleave', function() {
                            // Verificar se o botão está ativo
                            if (!this.classList.contains('menu-active')) {
                                this.style.backgroundColor = '#f5f7fa';
                                this.style.transform = 'translateY(0)';
                                this.style.boxShadow = 'none';
                            } else {
                                this.style.backgroundColor = '#E3F2FD';
                                this.style.transform = 'translateY(0)';
                                this.style.boxShadow = '0 2px 5px rgba(30, 54, 111, 0.15)';
                            }
                        });
                    });
                    
                    // Reduzir espaçamento no topo da sidebar
                    const sidebar = document.querySelector('[data-testid="stSidebar"]');
                    if (sidebar) {
                        const sidebarContent = sidebar.querySelector('[data-testid="stVerticalBlock"]');
                        if (sidebarContent) {
                            sidebarContent.style.paddingTop = '0';
                            sidebarContent.style.marginTop = '0';
                        }
                    }
                    
                    // Limpar intervalo após sucesso
                    clearInterval(interfaceInterval);
                    logDebug('Estilização da interface aplicada com sucesso');
                }
            }, 500);
            
            // Definir timeout máximo para evitar loop infinito
            setTimeout(function() {
                clearInterval(interfaceInterval);
                logDebug('Timeout da estilização da interface');
            }, 10000);
        });
    </script>
    """
    
    # Injetar o código JavaScript no aplicativo Streamlit
    st.components.v1.html(js_code, height=0, width=0)