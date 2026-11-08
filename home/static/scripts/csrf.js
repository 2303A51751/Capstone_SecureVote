// CSRF Handler for Django AJAX
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    // Fallback: look for hidden input
    if (!cookieValue) {
        var el = document.querySelector('[name=csrfmiddlewaretoken]');
        if (el) cookieValue = el.value;
    }
    return cookieValue;
}

function csrfSafeMethod(method) {
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            var token = getCookie('csrftoken');
            if (token) {
                xhr.setRequestHeader("X-CSRFToken", token);
            }
        }
    }
});
