# Runbook Security, Debug Và Issue

Phiên bản: 2026-07-09

File này thay thế các tài liệu security/debug/production issue cũ và đã được cập nhật theo codebase hiện tại.

## Hiện Trạng Codebase

Project là Django ecommerce app dùng cấu hình chính tại `Project/settings.py`.
Sau refactor domain app, tài liệu kiến trúc/quy ước backend hiện nằm ở `docs/BACKEND-SKILL.md`.

Các file vận hành quan trọng:

- `Project/settings.py`: cấu hình Django, static, CORS/CSRF, security và logging.
- `App_Core/middleware.py`: chặn request đáng ngờ, giới hạn upload, ghi nhận page view.
- `App_Core/context_processors.py`: context dùng chung cho cart/menu/contact, có fallback an toàn.
- `App_Account/password_validation.py`: kiểm tra mật khẩu mạnh cho form tùy chỉnh.
- `scripts/3_security_tools.py`: công cụ hợp nhất cho production, debug và security.

Các lệnh production/security hiện tại đã gộp vào một script:

```bash
python scripts/3_security_tools.py deploy
python scripts/3_security_tools.py debug --verbose
python scripts/3_security_tools.py server
python scripts/3_security_tools.py monitor
python scripts/3_security_tools.py logs
python scripts/3_security_tools.py all
python scripts/3_security_tools.py refactor-audit
```

Không còn dùng các lệnh cũ như `scripts/debug_production.py`, `scripts/debug_server_errors.py`, `scripts/security_monitor.py`, `scripts/check_logs.py`, `scripts/start_production.sh`. Các tài liệu cũ có nhắc những file này đã lỗi thời.

## Cấu Hình Security

