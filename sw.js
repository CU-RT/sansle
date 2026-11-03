const CACHE = "sansle-v3";
const SHELL = ["./", "index.html", "manifest.webmanifest", "icon-192.png", "icon-512.png", "apple-touch-icon.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});
/* Pages come from the network when possible, so updates arrive, and from the cache when offline. Everything else is cache first. */
self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  /* Account data must always be live, never a cached copy. */
  if (new URL(e.request.url).hostname.endsWith(".supabase.co")) return;
  const save = (res) => {
    if (res && (res.ok || res.type === "opaque")) {
      const copy = res.clone();
      caches.open(CACHE).then((c) => c.put(e.request, copy));
    }
    return res;
  };
  if (e.request.mode === "navigate") {
    e.respondWith(fetch(e.request).then(save).catch(() => caches.match("index.html")));
    return;
  }
  e.respondWith(caches.match(e.request).then((hit) => hit || fetch(e.request).then(save)));
});
