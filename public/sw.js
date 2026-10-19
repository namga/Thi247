const CACHE = 'kho-hoc-tap-shell-v1';
const SHELL = ['/', '/manifest.webmanifest'];
self.addEventListener('install', event => event.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL))));
self.addEventListener('activate', event => event.waitUntil(self.clients.claim()));
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;
  event.respondWith(caches.match(event.request).then(hit => hit || fetch(event.request).then(res => {
    if (res.ok && (event.request.destination === 'script' || event.request.destination === 'style')) {
      const copy = res.clone(); caches.open(CACHE).then(c => c.put(event.request, copy));
    }
    return res;
  }).catch(() => caches.match('/'))));
});
