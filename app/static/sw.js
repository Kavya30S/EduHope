self.addEventListener('install', event => {
    event.waitUntil(
        caches.open('edu-hope-v1').then(cache => {
            return cache.addAll([
                '/',
                '/static/css/style.css',
                '/static/js/main.js',
                '/templates/pet.html'
            ]);
        })
    );
});

self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request).then(response => {
            return response || fetch(event.request);
        })
    );
});