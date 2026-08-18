// Minimal service worker for Compass Leads.
// This exists mainly so Chrome/Android considers the app "installable."
// It does NOT try to cache Firestore or Anthropic API calls — those need
// a live connection, per the "solid venue wifi" assumption this app is built on.
const CACHE = 'compass-leads-shell-v1';
const SHELL_FILES = ['./index.html', './manifest.json', './icon-192.png', './icon-512.png'];

self.addEventListener('install', evt => {
  evt.waitUntil(
    caches.open(CACHE).then(cache => cache.addAll(SHELL_FILES)).catch(()=>{})
  );
  self.skipWaiting();
});

self.addEventListener('activate', evt => {
  evt.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
  );
  self.clients.claim();
});

self.addEventListener('fetch', evt => {
  const url = evt.request.url;
  // Never intercept Firestore, Firebase auth, or the Anthropic API — always go to network.
  if (url.includes('firestore.googleapis.com') || url.includes('googleapis.com') ||
      url.includes('api.anthropic.com') || url.includes('gstatic.com') ||
      url.includes('cdnjs.cloudflare.com')) {
    return;
  }
  evt.respondWith(
    caches.match(evt.request).then(cached => cached || fetch(evt.request))
  );
});
