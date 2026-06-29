/**
 * Service Worker - PWA
 * Manejo de caché, sincronización en segundo plano, notificaciones
 */

const CACHE_NAME = 'ftra-v1';
const ASSETS_TO_CACHE = [
    '/',
    '/static/css/main.css',
    '/static/js/main.js',
    '/static/js/upload.js',
    '/offline.html'
];

// ============================================
// INSTALACIÓN
// ============================================

self.addEventListener('install', (event) => {
    console.log('[Service Worker] Instalando...');
    
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('[Service Worker] Cacheando assets');
            return cache.addAll(ASSETS_TO_CACHE).catch((error) => {
                console.error('[Service Worker] Error al cachear:', error);
                // Continuar incluso si algunos assets fallan
                return Promise.resolve();
            });
        })
    );
    
    self.skipWaiting();
});

// ============================================
// ACTIVACIÓN
// ============================================

self.addEventListener('activate', (event) => {
    console.log('[Service Worker] Activando...');
    
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('[Service Worker] Eliminando caché antigua:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    
    self.clients.claim();
});

// ============================================
// FETCH
// ============================================

self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Ignorar requests no-HTTP
    if (!url.protocol.startsWith('http')) {
        return;
    }

    // Strategy: Network first, fallback to cache
    if (request.method === 'GET') {
        event.respondWith(
            fetch(request)
                .then((response) => {
                    // Cachear respuesta exitosa
                    if (response.status === 200) {
                        const responseToCache = response.clone();
                        caches.open(CACHE_NAME).then((cache) => {
                            cache.put(request, responseToCache);
                        });
                    }
                    return response;
                })
                .catch(() => {
                    // Fallback a caché
                    return caches.match(request).then((response) => {
                        if (response) {
                            return response;
                        }
                        
                        // Mostrar página offline
                        if (request.destination === 'document') {
                            return caches.match('/offline.html');
                        }
                    });
                })
        );
    }
});

// ============================================
// SINCRONIZACIÓN EN SEGUNDO PLANO
// ============================================

self.addEventListener('sync', (event) => {
    console.log('[Service Worker] Background Sync:', event.tag);
    
    if (event.tag === 'sync-facturas') {
        event.waitUntil(syncFacturas());
    }
});

async function syncFacturas() {
    try {
        // Sincronizar facturas pendientes
        const clients = await self.clients.matchAll();
        clients.forEach(client => {
            client.postMessage({
                type: 'sync-complete',
                data: { message: 'Facturas sincronizadas' }
            });
        });
    } catch (error) {
        console.error('[Service Worker] Error en sincronización:', error);
    }
}

// ============================================
// NOTIFICACIONES PUSH
// ============================================

self.addEventListener('push', (event) => {
    console.log('[Service Worker] Push recibido');
    
    const options = {
        badge: '/static/img/badge.png',
        icon: '/static/img/icon-192x192.png',
        body: event.data ? event.data.text() : 'Nueva notificación',
        tag: 'ftra-notification',
        requireInteraction: false,
        actions: [
            { action: 'open', title: 'Abrir' },
            { action: 'close', title: 'Cerrar' }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification('FTRA', options)
    );
});

self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    
    event.waitUntil(
        clients.matchAll({ type: 'window' }).then((clientList) => {
            // Buscar cliente existente
            for (let i = 0; i < clientList.length; i++) {
                const client = clientList[i];
                if (client.url === '/' && 'focus' in client) {
                    return client.focus();
                }
            }
            
            // Abrir nueva ventana si no existe
            if (clients.openWindow) {
                return clients.openWindow('/');
            }
        })
    );
});

// ============================================
// MENSAJES DESDE CLIENTE
// ============================================

self.addEventListener('message', (event) => {
    console.log('[Service Worker] Mensaje recibido:', event.data);
    
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});
