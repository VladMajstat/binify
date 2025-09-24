document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll('textarea.autosize').forEach(function (textarea) {
        function resize() {
            textarea.style.height = 'auto';
            textarea.style.height = textarea.scrollHeight + 'px';
        }
        textarea.addEventListener('input', resize);
        resize(); // ініціалізація при завантаженні
    });
});