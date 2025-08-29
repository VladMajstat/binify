// === Binify Custom JS ===

// Copy to Clipboard functionality for code blocks and share links
document.addEventListener('DOMContentLoaded', function () {
    // Кнопка копіювання коду
    const copyBtn = document.getElementById('copy-btn');
    if (copyBtn) {
        copyBtn.addEventListener('click', function () {
            const code = document.querySelector('.code-block code');
            if (code) {
                navigator.clipboard.writeText(code.innerText).then(() => {
                    copyBtn.innerText = 'Скопійовано!';
                    setTimeout(() => copyBtn.innerText = 'Копіювати', 1500);
                });
            }
        });
    }

    // Кнопка копіювання посилання
    const shareBtn = document.getElementById('share-btn');
    if (shareBtn) {
        shareBtn.addEventListener('click', function () {
            navigator.clipboard.writeText(window.location.href).then(() => {
                shareBtn.innerText = 'Посилання скопійовано!';
                setTimeout(() => shareBtn.innerText = 'Поділитись', 1500);
            });
        });
    }

    // Highlight.js ініціалізація (якщо підключено)
    if (typeof hljs !== 'undefined') {
        document.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
    }
});