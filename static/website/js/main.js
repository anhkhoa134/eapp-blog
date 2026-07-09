/*
 * PTcom — main.js
 * JS chính cho giao diện website (vanilla JS, không cần jQuery).
 * Thay thế static/007-eshopper/js/main.js (jQuery + easing + owl carousel).
 */
(function () {
    'use strict';

    // Nút "Back to top": hiện khi cuộn xuống, click cuộn mượt lên đầu trang
    const backToTop = document.querySelector('.back-to-top');
    if (backToTop) {
        window.addEventListener('scroll', function () {
            backToTop.classList.toggle('show', window.scrollY > 100);
        }, { passive: true });

        backToTop.addEventListener('click', function (e) {
            e.preventDefault();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    // Vendor strip: nhân đôi nội dung track để marquee CSS chạy vòng lặp liền mạch
    // (keyframe vendor-scroll dịch translateX(-50%) nên cần 2 bản nội dung giống nhau)
    document.querySelectorAll('.vendor-strip .vendor-track').forEach(function (track) {
        Array.from(track.children).forEach(function (item) {
            const clone = item.cloneNode(true);
            clone.setAttribute('aria-hidden', 'true');
            track.appendChild(clone);
        });
    });
})();
