function attachLoadMoreHandler() {
    const loadMoreBtn = document.getElementById('load-more-btn');
    if (!loadMoreBtn) return;

    loadMoreBtn.onclick = function () {
        const nextPage = loadMoreBtn.getAttribute('data-next-page');
        fetch(window.location.pathname + `?page=${nextPage}`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
            .then(response => response.text())
            .then(html => {
                // Додаємо тільки нові біни (HTML з partial-шаблону)
                document.getElementById('bins-list').insertAdjacentHTML('beforeend', html);

                // Видаляємо стару кнопку
                loadMoreBtn.remove();

                // Якщо у відповіді є нова кнопка — додаємо її і навішуємо обробник
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const newBtn = doc.getElementById('load-more-btn');
                if (newBtn) {
                    document.querySelector('.d-flex.justify-content-center.mt-4').appendChild(newBtn);
                    attachLoadMoreHandler();
                }
            });
    };
}

// Підключаємо обробник після завантаження сторінки
document.addEventListener('DOMContentLoaded', attachLoadMoreHandler);