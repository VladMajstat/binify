document.addEventListener('DOMContentLoaded', function () {
    // Копіювання контенту біна
    const copyBtn = document.getElementById('copy-btn');
    if (copyBtn) {
        copyBtn.onclick = function () {
            const content = document.getElementById('bin-content').textContent;
            navigator.clipboard.writeText(content);
            this.innerText = "Скопійовано!";
            setTimeout(() => this.innerText = "Копіювати", 1500);
        }
    }
    // Копіювання URL сторінки
    const shareBtn = document.getElementById('share-btn');
    if (shareBtn) {
        shareBtn.onclick = function () {
            navigator.clipboard.writeText(window.location.href);
            this.innerText = "Скопійовано!";
            setTimeout(() => this.innerText = "URL", 1500);
        }
    }
});