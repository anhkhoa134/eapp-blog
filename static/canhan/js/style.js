// <!-- CSRF: đồng bộ token mới nhất từ cookie csrftoken trước khi submit form / gửi HTMX request -->
// Tránh lỗi "CSRF verification failed" khi hidden token trong HTML bị cũ (trang cache, back/forward, token rotate)
function getCsrfCookie() {
    const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : null;
}

// Form thường: cập nhật hidden input csrfmiddlewaretoken theo cookie ngay trước khi submit
document.addEventListener('submit', (event) => {
    const form = event.target;
    if (!form || !form.querySelector) {
        return;
    }
    const input = form.querySelector('input[name="csrfmiddlewaretoken"]');
    const token = getCsrfCookie();
    if (input && token) {
        input.value = token;
    }
}, true);

// HTMX request: set header X-CSRFToken và đồng bộ csrfmiddlewaretoken trong body theo cookie
if (window.htmx) {
    document.body.addEventListener('htmx:configRequest', (event) => {
        const token = getCsrfCookie();
        if (!token) {
            return;
        }
        event.detail.headers['X-CSRFToken'] = token;
        if (event.detail.parameters && event.detail.parameters.csrfmiddlewaretoken) {
            event.detail.parameters.csrfmiddlewaretoken = token;
        }
    });
}

// <!-- Spinner cho loading page + upload file: hiển thị ngay lập tức -->
// Hiển thị spinner
function showSpinner() {
    const spinner = document.getElementById('spinner');
    if (spinner) {
        spinner.classList.add('show');
    }
}

// Ẩn spinner
function hideSpinner() {
    const spinner = document.getElementById('spinner');
    if (spinner) {
        spinner.classList.remove('show');
    }
}

// Hiển thị spinner ngay khi tải trang bắt đầu
document.addEventListener('DOMContentLoaded', () => {
    showSpinner();
});

// Ẩn spinner khi trang tải xong
window.addEventListener('load', () => {
    hideSpinner();
});

// Spinner khi sử dụng HTMX (nếu có)
if (window.htmx) {
    document.body.addEventListener('htmx:configRequest', (event) => {
        showSpinner();
    });

    document.body.addEventListener('htmx:afterRequest', (event) => {
        hideSpinner();
    });
}




// <!-- HTMX Modal Form -->
// dialog.js
;(function () {
    const modal = new bootstrap.Modal(document.getElementById("modal"))

    htmx.on("htmx:afterSwap", (e) => {
    // Response targeting #dialog => show the modal
    if (e.detail.target.id == "dialog") {
        modal.show()
    }
    })

    htmx.on("htmx:beforeSwap", (e) => {
    // Empty response targeting #dialog => hide the modal
    if (e.detail.target.id == "dialog" && !e.detail.xhr.response) {
        modal.hide()
        e.detail.shouldSwap = false
    }
    })

    // Remove dialog content after hiding
    htmx.on("hidden.bs.modal", () => {
    document.getElementById("dialog").innerHTML = ""
    })
})()      

// <!-- HTMX Toast Message -->
// toast_HTMX.js
document.body.addEventListener('htmx:afterRequest', (event) => {
    const triggerData = event.detail.xhr.getResponseHeader('HX-Trigger');
    if (triggerData) {
    const triggers = JSON.parse(triggerData);
    if (triggers.showMessage) {
        // console.log('Show Message:', triggers.showMessage); // Log the showMessage trigger
        showMessage(triggers.showMessage.message, triggers.showMessage.type);
    }}
});

document.body.addEventListener('htmx:afterRequest', (event) => {
    const status = event.detail.xhr.status;
    const isSuccess = status >= 200 && status < 300;
    if (!isSuccess || !event.detail.elt) {
        return;
    }

    const addCartButton = event.detail.elt.closest('.btn-add-cart');
    if (addCartButton) {
        runCartButtonEffect(addCartButton);
    }
});

document.body.addEventListener('htmx:afterSwap', (event) => {
    const target = event.detail.target;
    if (!target || !target.matches || !target.matches('.btn-wishlist')) {
        return;
    }

    runIconPop(target);
});

function showMessage(message, type) {
    const toastElement = document.getElementById("toast-bg-htmx");
    const toastBody = document.getElementById("toast-body-htmx");
    toastBody.innerText = message;
    const toastType = type || 'bg-success'; // Default to bg-success
    toastElement.className = `toast align-items-center text-white border-0 ${toastType}`;

    const newToast = toastElement.cloneNode(true);
    newToast.id = ''; // Remove ID to avoid duplicates
    document.getElementById('toastContainer').appendChild(newToast);

    const toast_HTMX = new bootstrap.Toast(newToast, { delay: 1500 });
    toast_HTMX.show();
}

function runCartButtonEffect(button) {
    const icon = button.querySelector('i');
    if (!icon) {
        return;
    }

    if (!button.dataset.originalIconClass) {
        button.dataset.originalIconClass = icon.className;
    }

    window.clearTimeout(button._iconEffectTimer);
    icon.className = 'fas fa-check';
    button.classList.add('is-confirmed');
    runIconPop(button);

    button._iconEffectTimer = window.setTimeout(() => {
        icon.className = button.dataset.originalIconClass;
        button.classList.remove('is-confirmed');
    }, 900);
}

function runIconPop(element) {
    element.classList.remove('icon-effect-pop');
    void element.offsetWidth;
    element.classList.add('icon-effect-pop');

    window.setTimeout(() => {
        element.classList.remove('icon-effect-pop');
    }, 450);
}

document.addEventListener('click', (event) => {
    const button = event.target.closest('.password-toggle');
    if (!button) {
        return;
    }

    const field = button.closest('.password-field');
    const input = field ? field.querySelector('input') : null;
    const icon = button.querySelector('i');
    if (!input) {
        return;
    }

    const shouldShow = input.type === 'password';
    input.type = shouldShow ? 'text' : 'password';
    input.dataset.passwordVisible = shouldShow ? 'true' : 'false';
    button.setAttribute('aria-pressed', shouldShow ? 'true' : 'false');
    button.setAttribute('aria-label', shouldShow ? 'Ẩn mật khẩu' : 'Hiện mật khẩu');
    button.setAttribute('title', shouldShow ? 'Ẩn mật khẩu' : 'Hiện mật khẩu');

    if (icon) {
        icon.className = shouldShow ? 'bi bi-eye-slash' : 'bi bi-eye';
    }

    input.focus({ preventScroll: true });
});
    
// <!-- Toast Message Django -->
// toast_message.js
var toast_message = document.getElementById('toast_message');
// Kiểm tra xem toast có tồn tại không
if (toast_message) {
    // Lấy nội dung của toast
    var toastBody = toast_message.querySelector('.toast-body');
    var message = toastBody.textContent.trim();

    // Nếu toast có nội dung, hiển thị nó
    if (message !== "") {
        var bootstrapToast = new bootstrap.Toast(toast_message, {
        autohide: true, // Tự động ẩn toast sau khoảng thời gian đã đặt
        delay: 1500 // Thời gian hiển thị toast (1.5 giây)
        });
        bootstrapToast.show(); // Hiển thị toast
    }
};

// Nút "Back to top" (.back-to-top) đã xử lý trong static/007-eshopper/js/main.js (jQuery).
// Không dùng #btn-back-to-top + window.onscroll ở đây — id không khớp base.html và ghi đè onscroll.
