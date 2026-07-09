# App Refactor Runbook

Phiên bản: 2026-07-09

Tài liệu này ghi lại trạng thái codebase sau khi tách app ecommerce cũ thành các app theo domain. Project đã chọn hướng **reset DB dev/local**, nên migration hiện tại là bộ `0001_initial.py` sạch cho từng app domain.

## Trạng Thái Hiện Tại

Runtime không còn phụ thuộc legacy app `App_ecom`.

Các app đang active trong `Project/settings.py`:

```python
INSTALLED_APPS = [
    ...
    'App_Core',
    'App_Account',
    'App_Product',
    'App_Post',
    'App_Quanly',
    ...
]
```

`Project/urls.py` include trực tiếp từng app với namespace riêng:

```python
path('', include('App_Core.urls', namespace='core'))
path('', include('App_Account.urls', namespace='account'))
path('', include('App_Product.urls', namespace='product'))
path('', include('App_Post.urls', namespace='post'))
path('', include('App_Quanly.urls', namespace='quanly'))
```

Không còn module URL trung gian giữ namespace legacy.

## Phân Rã Domain

| App | Trách nhiệm chính |
| --- | --- |
| `App_Core` | Trang home/static, contact, upload CKEditor, middleware, sitemap, constants, helper storage/model utils, `PageView` |
| `App_Account` | Đăng ký/đăng nhập/đăng xuất, profile, checkout info, password reset, password validation, Google SocialApp setup |
| `App_Product` | Product/category/subcategory, variant/attribute, specs/photos, cart, checkout, order, payment method, wishlist, compare, review |
| `App_Post` | Subject/subsubject, post, post photo/content, comment, reply |
| `App_Quanly` | Dashboard/quản trị nghiệp vụ, menu config, import sản phẩm, seed dữ liệu quản lý |

## Model Ownership

`App_Core.models`:

- `Contact`
- `PageView`

`App_Account.models`:

- `Profile`
- `Checkout_info`

`App_Product.models`:

- `PaymentMethod`
- `Category`
- `SubCategory`
- `Product`
- `ProductPhoto`
- `Attribute`
- `ProductVariant`
- `VariantAttribute`
- `BaseProductSpecification`
- `Cart`
- `CartItem`
- `Order`
- `OrderItem`
- `Wishlist`
- `Compare`
- `Review`

`App_Post.models`:

- `Subject`
- `SubSubject`
- `Post`
- `PostPhoto`
- `PostContent`
- `Comment`
- `Reply`

`App_Quanly.models`:

- `QuanlyMenuConfig`

## URL Namespace Chuẩn

Template và code mới phải dùng namespace domain mới:

| Domain | Namespace | Ví dụ |
| --- | --- | --- |
| Core | `core` | `{% url 'core:home' %}` |
| Account | `account` | `{% url 'account:login' %}` |
| Product/cart/order | `product` | `{% url 'product:product_all' %}` |
| Post/blog | `post` | `{% url 'post:post_all' %}` |
| Quản lý | `quanly` | `{% url 'quanly:dashboard' %}` |

Không thêm lại URL theo namespace legacy. Nếu gặp template cũ, đổi sang namespace ở bảng trên.

URL quản lý canonical là `/quan-ly/`. Đường `/quanly/` được giữ làm redirect tương thích về `/quan-ly/`.

## Forms, Filters, Admin, Helper

Code phụ trợ đã nằm cùng app domain:

- `App_Core/forms.py`: `ContactForm`
- `App_Account/forms.py`: account/profile/password forms
- `App_Product/forms.py`: product/cart/order/payment/review forms
- `App_Product/filters.py`: product/order filters
- `App_Post/forms.py`: post/comment/reply forms
- `App_Post/filters.py`: post filters
- `App_Core/middleware.py`: security/upload/pageview middleware
- `App_Core/storage.py`: storage/upload path helpers
- `App_Core/sitemap.py`: sitemap classes
- `App_Account/password_validation.py`: password strength helpers

