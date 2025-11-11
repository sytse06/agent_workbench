// Service Worker for Agent Workbench PWA
// Implements caching strategies for offline functionality

const CACHE_NAME = 'agent-workbench-v1';
const STATIC_CACHE = 'agent-workbench-static-v1';
const API_CACHE = 'agent-workbench-api-v1';

// Static assets to cache
const STATIC_ASSETS = [
  '/',
  '/static/manifest.json',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/static/icons/apple-touch-icon.png',
  '/static/offline.html',
  // CSS files (unified architecture)
  '/static/assets/css/main.css',
  '/static/assets/css/fonts.css',
  '/static/assets/css/shared.css',
  '/static/assets/css/settings.css',
  '/static/assets/css/seo-coach.css'
];

// Install event - cache static assets
self.addEventListener('install', event => {
  console.log('Service Worker: Installing...');
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => {
        console.log('Service Worker: Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('Service Worker: Static assets cached');
        return self.skipWaiting();
      })
      .catch(error => {
        console.error('Service Worker: Failed to cache static assets', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('Service Worker: Activating...');
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            if (cacheName !== STATIC_CACHE && cacheName !== API_CACHE) {
              console.log('Service Worker: Deleting old cache', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('Service Worker: Activated');
        return self.clients.claim();
      })
  );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Handle different types of requests with appropriate caching strategies
  if (request.method === 'GET') {
    // Static assets - cache first
    if (STATIC_ASSETS.includes(url.pathname) || url.pathname.startsWith('/static/')) {
      event.respondWith(cacheFirst(request, STATIC_CACHE));
    }
    // API requests - network first with cache fallback
    else if (url.pathname.startsWith('/api/')) {
      event.respondWith(networkFirst(request, API_CACHE));
    }
    // HTML pages - network first with offline fallback
    else if (request.headers.get('accept')?.includes('text/html')) {
      event.respondWith(networkFirstWithOfflineFallback(request));
    }
    // Other requests - network first
    else {
      event.respondWith(networkFirst(request, CACHE_NAME));
    }
  }
});

// Cache-first strategy for static assets
async function cacheFirst(request, cacheName) {
  try {
    const cache = await caches.open(cacheName);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
      console.log('Service Worker: Serving from cache', request.url);
      return cachedResponse;
    }
    
    console.log('Service Worker: Fetching and caching', request.url);
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.error('Service Worker: Cache-first failed', error);
    throw error;
  }
}

// Network-first strategy with cache fallback
async function networkFirst(request, cacheName) {
  try {
    console.log('Service Worker: Network-first for', request.url);
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.log('Service Worker: Network failed, trying cache', request.url);
    const cache = await caches.open(cacheName);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
      return cachedResponse;
    }
    
    throw error;
  }
}

// Network-first with offline fallback for HTML pages
async function networkFirstWithOfflineFallback(request) {
  try {
    const networkResponse = await fetch(request);
    return networkResponse;
  } catch (error) {
    console.log('Service Worker: Network failed, serving offline page');
    const cache = await caches.open(STATIC_CACHE);
    const offlinePage = await cache.match('/static/offline.html');
    
    if (offlinePage) {
      return offlinePage;
    }
    
    // Fallback response if offline page is not available
    return new Response(
      '<html><body><h1>Offline</h1><p>You are currently offline. Please check your internet connection.</p></body></html>',
      {
        status: 200,
        statusText: 'OK',
        headers: { 'Content-Type': 'text/html' }
      }
    );
  }
}

// Background sync for conversation data
self.addEventListener('sync', event => {
  if (event.tag === 'conversation-sync') {
    console.log('Service Worker: Background sync for conversations');
    event.waitUntil(syncConversations());
  }
});

// Sync conversations when back online
async function syncConversations() {
  try {
    // Get pending conversations from IndexedDB
    const pendingConversations = await getPendingConversations();
    
    for (const conversation of pendingConversations) {
      try {
        const response = await fetch('/api/conversations', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(conversation)
        });
        
        if (response.ok) {
          await removePendingConversation(conversation.id);
          console.log('Service Worker: Synced conversation', conversation.id);
        }
      } catch (error) {
        console.error('Service Worker: Failed to sync conversation', error);
      }
    }
  } catch (error) {
    console.error('Service Worker: Background sync failed', error);
  }
}

// IndexedDB helpers for offline conversation storage
async function getPendingConversations() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('agent-workbench-offline', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction(['conversations'], 'readonly');
      const store = transaction.objectStore('conversations');
      const getAllRequest = store.getAll();
      
      getAllRequest.onsuccess = () => resolve(getAllRequest.result);
      getAllRequest.onerror = () => reject(getAllRequest.error);
    };
    
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains('conversations')) {
        db.createObjectStore('conversations', { keyPath: 'id' });
      }
    };
  });
}

async function removePendingConversation(id) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('agent-workbench-offline', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction(['conversations'], 'readwrite');
      const store = transaction.objectStore('conversations');
      const deleteRequest = store.delete(id);
      
      deleteRequest.onsuccess = () => resolve();
      deleteRequest.onerror = () => reject(deleteRequest.error);
    };
  });
}

// Push notification handling
self.addEventListener('push', event => {
  if (event.data) {
    const data = event.data.json();
    console.log('Service Worker: Push notification received', data);
    
    const options = {
      body: data.body,
      icon: '/static/icons/icon-192.png',
      badge: '/static/icons/icon-192.png',
      tag: 'agent-workbench-notification',
      requireInteraction: false,
      actions: [
        {
          action: 'open',
          title: 'Open App'
        },
        {
          action: 'dismiss',
          title: 'Dismiss'
        }
      ]
    };
    
    event.waitUntil(
      self.registration.showNotification(data.title || 'Agent Workbench', options)
    );
  }
});

// Notification click handling
self.addEventListener('notificationclick', event => {
  event.notification.close();
  
  if (event.action === 'open' || !event.action) {
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

console.log('Service Worker: Loaded and ready');
