// Service Worker for Offline Functionality
const CACHE_NAME = 'eduhope-v1.2.0';
const urlsToCache = [
    '/',
    '/static/css/style.css',
    '/static/js/main.js',
    '/static/js/pet.js',
    '/static/js/storytelling.js',
    '/static/js/language_game.js',
    '/static/js/math_maze.js',
    '/static/images/logo.png',
    '/static/images/pets/',
    '/dashboard',
    '/pet',
    '/offline.html'
];

// Install event - cache resources
self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function(cache) {
                console.log('Opened cache');
                return cache.addAll([
                    '/',
                    '/static/css/style.css',
                    '/static/js/main.js',
                    '/dashboard'
                ].filter(Boolean));
            })
            .catch(function(error) {
                console.error('Cache installation failed:', error);
            })
    );
});

// Fetch event - serve from cache when offline
self.addEventListener('fetch', function(event) {
    event.respondWith(
        caches.match(event.request)
            .then(function(response) {
                // Return cached version if available
                if (response) {
                    return response;
                }
                
                // Otherwise fetch from network
                return fetch(event.request).then(function(response) {
                    // Don't cache non-successful responses
                    if (!response || response.status !== 200 || response.type !== 'basic') {
                        return response;
                    }
                    
                    // Clone the response for caching
                    const responseToCache = response.clone();
                    
                    caches.open(CACHE_NAME)
                        .then(function(cache) {
                            cache.put(event.request, responseToCache);
                        });
                    
                    return response;
                }).catch(function() {
                    // If fetch fails and no cache, return offline page
                    if (event.request.destination === 'document') {
                        return caches.match('/offline.html');
                    }
                });
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', function(event) {
    event.waitUntil(
        caches.keys().then(function(cacheNames) {
            return Promise.all(
                cacheNames.map(function(cacheName) {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// Background sync for offline actions
self.addEventListener('sync', function(event) {
    if (event.tag === 'background-sync') {
        event.waitUntil(doBackgroundSync());
    }
});

function doBackgroundSync() {
    // Sync offline actions when connection is restored
    return new Promise((resolve) => {
        const offlineActions = JSON.parse(localStorage.getItem('offlineActions') || '[]');
        
        if (offlineActions.length > 0) {
            Promise.all(offlineActions.map(action => {
                return fetch('/api/sync', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(action)
                });
            })).then(() => {
                localStorage.removeItem('offlineActions');
                resolve();
            });
        } else {
            resolve();
        }
    });
}

// Push notifications for learning reminders
self.addEventListener('push', function(event) {
    const options = {
        body: event.data ? event.data.text() : 'Time for learning!',
        icon: '/static/images/logo.png',
        badge: '/static/images/badge.png',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: '2'
        },
        actions: [
            {
                action: 'explore',
                title: 'Start Learning',
                icon: '/static/images/checkmark.png'
            },
            {
                action: 'close',
                title: 'Later',
                icon: '/static/images/xmark.png'
            }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification('EduHope Learning Reminder', options)
    );
});

// Handle notification clicks
self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    
    if (event.action === 'explore') {
        // Open the app and navigate to dashboard
        event.waitUntil(
            clients.openWindow('/dashboard')
        );
    }
});