Khi thêm form/filter/admin mới, đặt trong app sở hữu model đó.

## Static Assets

Source static dùng chung nằm dưới root `static/`. Asset riêng cho giao diện quản lý đang nằm tại:

- `static/quanly/css/quanly.css`
- `static/quanly/js/quanly.js`
- `static/quanly/products.zip`

Template vẫn reference bằng `{% static 'quanly/...' %}`. Không sửa trực tiếp file trong `staticfiles/`; thư mục đó chỉ là output của `collectstatic`.

## Management Commands

Các command hiện tại:

```bash
python manage.py setup_google_socialapp
python manage.py seed_paymentmethods
python manage.py seed_products
python manage.py seed_posts
python manage.py seed_quanly
```

Vị trí command:

- `App_Account/management/commands/setup_google_socialapp.py`
- `App_Product/management/commands/seed_paymentmethods.py`
- `App_Product/management/commands/seed_products.py`
- `App_Post/management/commands/seed_posts.py`
- `App_Quanly/management/commands/seed_quanly.py`

`scripts/1_reset_fresh.py` sau khi reset DB và migrate sẽ hỏi xác nhận trước khi tạo/cập nhật account seed `superadmin` và `quanly`, rồi chạy seed theo thứ tự:

```bash
python manage.py seed_products
python manage.py seed_posts
python manage.py seed_quanly
python manage.py seed_paymentmethods
```

Tài khoản seed chỉ được tạo/cập nhật khi bạn xác nhận trong prompt:

```text
username: superadmin  password: 123456
username: quanly      password: 123456
```

Nếu chỉ muốn reset/migrate nhưng không seed dữ liệu:

```bash
python scripts/1_reset_fresh.py --skip-seed
```

## Migration Và Database

Refactor này đã chọn hướng reset DB, không giữ migration lịch sử hoặc table legacy.

Trạng thái migration:

- `App_Core/migrations/0001_initial.py`
- `App_Account/migrations/0001_initial.py`
- `App_Product/migrations/0001_initial.py`
- `App_Post/migrations/0001_initial.py`
- `App_Quanly/migrations/0001_initial.py`

DB SQLite cũ đã từng được backup trước khi reset, sau đó đã xoá theo quyết định dọn local:

```text
db.sqlite3.before_app_ecom_reset
```

Hiện không còn file backup DB local trong repo. Với production hoặc DB có dữ liệu thật, không dùng lại hướng reset DB này; cần migration chuyển state có kiểm soát và backup riêng trước khi thao tác.

## Checklist Khi Sửa Code Sau Refactor

Sau mỗi thay đổi liên quan model/import/template URL, chạy:

```bash
python3 scripts/3_security_tools.py refactor-audit
python3 manage.py check
python3 manage.py makemigrations --check --dry-run
python3 manage.py test App_Product App_Account App_Core App_Post App_Quanly
```

Rà import/namespace legacy:

```bash
rg -n "App_ecom|App_ecom:" . --glob '!*.pyc'
```

Nếu chỉ muốn kiểm tra runtime và bỏ qua tài liệu lịch sử:

```bash
rg -n "App_ecom|App_ecom:" App_Account App_Core App_Product App_Post App_Quanly Project templates scripts --glob '!*.pyc'
```

Rà URL namespace cũ trong template:

```bash
rg -n "url 'App_ecom:|url \"App_ecom:" templates App_* Project --glob '!*.pyc'
```

## Quy Ước Không Regress

- Không import model/form/filter từ app legacy.
- Không thêm lại app legacy vào `INSTALLED_APPS`.
- Không tạo namespace legacy để che lỗi template.
- Không đặt model ở app không sở hữu domain.
- Không tạo migration phụ thuộc app legacy.
- Nếu cần khôi phục dữ liệu từ backup DB, làm thành task riêng và viết migration/import script rõ ràng.
