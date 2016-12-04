$(function () {
    $('.remember-input').each(function (i, input) {
        $(input).val(Cookies.get($(input).attr('name'), ''));
    });
    $('.remember-input-form').submit(function (e) {
        $('.remember-input').each(function (i, input) {
            Cookies.set($(input).attr('name'), $(input).val(), { path: '' });
        });
    });
});