Thứ tự middleware hiện tại trong `Project/settings.py`:

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'App_Core.middleware.SecurityMiddleware',
    'App_Core.middleware.UploadLimitMiddleware',
    'App_Core.middleware.PageViewMiddleware',
]
```

`App_Core.middleware.SecurityMiddleware` chặn path và user-agent đáng ngờ, sau đó trả về 404 hoặc 403. Nhóm pattern đang chặn gồm PHP/WordPress probe, admin panel, `.env`, backup/log, SQL/database, Git/IDE, credential, SSH key và các extension script/executable.

Các ngoại lệ đang được cho phép:

- `robots.txt`
- `sitemap.xml`
- `favicon.ico`
- `.well-known/appspecific/com.chrome.devtools.json`
- `admin-guide`
- `static/quanly/products.zip`

`PageViewMiddleware` ghi log request đáng ngờ qua logger `App_Core` và đếm các public path trong model `PageView`. Middleware này không đếm `/admin/`, `/static/`, `/media/`, `/quanly/`, `/htmx/`.

`UploadLimitMiddleware` kiểm tra POST upload của user đã đăng nhập và từ chối request vượt `MAX_UPLOAD_REQUEST_SIZE` hoặc tổng dung lượng upload trong `App_Core.constants`.

Lưu ý production đã từng gặp:

- CKEditor upload ở `/tai-len/` bị chặn vì middleware từng tính quota bằng toàn bộ `settings.BASE_DIR`; VPS có source/static/log lớn sẽ vượt `MAX_UPLOAD_SIZE` dù `media/` chưa lớn. Quota phải tính theo `settings.MEDIA_ROOT`.
- CKEditor `SimpleUploadAdapter` cần response JSON. Nếu chặn upload, endpoint `/tai-len/` phải trả dạng `{"error": {"message": "..."}}` với HTTP 400, không trả `204` HTMX.
- Trang `/quan-ly/thong-tin-tai-khoan/` chỉ nên hiển thị dung lượng upload/media. Không quét toàn bộ `BASE_DIR` trong request vì production có thể timeout.

Security settings hiện tại:

```python
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = False
SECURE_SSL_REDIRECT = False
```

`SECURE_SSL_REDIRECT` đang tắt. Nếu HTTPS được terminate ở reverse proxy, cần cấu hình proxy đúng trước khi bật redirect trong Django.

## Logging

Logging được cấu hình trong `Project/settings.py` và ghi vào thư mục `logs/`. Thư mục này được tạo tự động khi settings load.

Log file hiện tại:

- `logs/debug.log`: debug/warning của `App_Core`.
- `logs/error.log`: lỗi Django và request error.
- `logs/debug_production.log`: output của `python scripts/3_security_tools.py debug`.

Handler đang dùng `logging.handlers.RotatingFileHandler`:

- `maxBytes = 5 * 1024 * 1024`
- `backupCount = 1`

Lệnh xem log nhanh:

```bash
tail -f logs/error.log
tail -f logs/debug.log
grep -i "blocked\|suspicious\|ERROR\|500" logs/*.log
```

## Static Files Và Rủi Ro Production

Static files dùng WhiteNoise manifest storage:

```python
STORAGES = {
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}
```

Khi `DEBUG=False`, manifest storage xử lý rất chặt. Template tham chiếu static file không tồn tại hoặc `staticfiles/manifest.json` chưa được tạo/cập nhật có thể gây lỗi 500. Ví dụ đã từng gặp: `/quan-ly/thong-tin-tai-khoan/` sập vì layout gọi `{% static 'website/img/hadona/favicon.ico' %}` trong khi production chưa có manifest mới.

Sau khi sửa static hoặc template có `{% static %}`, chạy:

```bash
python manage.py collectstatic --noinput
python manage.py check
```

Khi production bị 404 static hoặc 500 do template/static:

```bash
python scripts/3_security_tools.py server
python scripts/3_security_tools.py debug --verbose
```

Nếu lỗi chỉ xuất hiện khi `DEBUG=False`, tái tạo local bằng:

```bash
ENVIRONMENT=prod python manage.py collectstatic --noinput
ENVIRONMENT=prod python manage.py shell -c "from django.test import Client; from django.contrib.auth.models import User; u=User.objects.get(username='quanly'); c=Client(); c.force_login(u); r=c.get('/quan-ly/thong-tin-tai-khoan/'); print(r.status_code)"
```

## Lệnh Debug

Health check cơ bản:

```bash
python manage.py check
python manage.py check --deploy
python scripts/3_security_tools.py debug --check-only
```

Debug production chi tiết:

```bash
python scripts/3_security_tools.py debug --verbose
```

Lệnh này kiểm tra:

- `DEBUG`, `ENVIRONMENT`, `ALLOWED_HOSTS`
- kết nối database
- thư mục logs
- thư mục static/media
- số lượng model chính
- số lượng user/superuser
- `App_Core.context_processors.cart`
- Django system check và deployment check

Debug lỗi 500 thường gặp:

```bash
python scripts/3_security_tools.py server
```

Lệnh này test:

- dữ liệu `Category`, `Product`, `Subject`, `Post`
- context processor
- render `base.html` và `home.html`
- response `/` cho anonymous và authenticated user
- static file quan trọng
- lỗi gần đây trong `logs/error.log` và `logs/debug.log`

Tự sửa một số lỗi vận hành phổ biến:

```bash
python scripts/3_security_tools.py debug --fix-common
```

Lệnh này có thể tạo thư mục runtime bị thiếu, chạy migration và collect static. Trên production nên đọc output trước khi dùng.

Setup production:

```bash
python scripts/3_security_tools.py deploy
python scripts/3_security_tools.py deploy --quick
python scripts/3_security_tools.py deploy --skip-backup --skip-debug
```

`deploy` tạo thư mục runtime, tùy chọn backup `db.sqlite3`, chạy migration, collect static, chạy check và kiểm tra superuser.

## Security Monitoring

Phân tích path đáng ngờ trong bảng `PageView`:

```bash
python scripts/3_security_tools.py monitor
```

Quét Django log và web server log có sẵn:

```bash
python scripts/3_security_tools.py logs
```

Chạy cả hai:

```bash
python scripts/3_security_tools.py all
```

Xem top public path trong database:

```bash
python manage.py shell -c "from App_Core.models import PageView; [print(f'{p.path}: {p.view_count}') for p in PageView.objects.all().order_by('-view_count')[:10]]"
```

Khi phát hiện traffic đáng ngờ:

1. Kiểm tra `logs/debug.log` và `logs/error.log` quanh thời điểm đó.
2. Xác định IP, path, user-agent bị lặp.
3. Xác nhận path có phải false positive không.
4. Chỉ thêm ngoại lệ vào `allowed_files` nếu path thật sự public.
5. Chặn nguồn abuse ở reverse proxy, firewall, CDN hoặc hosting layer.
6. Chạy lại `python scripts/3_security_tools.py all`.

## Mẫu Issue Production Đã Gặp

Sự cố production cũ chủ yếu đến từ:

- thiếu static file gây 404
- WhiteNoise manifest hoặc template static gây 500
- context processor crash làm trang render không đầy đủ
- JavaScript gắn event vào element không tồn tại
- modal HTMX admin trỏ nhầm `data-bs-target` sang modal không tồn tại (`#addModal`) thay vì để `#dialog` tự mở qua JS
- script inline trong fragment HTMX chạy lại gây `$ is not defined` hoặc `redeclaration` nếu dùng jQuery/biến global
- signal receiver viết sai vị trí, ví dụ `@receiver(...)` treo trước class khác, gây 500 khi xóa cascade

Codebase hiện tại đã có các điểm giảm rủi ro:

- `App_Core.context_processors.cart` bắt exception và trả default an toàn.
- view `home` bắt exception và render collection rỗng.
- logging đã bật cho Django request error và warning của `App_Core`.
- `scripts/3_security_tools.py server` test trực tiếp các đường lỗi 500 cũ.
- quy ước HTMX/admin và signal receiver được ghi trong `docs/FRONTEND-SKILL.md` và `docs/BACKEND-SKILL.md`.

Khi site chỉ hiện layout base, trả 500, hoặc mất CSS/JS:

```bash
python scripts/3_security_tools.py server
tail -50 logs/error.log
python manage.py collectstatic --noinput
python manage.py check
```

Khi lỗi chỉ xảy ra trong modal quản lý:

```bash
rg -n "data-bs-target=\"#addModal\"|\\$\\(|\\.ajax|@receiver\\(" templates/quanly App_Post App_Product App_Quanly
python manage.py check
```

Sau đó test lại flow trên browser: mở add/edit modal 2 lần liên tiếp, bấm `Lưu`, bấm `Xóa` trên bản ghi test và kiểm tra console + network không còn 500.

Nếu lỗi liên quan static manifest, sửa đường dẫn `{% static %}` trong template hoặc khôi phục static file bị thiếu, rồi chạy lại `collectstatic`.

## Contact Và Password Reset

Hiện tại `App_Core.views.contact` và `contact_modal` validate `ContactForm`, tạo `Contact`, rồi gửi email tới user `quanly`. `ContactForm` hiện để các field optional và chưa có honeypot/rate limit trong codebase này.

Hiện tại `password_reset_request`:

- dùng `CustomPasswordResetForm`
- gửi email reset cho user tồn tại
- trả lỗi rõ ràng "Email không tồn tại." nếu email không có trong hệ thống
- dùng `request.META['HTTP_HOST']`

Khuyến nghị hardening tiếp theo:

- đặt required field rõ ràng cho form liên hệ nếu nghiệp vụ cần
- thêm honeypot và rate limit cho contact form public
- tránh account enumeration trong password reset bằng cách luôn chuyển sang trang done khi form hợp lệ
- dùng `request.get_host()` thay cho `request.META['HTTP_HOST']`
- thêm email timeout nếu SMTP/Gmail chậm gây treo request

Tài liệu cũ `session-email-security-logging.md` mô tả app/module khác (`App_home`, `App_book`), không khớp trạng thái repository này.

## Checklist Deploy

Trước deploy:

```bash
python manage.py check
python scripts/3_security_tools.py debug --check-only
python manage.py collectstatic --noinput
```

Production cần có các biến môi trường:

- `SECRET_KEY`
- `DOMAIN`
- `VPS`
- `EMAIL_PORT`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `ENVIRONMENT=prod` hoặc giá trị non-dev đang dùng

Sau deploy:

```bash
python scripts/3_security_tools.py server
python scripts/3_security_tools.py all
tail -50 logs/error.log
```

Checklist vận hành:

- tạo hoặc kiểm tra superuser
- kiểm tra `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `CORS_ALLOWED_ORIGINS`
- kiểm tra HTTPS, reverse proxy và cookie secure
- kiểm tra Redis nếu dùng Celery
- test checkout, contact, login, password reset và admin

## Troubleshooting Matrix

| Triệu chứng | Lệnh kiểm tra đầu tiên | Hướng xử lý |
| --- | --- | --- |
| Home page 500 | `python scripts/3_security_tools.py server` | Sửa lỗi context/template/static trong output hoặc log |
| CSS/JS không load | `python manage.py collectstatic --noinput` | Khôi phục static file thiếu hoặc sửa template static path |
| Probe đáng ngờ | `python scripts/3_security_tools.py all` | Chặn IP abuse và cập nhật middleware rule thật hẹp |
| CKEditor không upload ảnh trên VPS nhưng paste ảnh được | Network tab request `/tai-len/`, log Django, kiểm tra quota trong `UploadLimitMiddleware` | Quota phải tính `MEDIA_ROOT`; lỗi CKEditor phải trả JSON `{"error": {"message": "..."}}` |
| Upload bị từ chối | Kiểm tra `App_Core.constants` và dung lượng `MEDIA_ROOT` | Điều chỉnh upload/request/media cap có chủ đích |
| Database lỗi | `python manage.py check` và `python manage.py migrate` | Chạy migration hoặc restore DB backup |
| Chưa có admin | `python manage.py createsuperuser` | Tạo production superuser |
| Static 500 khi `DEBUG=False` | `python scripts/3_security_tools.py server` hoặc `python manage.py collectstatic --noinput` | Sửa file thiếu trong WhiteNoise manifest, chạy lại `collectstatic`, restart app |
| `/quan-ly/thong-tin-tai-khoan/` chậm hoặc không mở production | Test bằng `ENVIRONMENT=prod` và user `quanly` | Không quét `BASE_DIR`; chỉ dùng `MEDIA_ROOT` cho dung lượng upload |

## Lịch Sử Gộp File

Các tài liệu cũ dưới đây đã được gộp vào tài liệu hiện tại và không còn là đường dẫn docs đang dùng:

- `QUICK_START.md`
- `SECURITY_GUIDE.md`
- `README_SECURITY.md`
- `SECURITY_UPDATE.md`
- `PRODUCTION_DEBUG_GUIDE.md`
- `README_DEBUG.md`
- `PRODUCTION_ISSUE_SUMMARY.md`
- `session-email-security-logging.md`
