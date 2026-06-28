const CACHE_NAME = "logos-offline-v1";

const lstAssetsToCache = [
    "/offline",
    "/static/css/style.css",
    "/static/icons/logo.svg"
];

// On install, pre-cache the offline page and the assets it needs to stay styled.
self.addEventListener("install", (vEvent) => {
    vEvent.waitUntil(
        caches.open(CACHE_NAME).then((vCache) => vCache.addAll(lstAssetsToCache))
    );
    self.skipWaiting();
});

// On activate, drop any caches left over from a previous version.
self.addEventListener("activate", (vEvent) => {
    vEvent.waitUntil(
        caches.keys().then((lstCacheNames) =>
            Promise.all(
                lstCacheNames
                    .filter((vCacheName) => vCacheName !== CACHE_NAME)
                    .map((vCacheName) => caches.delete(vCacheName))
            )
        )
    );
    self.clients.claim();
});

// Serve cached assets when possible; fall back to the offline page when a
// navigation fails because there is no connection.
self.addEventListener("fetch", (vEvent) => {
    if (vEvent.request.mode === "navigate") {
        vEvent.respondWith(
            fetch(vEvent.request).catch(() => caches.match("/offline"))
        );
        return;
    }

    vEvent.respondWith(
        caches.match(vEvent.request).then((vCachedResponse) => vCachedResponse || fetch(vEvent.request))
    );
});
