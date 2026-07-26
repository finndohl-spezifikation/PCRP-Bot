// PCRP City Chat Service Worker
// Empfängt Push-Benachrichtigungen und zeigt iOS-/Android-Notifications

self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(clients.claim()));

self.addEventListener('push', event => {
  let data = {};
  try { data = event.data ? event.data.json() : {}; } catch (e) {}

  const title   = data.title || 'City Chat';
  const options = {
    body:      data.body  || '',
    icon:      '/icon-192.png',
    badge:     '/badge-72.png',
    vibrate:   [200, 100, 200],
    tag:       'cc-msg-' + (data.from || 'unknown'),
    renotify:  true,
    data:      { url: data.url || '/city-chat' }
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  const target = (event.notification.data && event.notification.data.url) || '/city-chat';
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(list => {
      for (const c of list) {
        if (c.url.includes('/city-chat')) { return c.focus(); }
      }
      return clients.openWindow(target);
    })
  );
});
