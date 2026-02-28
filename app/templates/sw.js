// MitsuList Service Worker
const CACHE_NAME = 'mitsulist-cache-v1';
const urlsToCache = [
    '/',
    '/static/css/index.css',
    '/static/css/variables.css',
    '/static/ico/favicon.ico',
    '/static/ico/android-chrome-192x192.png',
    '/static/ico/android-chrome-512x512.png'
];

// Install Event
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Opened cache');
                return cache.addAll(urlsToCache);
            })
    );
    // Force the waiting service worker to become the active service worker.
    self.skipWaiting();
});

// Activate Event
self.addEventListener('activate', event => {
    const cacheWhitelist = [CACHE_NAME];
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheWhitelist.indexOf(cacheName) === -1) {
                        return caches.delete(cacheName); // Delete old caches
                    }
                })
            );
        })
    );
    // Tell the active service worker to take control of the page immediately.
    self.clients.claim();
});

// Fetch Event - Network First Strategy
self.addEventListener('fetch', event => {
    // We only want to cache GET requests
    if (event.request.method !== 'GET') {
        return;
    }

    // Skip caching for API calls or admin panel if needed
    if (event.request.url.includes('/api/') || event.request.url.includes('/admin/')) {
        event.respondWith(fetch(event.request));
        return;
    }

    event.respondWith(
        fetch(event.request)
            .then(response => {
                // Check if we received a valid response
                if (!response || response.status !== 200 || response.type !== 'basic') {
                    return response;
                }

                // IMPORTANT: Clone the response. A response is a stream
                // and because we want the browser to consume the response
                // as well as the cache consuming the response, we need
                // to clone it so we have two streams.
                var responseToCache = response.clone();

                caches.open(CACHE_NAME)
                    .then(cache => {
                        cache.put(event.request, responseToCache);
                    });

                return response;
            })
            .catch(() => {
                // If network fails, try to get it from the cache
                return caches.match(event.request);
            })
    );
});
