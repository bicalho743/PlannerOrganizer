// Service Worker para Planner Organizer
// Otimizações de cache e performance

const CACHE_NAME = 'planner-organizer-v1.0';
const CACHE_STATIC_NAME = 'planner-static-v1.0';
const CACHE_DYNAMIC_NAME = 'planner-dynamic-v1.0';

// Recursos estáticos para cache
const STATIC_FILES = [
    '/',
    '/app-icon.svg',
    '/favicon.png',
    'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap'
];

// Instalar Service Worker
self.addEventListener('install', event => {
    console.log('[SW] Instalando Service Worker...');
    event.waitUntil(
        caches.open(CACHE_STATIC_NAME)
            .then(cache => {
                console.log('[SW] Fazendo cache dos arquivos estáticos');
                return cache.addAll(STATIC_FILES);
            })
            .catch(error => {
                console.log('[SW] Erro ao fazer cache:', error);
            })
    );
});

// Ativar Service Worker
self.addEventListener('activate', event => {
    console.log('[SW] Ativando Service Worker...');
    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => {
                        if (cacheName !== CACHE_STATIC_NAME && cacheName !== CACHE_DYNAMIC_NAME) {
                            console.log('[SW] Removendo cache antigo:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
    );
});

// Interceptar requisições
self.addEventListener('fetch', event => {
    const requestUrl = new URL(event.request.url);
    
    // Estratégia Cache First para recursos estáticos
    if (STATIC_FILES.includes(event.request.url) || 
        event.request.url.includes('fonts.googleapis.com') ||
        event.request.url.includes('fonts.gstatic.com')) {
        
        event.respondWith(
            caches.match(event.request)
                .then(response => {
                    return response || fetch(event.request)
                        .then(fetchResponse => {
                            return caches.open(CACHE_STATIC_NAME)
                                .then(cache => {
                                    cache.put(event.request, fetchResponse.clone());
                                    return fetchResponse;
                                });
                        });
                })
        );
        return;
    }
    
    // Estratégia Network First para dados dinâmicos
    if (event.request.url.includes('/api/') || 
        event.request.method === 'POST' ||
        requestUrl.pathname.includes('streamlit')) {
        
        event.respondWith(
            fetch(event.request)
                .then(response => {
                    // Cache apenas respostas bem-sucedidas
                    if (response.status === 200) {
                        const responseClone = response.clone();
                        caches.open(CACHE_DYNAMIC_NAME)
                            .then(cache => {
                                cache.put(event.request, responseClone);
                            });
                    }
                    return response;
                })
                .catch(() => {
                    // Fallback para cache se offline
                    return caches.match(event.request);
                })
        );
        return;
    }
    
    // Estratégia Stale While Revalidate para outros recursos
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                const fetchPromise = fetch(event.request)
                    .then(fetchResponse => {
                        caches.open(CACHE_DYNAMIC_NAME)
                            .then(cache => {
                                cache.put(event.request, fetchResponse.clone());
                            });
                        return fetchResponse;
                    });
                
                return response || fetchPromise;
            })
    );
});

// Limpeza periódica do cache
self.addEventListener('message', event => {
    if (event.data && event.data.type === 'CLEAN_CACHE') {
        caches.open(CACHE_DYNAMIC_NAME)
            .then(cache => {
                cache.keys().then(requests => {
                    const now = Date.now();
                    const maxAge = 24 * 60 * 60 * 1000; // 24 horas
                    
                    requests.forEach(request => {
                        cache.match(request).then(response => {
                            if (response) {
                                const dateHeader = response.headers.get('date');
                                const responseTime = dateHeader ? new Date(dateHeader).getTime() : 0;
                                
                                if (now - responseTime > maxAge) {
                                    cache.delete(request);
                                }
                            }
                        });
                    });
                });
            });
    }
});

// Compressão de dados antes do cache
function compressData(data) {
    try {
        return new TextEncoder().encode(JSON.stringify(data));
    } catch (error) {
        return data;
    }
}

// Descompressão de dados do cache
function decompressData(compressedData) {
    try {
        return JSON.parse(new TextDecoder().decode(compressedData));
    } catch (error) {
        return compressedData;
    }
}

// Preload de recursos críticos
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_STATIC_NAME)
            .then(cache => {
                // Preload recursos críticos
                const criticalResources = [
                    'https://www.google-analytics.com/analytics.js',
                    'https://connect.facebook.net/en_US/fbevents.js'
                ];
                
                return Promise.all(
                    criticalResources.map(url => {
                        return fetch(url)
                            .then(response => {
                                if (response.ok) {
                                    cache.put(url, response);
                                }
                            })
                            .catch(() => {
                                console.log('[SW] Falha ao preload:', url);
                            });
                    })
                );
            })
    );
});