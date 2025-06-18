if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/sw.js')
        .then(() => console.log('Service Worker Registered'))
        .catch(err => console.log('Service Worker Error:', err));
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('EduHope app loaded!');
});