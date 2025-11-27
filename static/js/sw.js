/*
  Service Worker for EduSync School Management (Enhanced)
  Strategies:
  - HTML navigation: Network-first with offline fallback
  - Static assets (CSS/JS/Fonts): Cache-first
  - Images: Cache-first with max entries and cleanup
  - API/JSON: Stale-while-revalidate with short TTL
*/

const VERSION = 'v2.1.0';
const APP_PREFIX = 'edusync';
const RUNTIME_CACHE = `${APP_PREFIX}-runtime-${VERSION}`;
const PAGE_CACHE = `${APP_PREFIX}-pages-${VERSION}`;
const STATIC_CACHE = `${APP_PREFIX}-static-${VERSION}`;
const IMAGE_CACHE = `${APP_PREFIX}-images-${VERSION}`;

const OFFLINE_URL = '/offline/';

// Precache shell and critical assets
const PRECACHE_URLS = [
  '/',
  OFFLINE_URL,
  '/static/dist/css/adminlte.min.css',
  '/static/plugins/fontawesome-free/css/all.min.css',
  '/static/plugins/toastr/toastr.min.css',
  '/static/plugins/jquery/jquery.min.js',
  '/static/plugins/bootstrap/js/bootstrap.bundle.min.js',
  '/static/plugins/toastr/toastr.min.js',
  '/static/dist/js/adminlte.min.js',
  '/static/dist/img/icon-192x192.png',
  '/static/dist/img/icon-512x512.png',
  '/manifest.json'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    (async () => {
      try {
        const pageCache = await caches.open(PAGE_CACHE);
        // Try to cache all, but don't fail if some fail
        const results = await Promise.allSettled(
          PRECACHE_URLS.map(url => pageCache.add(url).catch(err => {
            console.warn(`Failed to cache ${url}:`, err);
            return null;
          }))
        );
        await self.skipWaiting();
      } catch (err) {
        console.error('Service worker install failed:', err);
        // Still skip waiting to activate the service worker
        await self.skipWaiting();
      }
    })()
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    (async () => {
      const keys = await caches.keys();
      await Promise.all(
        keys.map((key) => {
          if (
            key !== RUNTIME_CACHE &&
            key !== PAGE_CACHE &&
            key !== STATIC_CACHE &&
            key !== IMAGE_CACHE
          ) {
            return caches.delete(key);
          }
        })
      );
      await self.clients.claim();
    })()
  );
});

function isNavigationRequest(req) {
  return req.mode === 'navigate' || (req.method === 'GET' && req.headers.get('accept')?.includes('text/html'));
}

function isStaticAsset(url) {
  return (
    url.pathname.startsWith('/static/') &&
    (url.pathname.endsWith('.css') || url.pathname.endsWith('.js') || url.pathname.endsWith('.woff') || url.pathname.endsWith('.woff2'))
  );
}

function isImage(url) {
  return /\.(png|jpg|jpeg|gif|svg|webp)$/i.test(url.pathname);
}

function isApiRequest(req) {
  const url = new URL(req.url);
  return (
    req.headers.get('accept')?.includes('application/json') ||
    url.pathname.startsWith('/api/')
  );
}

async function putInCache(cacheName, request, response) {
  const cache = await caches.open(cacheName);
  try { await cache.put(request, response); } catch (_) {}
}

async function networkFirst(event) {
  try {
    const response = await fetch(event.request);
    const resClone = response.clone();
    putInCache(PAGE_CACHE, event.request, resClone);
    return response;
  } catch (err) {
    const cached = await caches.match(event.request) || await caches.match(OFFLINE_URL);
    return cached;
  }
}

async function cacheFirst(event, cacheName) {
  const cached = await caches.match(event.request);
  if (cached) return cached;
  const response = await fetch(event.request);
  putInCache(cacheName, event.request, response.clone());
  return response;
}

async function staleWhileRevalidate(event, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(event.request);
  const networkPromise = fetch(event.request)
    .then((response) => {
      cache.put(event.request, response.clone());
      return response;
    })
    .catch(() => cached);
  return cached || networkPromise;
}

async function trimCache(cacheName, maxItems = 60) {
  const cache = await caches.open(cacheName);
  const keys = await cache.keys();
  if (keys.length > maxItems) {
    await cache.delete(keys[0]);
    await trimCache(cacheName, maxItems);
  }
}

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Background sync for POST when offline
  if (request.method === 'POST') {
    if (self.registration.sync) {
      event.respondWith(
        (async () => {
          try {
            return await fetch(request.clone());
          } catch (e) {
            const body = await request.clone().formData().catch(() => null);
            const payload = body ? Object.fromEntries(body.entries()) : null;
            const queue = await caches.open(RUNTIME_CACHE);
            await queue.put(
              new Request(`/__queue__/${Date.now()}`, { method: 'GET' }),
              new Response(JSON.stringify({ url: request.url, payload }), {
                headers: { 'Content-Type': 'application/json' }
              })
            );
            await self.registration.sync.register('sync-queued-posts');
            return new Response(JSON.stringify({ queued: true }), {
              status: 202,
              headers: { 'Content-Type': 'application/json' }
            });
          }
        })()
      );
      return;
    }
  }

  // Ignore non-GET and cross-origin
  if (request.method !== 'GET' || url.origin !== self.location.origin) {
    return;
  }

  if (isNavigationRequest(request)) {
    event.respondWith(networkFirst(event));
    return;
  }

  if (isStaticAsset(url)) {
    event.respondWith(cacheFirst(event, STATIC_CACHE));
    return;
  }

  if (isImage(url)) {
    event.respondWith(
      (async () => {
        const response = await cacheFirst(event, IMAGE_CACHE);
        trimCache(IMAGE_CACHE, 80);
        return response;
      })()
    );
    return;
  }

  if (isApiRequest(request)) {
    event.respondWith(staleWhileRevalidate(event, RUNTIME_CACHE));
    return;
  }

  // Default: try cache, then network
  event.respondWith(cacheFirst(event, RUNTIME_CACHE));
});

// Background sync event handler
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-queued-posts') {
    event.waitUntil(
      (async () => {
        const queue = await caches.open(RUNTIME_CACHE);
        const keys = await queue.keys();
        for (const key of keys) {
          if (!key.url.includes('/__queue__/')) continue;
          const res = await queue.match(key);
          if (!res) continue;
          const { url, payload } = await res.json();
          try {
            await fetch(url, {
              method: 'POST',
              headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
              body: payload ? new URLSearchParams(payload).toString() : undefined
            });
            await queue.delete(key);
          } catch (_) {
            // Keep in queue
          }
        }
      })()
    );
  }
});

// Optional: handle messages to trigger skipWaiting from UI
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
