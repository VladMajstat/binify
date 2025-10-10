document.addEventListener('DOMContentLoaded', function() {
    // Отримуємо hash біна та CSRF-токен з window
    const binHash = window.BIN_HASH;
    const csrfToken = window.CSRF_TOKEN;

    // Функція для отримання та оновлення лічильників лайків/дизлайків
    function updateLikesDislikes() {
        // GET-запит на сервер для отримання поточних значень
        fetch(`/bins/bin_likes_dislikes/${binHash}/`, )
            .then(response => response.json())
            .then(data => {
                // Оновлюємо текст кнопок лайк/дизлайк
                document.getElementById('like-btn').innerText = `👍 ${data.likes}`;
                document.getElementById('dislike-btn').innerText = `👎 ${data.dislikes}`;
            });
    }

    // Початкове оновлення лічильників при завантаженні сторінки
    updateLikesDislikes();

    // Обробник кліку на кнопку лайк
    document.getElementById('like-btn').onclick = function() {
        // POST-запит на сервер для додавання/оновлення лайка
        fetch(`/bins/bin_likes_dislikes/${binHash}/`, {
            method: 'POST',
            headers: {'X-CSRFToken': csrfToken},
            body: new URLSearchParams({'is_like': 'true'})
        })
        .then(response => response.json())
        .then(data => {
            // Оновлюємо текст кнопок лайк/дизлайк після відповіді
            document.getElementById('like-btn').innerText = `👍 ${data.likes}`;
            document.getElementById('dislike-btn').innerText = `👎 ${data.dislikes}`;
        });
    };

    // Обробник кліку на кнопку дизлайк
    document.getElementById('dislike-btn').onclick = function() {
        // POST-запит на сервер для додавання/оновлення дизлайка
        fetch(`/bins/bin_likes_dislikes/${binHash}/`, {
            method: 'POST',
            headers: {'X-CSRFToken': csrfToken},
            body: new URLSearchParams({'is_like': 'false'})
        })
        .then(response => response.json())
        .then(data => {
            // Оновлюємо текст кнопок лайк/дизлайк після відповіді
            document.getElementById('like-btn').innerText = `👍 ${data.likes}`;
            document.getElementById('dislike-btn').innerText = `👎 ${data.dislikes}`;
        });
    };
});
