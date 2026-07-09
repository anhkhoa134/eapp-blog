# Hướng dẫn chi tiết: Đăng nhập Google (Django + django-allauth)

Tài liệu này hướng dẫn từ đầu đến cuối để kích hoạt đăng nhập Google cho project `linhkienv92`.

## Quick checklist trước khi demo production

- [ ] Đã thêm redirect URI production trên Google Console:
  - `https://linhkienv92.vn/accounts/google/login/callback/`
  - `https://www.linhkienv92.vn/accounts/google/login/callback/`
- [ ] Server production đã set đúng `GOOGLE_CLIENT_ID` và `GOOGLE_CLIENT_SECRET`.
- [ ] Đã chạy `python manage.py setup_google_socialapp` trên môi trường production.
- [ ] Không cấu hình trùng nguồn credentials (chỉ dùng DB `SocialApp`, không đặt thêm `SOCIALACCOUNT_PROVIDERS['google']['APP']`).
- [ ] Đã restart app process (gunicorn/uvicorn/systemd) sau khi cập nhật env/settings.
- [ ] Truy cập thử URL `/accounts/google/login/` và xác nhận redirect sang Google thành công.

## 1) Điều kiện cần

- Đã cài package `django-allauth` trong virtualenv đang chạy.
- Project đã có các thay đổi backend:
  - `Project/settings.py`: thêm `allauth`, `sites`, middleware, auth backends.
  - `Project/settings.py`: **không** đặt `SOCIALACCOUNT_PROVIDERS['google']['APP']` khi đã dùng `SocialApp` trong DB.
  - `Project/urls.py`: thêm `path('accounts/', include('allauth.urls'))`.
- Đã migrate DB (`sites`, `account`, `socialaccount`).
- pip install django-allauth==0.57.0

## 2) Tạo OAuth Credentials trên Google Cloud

Lưu ý: Đăng nhập Google web cần **OAuth Client (Web application)**, không dùng file `service_account.json`.

### Bước 2.1: Chọn project

