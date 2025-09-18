$(document).ready(function () {
    $('#comment-form').on('submit', function (e) {
        e.preventDefault();
        console.log('AJAX submit!');
        $.ajax({
            url: "/bins/bin_comment/" + window.BIN_ID + "/",
            type: "POST",
            data: $(this).serialize(),
            headers: { "X-CSRFToken": window.CSRF_TOKEN },
            success: function (response) {
                if (response.success) {
                    $('#comment-messages').html('<div class="success">Коментар додано!</div>');
                    $('#comments-list').prepend(response.comment_html);
                    $('#comment-form')[0].reset();
                } else {
                    $('#comment-messages').html('<div class="error">' + response.error + '</div>');
                }
            },
            error: function (xhr) {
                $('#comment-messages').html('<div class="error">Сталася помилка. Спробуйте ще раз.</div>');
            }
        });
    });
});