1. Mở [Google Cloud Console](https://console.cloud.google.com/).
2. Chọn đúng project (ví dụ: `django-430004`).

### Bước 2.2: Bật API

1. Vào `APIs & Services` -> `Library`.
2. Tìm và bật `Google People API`.

### Bước 2.3: OAuth Consent Screen

1. Vào `APIs & Services` -> `OAuth consent screen` -> `Branding`.
2. Chọn loại app (`External` nếu user bên ngoài tổ chức).
3. Điền thông tin cơ bản:
   - App name
   - Support email
   - Developer contact email
4. Thêm scope nếu được yêu cầu: `openid`, `email`, `profile`.
5. Nếu app ở chế độ Testing, thêm tài khoản của bạn vào `Test users`.

### Bước 2.4: Tạo OAuth Client ID

1. Vào `APIs & Services` -> `Credentials`.
2. Bấm `Create Credentials` -> `OAuth client ID`.
3. Chọn `Application type`: **Web application**.
4. Đặt tên (ví dụ: `linhkienv92-web`).
5. Thêm `Authorized redirect URIs`:

   Local:
   - `http://127.0.0.1:8000/accounts/google/login/callback/`
   - `http://localhost:8000/accounts/google/login/callback/`

   Production:
   - `https://linhkienv92.vn/accounts/google/login/callback/`
   - `https://www.linhkienv92.vn/accounts/google/login/callback/`

6. Bấm `Create`.
7. Copy:
   - `Client ID` -> `GOOGLE_CLIENT_ID`
   - `Client secret` -> `GOOGLE_CLIENT_SECRET`

## 3) Thêm biến môi trường

Thêm vào file `.env` (hoặc system env):

```env
GOOGLE_CLIENT_ID=xxxxxxxxxxxxxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxxxxxxxxxxxxxxx
```

Sau đó restart process Django.

## 4) Nguyên tắc cấu hình (tránh trùng lặp)

Chỉ nên chọn **1 trong 2 cách**:

- Cách A (khuyến nghị cho project này): lưu credentials trong DB qua model `SocialApp`.
- Cách B: khai báo trực tiếp trong `settings.py` bằng `SOCIALACCOUNT_PROVIDERS['google']['APP']`.

Nếu dùng đồng thời A + B, allauth có thể báo lỗi `MultipleObjectsReturned` khi vào `/accounts/google/login/`.

Project này đã được chuẩn hóa theo **Cách A**.

## 5) Tạo/Cập nhật SocialApp tự động

### Có cần tạo file `setup_google_socialapp.py` và chạy không?

Có, **nếu bạn đang cấu hình theo Cách A** (khuyến nghị cho project này): lưu credentials trong DB qua model `SocialApp`.

Vì allauth sẽ đọc `client_id/secret` từ DB, nên bạn cần **tạo/cập nhật** bản ghi `SocialApp` và gắn với `Site` tương ứng:

- **Local (SQLite/dev DB)**: chạy ít nhất 1 lần sau khi migrate và sau khi thay đổi `GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET`.
- **Production (Postgres/prod DB)**: chạy ít nhất 1 lần sau deploy/migrate và sau mỗi lần rotate secret.

Nếu **không chạy** command này, bạn phải tạo thủ công trong Django Admin:

- `Sites` → tạo/đúng domain (khớp domain chạy thực tế)
- `Social applications` → provider `google` → nhập `Client id` + `Secret` → gắn vào `Site`

Thiếu hoặc sai DB `SocialApp` thường gây các lỗi như: `SocialApp matching query does not exist`, `invalid_client`, hoặc không redirect đúng.

Project đã có command:

- `App_Account/management/commands/setup_google_socialapp.py`

### Cách 1: Dùng env đã set

```bash
python manage.py setup_google_socialapp
```

### Cách 2: Truyền trực tiếp qua tham số

```bash
python manage.py setup_google_socialapp \
  --client-id "YOUR_GOOGLE_CLIENT_ID" \
  --secret "YOUR_GOOGLE_CLIENT_SECRET" \
  --site-domain "127.0.0.1:8000" \
  --site-name "Local Dev"
```

Command sẽ:
- Tạo/cập nhật `Site` theo `SITE_ID`.
- Tạo/cập nhật `SocialApp` provider `google`.
- Gắn `SocialApp` vào `Site`.

## 6) Kiểm tra nhanh

Chạy các lệnh:

```bash
python manage.py check
python manage.py showmigrations sites account socialaccount
```

Truy cập URL:

- `http://127.0.0.1:8000/accounts/google/login/`

Hoặc vào trang login của hệ thống và bấm nút `Đăng nhập bằng Gmail`.

## 7) Lỗi thường gặp và cách xử lý

### Lỗi: `ModuleNotFoundError: No module named 'allauth'`

Nguyên nhân: virtualenv đang chạy chưa cài `django-allauth`.

Xử lý:

```bash
python -m pip install django-allauth==0.57.0
```

Nếu có nhiều virtualenv, dùng đúng Python binary của env đang chạy project.

### Vào `/accounts/google/login/` nhưng ra trang "Sign In Via Google" có nút `Continue` (không nhảy thẳng sang Google)

Hiện tượng: khi truy cập URL dạng:

- `/accounts/google/login/?process=login`

Bạn thấy trang xác nhận của `django-allauth` (ví dụ tiêu đề **"Sign In Via Google"**) và phải bấm `Continue` mới redirect sang Google.

Nguyên nhân: `django-allauth` mặc định **không tự động redirect OAuth trên GET** để giảm rủi ro CSRF / open-redirect.

Cách xử lý (nếu bạn muốn nhảy thẳng sang Google ngay):

- Thêm vào `Project/settings.py`:

```py
SOCIALACCOUNT_LOGIN_ON_GET = True
```

- Restart server (`runserver`, gunicorn, daphne...) để settings được load lại.

### Lỗi: `redirect_uri_mismatch`

Nguyên nhân: redirect URI trên Google Console không giống 100% URL callback thực tế.

Xử lý:
- Kiểm tra đúng protocol (`http`/`https`), domain (`www`), port, và dấu `/` cuối.
- Thêm đầy đủ callback cho local và production.

### Lỗi: `SocialApp matching query does not exist`

Nguyên nhân: chưa tạo `SocialApp` hoặc chưa gắn vào `Site`.

Xử lý:
- Chạy lại `python manage.py setup_google_socialapp`.
- Kiểm tra `SITE_ID` trong `settings.py`.

### Lỗi: `MultipleObjectsReturned` tại `/accounts/google/login/`

Nguyên nhân:
- Cấu hình bị trùng nguồn credentials (vừa có `SocialApp` trong DB, vừa có `SOCIALACCOUNT_PROVIDERS['google']['APP']` trong `settings.py`),
- Hoặc có nhiều bản ghi `SocialApp` cùng provider `google`.

Xử lý:
- Chỉ giữ 1 nguồn cấu hình (khuyến nghị: DB `SocialApp`).
- Kiểm tra/loại bỏ bản ghi `SocialApp` trùng lặp provider `google`.
- Restart `runserver` sau khi sửa.

### Đăng nhập local được, production lỗi

Nguyên nhân thường gặp:
- Chưa thêm callback production trên Google Console.
- Domain trong `Site` hoặc env không đúng.

## 8) Bảo mật

- Không commit `GOOGLE_CLIENT_SECRET` lên git.
- Không dùng `service_account` cho login người dùng web.
- File service account có `private_key` là dữ liệu rất nhạy cảm; nếu lộ, cần rotate/revoke key ngay.

## 9) Ghi chú cho project này

- Nút Google (UI mới) đã được thêm trong:
  - `templates/accounts/login.html`
  - `templates/accounts/register.html`
- CSS cho nút Google + divider "hoặc":
  - `static/ui/css/main.css` với các class: `.auth-divider`, `.btn-google`
- URL login Google allauth:
  - `/accounts/google/login/?process=login`
- Trong `Project/settings.py`, `SOCIALACCOUNT_PROVIDERS['google']['AUTH_PARAMS']` đã có `prompt: select_account` để Google **luôn hiển thị bước chọn tài khoản** (hữu ích khi trình duyệt đăng nhập nhiều Gmail). Nếu muốn tắt hành vi này, xóa hoặc đổi giá trị `prompt`.

### UI nút Google (tham khảo thiết kế)

Gợi ý triển khai giao diện nút Google giống thiết kế hiện đại:

- Dùng divider dạng 2 đường kẻ + chữ `hoặc` ở giữa.
- Nút Google nền trắng, border nhẹ, shadow mềm, hover rõ ràng.
- Icon Google nên dùng **SVG nhiều màu** (đúng logo) thay vì chỉ chữ `G` đơn sắc.

Lưu ý cache:

- Nếu vừa chỉnh CSS mà chưa thấy thay đổi, hãy hard refresh (macOS Chrome): `Cmd + Shift + R`.
