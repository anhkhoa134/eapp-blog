---
name: django-ui-replacement
description: Use this skill when replacing an existing Django site's UI with a new static or template-based interface, while preserving Django template hooks, backing up old templates/database, moving assets into static/media, wiring navbar/content to real database categories and records, creating seed data, and validating the result across desktop/mobile pages.
---

# Django UI Replacement

## Khi dùng

Dùng skill này khi cần thay giao diện một project Django bằng bộ UI mới, ví dụ HTML/CSS/JS tĩnh nằm trong `backup/<ui-name>/`, nhưng vẫn phải giữ logic Django hiện có:

- `{% static %}`, `{% url %}`, `{% csrf_token %}`, `{% block %}`
- `messages`, modal, HTMX, form POST, auth/user context
- dữ liệu thật từ database thay vì hard-code HTML
- category/navbar lấy từ database
- backup template và database trước khi thay đổi
- seed dữ liệu mới để UI chạy được ngay
- sau khi giao diện mới chạy ổn, cập nhật content, SEO/meta, sitemap, robots và thông tin thương hiệu trước khi bàn giao

Không dùng skill này cho task chỉ sửa màu, đổi copy nhỏ, hoặc chỉnh một component đơn lẻ — các task đó dùng [FRONTEND-SKILL.md](FRONTEND-SKILL.md). Quy ước backend (app ownership, URL namespace, HTMX trang quản lý) xem [BACKEND-SKILL.md](BACKEND-SKILL.md).

Nếu muốn dùng như Codex skill chuẩn cho nhiều repo, đặt nội dung file này vào:

```text
$CODEX_HOME/skills/django-ui-replacement/SKILL.md
```

## Input cần xác định

Trước khi sửa file, tìm các thông tin sau trong repo:

```bash
rg --files | sort
rg --files docs | rg "customer|persona|brand|seo|content|profile"
rg -n "TEMPLATES|STATIC_URL|STATICFILES_DIRS|MEDIA_URL|MEDIA_ROOT|context_processors" . -g "*settings.py" -S
rg -n "class .*Category|class .*Product|class .*Post|def .*home|product_all|product_detail|get_absolute_url" . -S
```

Xác định:

- file thông tin khách hàng/brand brief: ưu tiên `docs/customer_info.md`, hoặc file tương đương do user cung cấp
- file customer persona: ưu tiên `docs/customer_persona.md`, hoặc file persona tương đương do user cung cấp
- thư mục UI mới: ví dụ `backup/<ui-name>/`
- template layout cũ: thường là `templates/base.html`
- template trang chủ cũ: thường là `templates/home.html`
- app Django chính: ví dụ `App_Product`
- model dữ liệu chính: thường là `Category`, `Product`, `Post`, `Subject`
- context processor đang dùng cho layout chung
- URL names hiện có cho home, danh mục, chi tiết, bài viết, liên hệ

Nếu thiếu file thông tin khách hàng hoặc customer persona, phải yêu cầu user cung cấp trước khi viết lại content, SEO/meta, sitemap hoặc robots. Có thể tiếp tục phần kỹ thuật giao diện nếu user đồng ý, nhưng không được tự bịa định vị thương hiệu, lợi ích, persona, địa chỉ, số điện thoại, email hoặc keyword chính.

Nếu project không dùng đúng các tên trên, đổi ví dụ trong skill theo tên thực tế của repo.

## Quy trình tổng quát

### 1. Đọc UI mới và template cũ

Luôn đọc cả giao diện mới và template cũ trước khi sửa:

```bash
rg --files backup/<ui-name> templates static | sort
sed -n '1,260p' templates/base.html
sed -n '1,280p' templates/home.html
sed -n '1,360p' backup/<ui-name>/index.html
```

Phân tách rõ:

- phần layout dùng chung: `<head>`, navbar, footer, modal, script vendor
- phần trang chủ: hero, section nội dung, list item/card
- phần asset: ảnh, CSS, JS, font
- phần dữ liệu động cần lấy từ DB

### 2. Backup giao diện cũ

Tạo backup có timestamp trước mọi thay đổi lớn:

```bash
mkdir -p backup/old_templates_YYYYMMDD_HHMMSS
cp templates/base.html templates/home.html backup/old_templates_YYYYMMDD_HHMMSS/
```

Nếu sẽ thay nhiều template khác, backup cả nhóm file liên quan:

```bash
cp templates/product_all.html templates/product_detail.html templates/post_all.html templates/post_detail.html templates/contact.html templates/about.html backup/old_templates_YYYYMMDD_HHMMSS/
```

Không ghi đè backup cũ.

### 3. Copy asset UI mới vào static

Không dùng trực tiếp đường dẫn tương đối như `images/...` trong Django template. Copy asset vào `static`:

```bash
mkdir -p static/website/img/<brand_slug>
cp backup/<ui-name>/images/* static/website/img/<brand_slug>/
```

Tách CSS/JS inline từ HTML mới thành file riêng:

```text
static/website/css/<brand_slug>.css
static/website/js/<brand_slug>.js
```

Đổi URL asset trong CSS:

```css
/* trước */
url('images/hero.jpg')

/* sau */
url('../img/<brand_slug>/hero.jpg')
```

#### Font chữ và tiếng Việt

Khi chọn hoặc migrate font cho UI tiếng Việt, phải kiểm tra font có subset/ký tự tiếng Việt đầy đủ cho các weight thực tế đang dùng, nhất là heading đậm `600`/`700`. Không dùng một font chỉ có subset latin/latin-ext nếu nội dung có dấu tiếng Việt vì các ký tự như `ư`, `ơ`, `ă`, `đ`, dấu nặng/hỏi/ngã có thể bị render lệch hoặc rơi về fallback từng ký tự.

Ưu tiên self-host font trong `static/vendor/gfonts/` hoặc `static/website/fonts/`, dùng `font-display: swap`, và khai báo fallback rõ ràng:

```css
:root {
  --brand-font-sans: "Plus Jakarta Sans", "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, "Helvetica Neue", sans-serif;
}

body {
  font-family: var(--brand-font-sans);
}
```

Với Hadona, website public đang dùng `static/vendor/gfonts/hadona-fonts.css`, trỏ tới bộ local `Plus Jakarta Sans` có subset Vietnamese và fallback `Inter` rồi system fonts. Nếu đổi font sau này, phải test bằng câu tiếng Việt có đủ dấu, ví dụ: `Chiêm ngưỡng kỳ quan thiên nhiên từ một góc nhìn khác biệt`.

Không dùng `Georgia`, `Times New Roman` hoặc font serif hệ thống cho tiêu đề/card chứa dữ liệu tiếng Việt động nếu chưa test kỹ trên trình duyệt đích. Lỗi đã gặp ở Hadona: tiêu đề bài viết như `Set menu buổi tối sát biển` và `Check-in Jeep hồng & khung tím` bị vỡ dấu khi card dùng `Georgia`; các selector card title nên dùng `var(--hadona-font-sans)` hoặc font self-hosted có Vietnamese subset.

Trong template, gọi bằng `{% static %}`:

```django
<link rel="stylesheet" href="{% static 'website/css/<brand_slug>.css' %}">
<script src="{% static 'website/js/<brand_slug>.js' %}"></script>
<img src="{% static 'website/img/<brand_slug>/logo.png' %}" alt="{{ site_name }}">
```

### 4. Thay `base.html` có kiểm soát

`base.html` mới phải giữ các hook Django bắt buộc:

```django
{% load static %}
{% block meta %}{% endblock meta %}
{% block css %}{% endblock css %}
{% block content %}{% endblock content %}
{% block js %}{% endblock js %}
{% csrf_token %}
```

Giữ hoặc chuyển tương đương các thành phần hệ thống:

- CSS/JS vendor đang self-host trong repo
- Django `messages`
- spinner/loading nếu project đang dùng
- HTMX modal/toast containers nếu project đang dùng HTMX
- form POST có `{% csrf_token %}`
- mobile nav/floating actions nếu UI mới cần

Tránh:

- copy nguyên link CDN nếu project đã có vendor self-hosted
- hard-code URL tuyệt đối của môi trường local
- xóa block mà template con đang dùng
- để `href="#"` cho hành động thật nếu đã có URL name phù hợp

### 5. Navbar phải lấy từ database và tự cập nhật

Navbar không nên hard-code URL chi tiết record như `product_detail` nếu menu đại diện cho danh mục. Dùng category từ DB và link về trang danh mục.

Context processor nên cung cấp một danh sách category dành riêng cho navbar. Nếu UI cần giữ một thứ tự ưu tiên cho vài category chính, sắp các slug đó trước rồi append toàn bộ category còn lại để category mới tạo từ trang quản lý tự xuất hiện trên navbar:

```python
categories = Category.objects.prefetch_related('subcategories').order_by('id')
category_by_slug = {category.slug: category for category in categories}
priority_slugs = ('thiet-ke', 'sua-chua', 'thi-cong', 'vat-dung-noi-that')
navbar_category_links = [
    category_by_slug[slug]
    for slug in priority_slugs
    if slug in category_by_slug
]
navbar_category_links.extend(
    category
    for category in categories
    if category.slug not in priority_slugs
)

# Optional: giữ mapping này nếu footer hoặc section riêng cần link nhanh theo slug.
navbar_categories = {
    'design': category_by_slug.get('thiet-ke'),
    'renovation': category_by_slug.get('sua-chua'),
    'construction': category_by_slug.get('thi-cong'),
    'interior': category_by_slug.get('vat-dung-noi-that'),
}
```

Template top navbar phải loop qua `navbar_category_links` và dùng `get_absolute_url` của category:

```django
{% for category in navbar_category_links %}
    <li class="nav-item">
        <a class="nav-link {% if request.resolver_match.kwargs.slug_category == category.slug %}active{% endif %}" href="{{ category.get_absolute_url }}">
            <span class="offcanvas-nav-icon">
                {% if category.slug == 'thiet-ke' %}
                    <i class="bi bi-rulers"></i>
                {% elif category.slug == 'sua-chua' %}
                    <i class="bi bi-tools"></i>
                {% elif category.slug == 'thi-cong' %}
                    <i class="bi bi-bricks"></i>
                {% elif category.slug == 'vat-dung-noi-that' %}
                    <i class="bi bi-lamp"></i>
                {% else %}
                    <i class="bi bi-grid"></i>
                {% endif %}
            </span>{{ category.name }}
        </a>
    </li>
{% endfor %}
```

Nguyên tắc:

- menu danh mục -> `Category.get_absolute_url` hoặc URL list/category
- top navbar category -> loop từ DB, không hard-code từng category trong template
- category mới tạo trong trang quản lý phải tự xuất hiện ở navbar, tối đa chỉ cần icon mặc định
- menu bài viết -> subject/category bài viết nếu có, không trỏ vào một bài cụ thể
- menu CTA như Báo giá -> modal hoặc trang contact/quote
- không dùng `product_detail` cho navbar chính, trừ khi menu thật sự là một landing page dạng sản phẩm/dịch vụ đơn

Kiểm tra nhanh:

```bash
rg -n "product_detail.*thiet-ke|product_detail.*thi-cong|product_detail.*sua-chua|product_detail" templates/base.html
```

Nếu lệnh này trả ra link menu chính, xem lại.

### 5.1. Quy chuẩn responsive/mobile

Giao diện mobile phải ưu tiên mật độ thông tin và thao tác nhanh. Khi chuyển UI desktop sang mobile:

- giảm padding/margin/gap của section, card, toolbar, form và footer so với desktop
- giảm size heading, button, icon, thumbnail và chiều cao card để hiển thị được nhiều nội dung hơn trong một viewport
- tránh hero quá cao, khoảng trắng lớn, card quá rộng hoặc font display trên mobile
- dùng grid 2 cột cho card nhỏ nếu nội dung đủ ngắn; dùng 1 cột cho form, bài viết dài hoặc card cần đọc nhiều text
- giới hạn mô tả bằng line clamp khi danh sách có nhiều item; detail page mới hiển thị đầy đủ
- giữ các nút hành động chính trong vùng dễ chạm, nhưng không tăng padding đến mức chiếm quá nhiều màn hình
- kiểm tra text dài, tên sản phẩm/danh mục, giá, trạng thái đơn hàng không làm vỡ layout

Navbar mobile nên dùng offcanvas mở từ trái sang phải:

- nút menu đặt rõ trong header mobile
- offcanvas có backdrop phía sau
- click bên ngoài offcanvas hoặc bấm nút đóng phải đóng được menu
- ESC đóng được nếu framework hỗ trợ sẵn
- menu trong offcanvas vẫn lấy category từ database như desktop navbar
- dropdown/submenu trong offcanvas phải mở được bằng tap, không phụ thuộc hover
- khi click một link thật, menu nên tự đóng hoặc chuyển trang bình thường
- không dùng overlay tự viết nếu Bootstrap/offcanvas hoặc thư viện hiện có đã đáp ứng được backdrop và outside-click

Với section có nhiều card, không dàn quá dài trên mobile:

- nếu card đơn giản và cần scan nhanh, dùng CSS grid responsive, ví dụ `grid-template-columns: repeat(2, minmax(0, 1fr))` ở mobile rộng
- nếu card lớn, có ảnh nổi bật, hoặc số lượng nhiều, dùng slider/swiper thay vì render một cột dài
- slider/swiper phải có nút previous/next nổi trên nội dung, nền mờ/translucent, đủ tương phản và không che text chính
- nút previous/next chỉ nên chiếm diện tích nhỏ; đặt giữa cạnh trái/phải hoặc vị trí ổn định theo thiết kế
- với card nằm trong scroll/slider, kiểm tra `box-shadow` kỹ: shadow đổ xuống dưới có thể cộng với thanh scroll hoặc block kế bên tạo thành một vệt tối ngang dưới hàng card; ưu tiên shadow đều quanh viền, ẩn scrollbar đúng cách, hoặc chừa padding đáy đủ sạch
- vẫn hỗ trợ touch swipe trên mobile nếu dùng slider
- desktop có thể dùng grid nhiều cột; mobile có thể chuyển sang slider nếu grid làm trang quá dài

### 6. Chuyển homepage sang dữ liệu thật

Trong `home` view, tạo queryset theo các section của UI mới:

```python
service_products = Product.objects.filter(
    name__in=[
        'Thiết kế kiến trúc',
        'Thiết kế nội thất',
        'Xây nhà thô',
        'Xây nhà trọn gói',
        'Sửa chữa cải tạo',
    ]
).order_by('id')
design_projects = Product.objects.filter(category__name='Thiết kế').order_by('id')
construction_projects = Product.objects.filter(category__name='Thi công').order_by('id')
renovation_projects = Product.objects.filter(category__name='Sửa chữa').order_by('id')
interior_items = Product.objects.filter(category__name='Vật dụng nội thất').order_by('id')
team_posts = Post.objects.filter(subject__slug='doi-ngu').order_by('id')[:3]
```

Truyền vào context:

```python
return render(request, 'home.html', {
    'service_products': service_products,
    'design_projects': design_projects,
    'construction_projects': construction_projects,
    'renovation_projects': renovation_projects,
    'interior_items': interior_items,
    'team_posts': team_posts,
})
```

Trong template, render card bằng object thật:

```django
{% for item in service_products %}
    <a href="{{ item.get_absolute_url }}" class="service-card">
        <img src="{{ item.get_image }}" alt="{{ item.name }}" loading="lazy">
        <span>{{ item.name }}</span>
    </a>
{% empty %}
    <p>Chưa có dữ liệu.</p>
{% endfor %}
```

Ưu tiên method sẵn có của model như `get_absolute_url`, `get_image`, `get_thumbnail`. Không tự ghép URL media bằng chuỗi nếu model đã có helper.

### 7. Backup và seed database

Trước khi xóa hoặc thay dữ liệu lớn, backup database:

```bash
mkdir -p backup/database
cp db.sqlite3 backup/database/db.sqlite3.before_ui_seed_YYYYMMDD_HHMM
```

Chỉ flush khi user đã yêu cầu xóa dữ liệu cũ:

```bash
python3 manage.py flush --noinput
```

Tạo management command seed trong app phù hợp:

```text
<app_name>/management/commands/seed_<brand_slug>.py
```

Seed command nên:

- tạo/cập nhật admin user nếu được yêu cầu
- tạo category/subject trước
- với KIẾN AN CONS, category chính hiện là `Thiết kế`, `Sửa chữa`, `Thi công`, `Vật dụng nội thất`
- nếu đổi taxonomy, cập nhật seed, homepage query và `priority_slugs` trong context processor cùng lúc
- tạo product/post theo category/subject
- attach ảnh từ `static/website/img/<brand_slug>` vào ImageField để UI dùng media thật
- dùng `update_or_create` để chạy lại không nhân đôi dữ liệu
- có option `--clear` để xóa dữ liệu do seed tạo rồi seed lại
- có thể xóa legacy category do seed cũ tạo, ví dụ `Dịch vụ`, `Dự án thiết kế`, `Dự án thi công`, `Dự án sửa chữa`

Nếu project có biến thể sản phẩm (`ProductVariant`, `Attribute`, `VariantAttribute`), seed phải giữ đúng contract hiện có:

- Khi tạo `Product`, signal có thể tự tạo một `ProductVariant` mặc định. Dùng lại variant mặc định này làm biến thể đầu tiên nếu cần seed nhiều biến thể, rồi mới tạo thêm các `ProductVariant` khác.
- Mỗi biến thể phải có `VariantAttribute` rõ ràng, ví dụ `Màu sắc: Titan Xanh`, `Dung lượng: 256GB`; không nhét thuộc tính biến thể vào tên product hoặc description.
- Giá hiển thị/listing thường lấy từ product nhưng product price có thể được cập nhật từ variant rẻ nhất qua signal. Sau khi seed variant, kiểm tra lại `Product.price`, `Product.price_sale`.
- `Product.stock` và `Product.is_stock` phải phản ánh tổng/khả dụng của biến thể nếu UI dùng trạng thái cấp product.
- Không để product có variant còn hàng nhưng `product.is_stock=False` do random seed, vì UI sẽ hiển thị sai trạng thái.
- Nếu seed nhiều biến thể cố định cho một product, cấu hình bằng dữ liệu có cấu trúc theo product name/slug thay vì logic random khó debug.

Mẫu khung command:

```python
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

class Command(BaseCommand):
    help = "Seed dữ liệu cho giao diện mới."

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true")

    def handle(self, *args, **options):
        asset_dir = Path(settings.BASE_DIR) / "static" / "website" / "img" / "<brand_slug>"
        if not asset_dir.exists():
            raise CommandError(f"Không tìm thấy asset: {asset_dir}")

        with transaction.atomic():
            if options["clear"]:
                self.clear_seeded_content()
            self.seed_categories()
            self.seed_content()

        self.stdout.write(self.style.SUCCESS("Đã seed dữ liệu giao diện mới."))
```

Sau khi seed:

```bash
python3 manage.py seed_<brand_slug>
python3 manage.py shell -c "from <app_name>.models import Category, Product; print(Category.objects.count(), Product.objects.count())"
```

### 8. Chia nhóm URL/template cần thay giao diện

Sau khi `base.html` và `home.html` ổn, chia các URL còn lại thành nhóm nhỏ. Làm xong nhóm nào thì dừng, chạy validation cho nhóm đó, rồi liệt kê nhóm/trang còn lại.

#### Nhóm A: Public core

Các trang khách truy cập thấy đầu tiên:

- `/` -> `templates/home.html`
- `/san-pham/` -> `templates/product_all.html`
- `/danh-muc/<slug:slug_category>/` -> `templates/product_all.html`
- `/danh-muc/<slug:slug_category>/<slug:slug_subcategory>/` -> `templates/product_all.html`
- `/san-pham/<slug:slug_category>/<slug:slug_product>/` -> `templates/product_detail.html`
- `/bai-viet/` -> `templates/post_all.html`
- `/chu-de/<slug:slug_subject>/` -> `templates/post_all.html`
- `/chu-de/<slug:slug_subject>/<slug:slug_subsubject>/` -> `templates/post_all.html`
- `/bai-viet/<slug:slug_subject>/<slug:slug_post>/` -> `templates/post_detail.html`
- `/lien-he/` -> `templates/contact.html`
- `/gioi-thieu/` -> `templates/about.html`

URL cũ dạng không dấu gạch (`/sanpham/`, `/lienhe/`, `/dangnhap/`, `/cart_view/`, `/wishlist/`…) vẫn được hỗ trợ bằng **redirect 301** về URL canonical mới — khai báo trong phần `# Legacy redirect` cuối `urls.py` của từng app (`App_Core`, `App_Account`, `App_Product`, `App_Post`; riêng `/quanly/` nằm ở `App_Quanly`). Không xóa các redirect này khi sửa route; route mới không dùng lại dạng không dấu gạch.

Partial đi kèm:

- `templates/partials/products.html`
- `templates/partials/products_pagination.html`
- `templates/partials/posts.html`
- `templates/partials/posts_pagination.html`
- `templates/partials/subcategory_checkboxes.html`

Lưu ý nghiệp vụ:

- `product_detail.html` phải giữ form đánh giá sản phẩm nếu project có `Review`/`add_review`.
- `post_detail.html` phải giữ form bình luận bài viết nếu project có `Comment`/`add_comment`.
- Nếu dùng HTMX cho comment/reply, cập nhật cả `partials/comment.html` và `partials/reply_form.html`.

Lưu ý riêng cho danh sách và chi tiết sản phẩm:

- Trang list/search/category sản phẩm không được lọc cứng `is_stock=True`. Sản phẩm hết hàng vẫn phải hiển thị để người dùng thấy kết quả tìm kiếm/danh mục, nhưng card phải ghi rõ `Hết hàng`.
- Card sản phẩm hết hàng phải tắt hoặc vô hiệu hóa hành động `Thêm vào giỏ hàng`, không chỉ đổi màu chữ.
- Nếu vẫn có filter tồn kho trong sidebar, đó phải là lựa chọn của người dùng (`Còn hàng`/`Hết hàng`), không phải điều kiện mặc định ẩn sản phẩm.
- Search theo tên, ví dụ `?product_name=Pro+Max`, phải tìm được cả product hết hàng nếu tên match.
- Giá trên card nên dùng `product.price_sale`/`product.price` đã được đồng bộ từ biến thể rẻ nhất; đừng tự query variant trong template nếu view/model đã chuẩn hóa giá.
- Nếu product có category nullable, link card phải fallback an toàn về list page hoặc xử lý giống partial hiện có, tránh template lỗi khi category trống.

Lưu ý riêng cho biến thể sản phẩm:

- `product_detail.html` phải giữ danh sách `variants`, `active_variant` và URL có `variant_slug` nếu view đang hỗ trợ `/san-pham/<category>/<product>//<variant_slug>`.
- Khi không có `variant_slug`, detail page hiện chọn biến thể có effective price thấp nhất; không thay bằng variant đầu tiên tùy ý nếu không sửa view/test tương ứng.
- Variant selector phải hiển thị các thuộc tính qua `variant.attributes -> VariantAttribute -> Attribute`, ví dụ `Màu: Nâu`, `Kiểu: Khóa kéo`, hoặc summary tương đương.
- Form thêm giỏ ở detail phải gửi đúng `variant_id`; không gửi mỗi `product_id` cho trang có nhiều biến thể.
- Nút thêm giỏ ở list dùng variant rẻ nhất qua `_product_variants(product).first()`; nếu đổi logic UI phải giữ behavior chọn variant mặc định rõ ràng.
- Filter thuộc tính ở list đang dựa vào `variants__attributes__attribute__key/value`; khi thay UI filter, giữ name/value của checkbox hoặc cập nhật view đồng bộ.
- Cart/order/email/invoice nên hiển thị tên hoặc thuộc tính biến thể đã chọn, không chỉ tên product gốc.
- Test tối thiểu: detail hiện đủ biến thể, chọn biến thể thêm vào giỏ hàng đúng variant, list search vẫn thấy product hết hàng và ghi `Hết hàng`.

#### Nhóm B: Branding, meta, partial hệ thống

Các phần này không phải page chính nhưng ảnh hưởng toàn site:

- `templates/partials/meta.html`
- `templates/partials/meta_product.html`
- `templates/partials/meta_post.html`
- `templates/partials/contact_modal.html`
- `templates/partials/error_404_500.html`
- `templates/partials/navbar.html` nếu còn được template cũ include
- `templates/robots.txt`
- favicon/logo trong `base.html`
- email templates trong `templates/registration/*.email` và email HTML tương ứng

Lưu ý:

- Xóa branding cũ như domain demo, logo cũ, email/số điện thoại cũ.
- Với email, ưu tiên logo JPG/PNG có URL tuyệt đối thay vì WebP.
- Email quản lý nhận thông báo/form liên hệ hiện dùng `kienanbuild@gmail.com`. Khi seed hoặc sửa user `quanly`, phải giữ email quản lý này để các form tư vấn/nhận tin gửi đúng nơi.
- Tài khoản SMTP gửi email vẫn lấy từ `.env` (`EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`). Không hard-code credential SMTP, không tự đổi tài khoản gửi sang email quản lý nếu user không yêu cầu.
- Cập nhật `site_name`, subject mặc định và nội dung email trong view/task gửi email; `from_email` nên dùng cấu hình từ settings hoặc `.env` nếu project đã thiết kế như vậy.

#### Nhóm C: Auth/account

Các trang tài khoản nên dùng chung layout form/panel:

- `/dang-nhap/` -> `templates/login.html`
- `/dang-ky/` -> `templates/register.html`
- `/doi-mat-khau/` -> `templates/registration/change_password.html`
- `/dat-lai-mat-khau/yeu-cau/` -> `templates/registration/reset_form.html`
- `/dat-lai-mat-khau/da-gui/` -> `templates/registration/reset_done.html`
- `/dat-lai-mat-khau/<uidb64>/<token>/xac-nhan/` -> `templates/registration/reset_confirm.html`
- `/dat-lai-mat-khau/hoan-tat/` -> `templates/registration/reset_complete.html`
- `/thong-tin-tai-khoan/` -> `templates/edit_profile.html`
- `/dia-chi-giao-hang/` -> `templates/edit_info.html`
- `/don-hang-da-mua/` -> `templates/order_cus.html`
- account sidebar -> `templates/partials/account_sidebar.html`

Lưu ý:

- Giữ field name mà view đang đọc, ví dụ `fullname`, `phone`, `address`, `email`, `birthday`, `gender`, `old_password`, `password1`, `password2`.
- Giữ HTMX validation target nếu đang dùng, ví dụ `check_username_*`, `check_password*`.
- Với các ô nhập mật khẩu ở auth/account (`login`, `register`, `change_password`, `reset_confirm`), giữ nút icon eye để người dùng có thể hiện/ẩn mật khẩu đang nhập. Pattern hiện tại dùng wrapper `.password-field`, button `.password-toggle`, icon Bootstrap Icons `bi-eye`/`bi-eye-slash`, CSS trong `static/website/css/main.css` và JS toggle trong `static/canhan/js/style.js`.
- Không dùng thông báo `password2` kiểu "Mật khẩu phù hợp" vì dễ hiểu nhầm là mật khẩu đủ mạnh. Helper `check_password2` chỉ nên báo trạng thái xác nhận mật khẩu: trùng khớp, không trùng, hoặc cần nhập mật khẩu mới trước; độ mạnh mật khẩu thuộc `check_password1`.
- Test cả trạng thái chưa đăng nhập và đã đăng nhập.

#### Nhóm D: Cart/order/checkout

Nhóm này thường còn UI thương mại điện tử cũ, nhưng vẫn cần giữ đúng flow nghiệp vụ:

- `/gio-hang/` -> `templates/cart/cart_view.html`
- HTMX cart partials -> `templates/cart/cart_items.html`, `templates/cart/cart_menu.html`, `templates/cart/cart_update.html`
- `/thanh-toan/` -> `templates/cart/checkout.html`
- `/don-hang/thanh-cong/<int:order_id>/` -> `templates/cart/order_success.html`
- `/don-hang/<int:order_id>/` -> `templates/cart/order_detail.html`
- invoice nếu có -> `templates/invoice.html`

Lưu ý:

- Giữ URL/action HTMX cho add/remove/update/decrease/increase cart.
- Giữ form checkout field names mà view đang đọc.
- Trang giỏ hàng và thông tin giao hàng/checkout nên gộp trong cùng một màn hình nếu UX hiện tại đang dùng flow một trang; không tạo lại trang checkout riêng chỉ để nhập giao hàng/thanh toán.
- Test với cart rỗng, cart có item, checkout khi chưa đủ thông tin và order detail.

#### HTMX action feedback cho cart/wishlist

Khi cập nhật UI sản phẩm, không biến các action nhỏ thành full-page redirect nếu flow cũ hoặc UX hiện tại đang dùng HTMX:

- Nút "Thêm vào giỏ hàng" trên product card phải dùng HTMX POST, swap lại `#cart-menu`/cart partial và giữ toast qua `HX-Trigger`.
- Nút "Thêm vào yêu thích" trên product card phải dùng HTMX POST, swap chính nút tim bằng partial thay vì redirect sang trang chi tiết hoặc trang wishlist.
- Response HTMX nên trả partial nhỏ đúng target, ví dụ `cart/cart_update.html` cho cart hoặc `partials/wishlist_button.html` cho wishlist.
- Request thường vẫn cần `href`/redirect fallback để link hoạt động khi không có JavaScript hoặc HTMX.
- Sau request thành công, giữ feedback ngoài toast: icon giỏ hàng đổi tạm sang dấu check, icon yêu thích đổi sang tim đầy và có effect pop/pulse nhẹ.
- Nếu thêm trạng thái active ban đầu, truyền danh sách product id đã yêu thích từ view, tránh query DB trong từng product card.
- Test bằng request HTMX để chắc response trả `200`, có `HX-Trigger`, và không có `Location` redirect header.

#### Nhóm E: Static utility/landing phụ

Các trang ít truy cập nhưng vẫn cần bỏ giao diện/branding cũ:

- `/thanh-cong/` -> `templates/success.html`
- `/ctv/` -> `templates/CTV.html`
- `templates/view_cart.html` nếu còn route hoặc include cũ
- `templates/partials/categories` nếu còn được dùng trên homepage/list page

#### Nhóm F: Admin/quanly

Không thay admin sang UI public mới trong quy trình này. Với `/quanly`, chỉ thay nhận diện thương hiệu để không lẫn brand cũ, còn layout quản trị, sidebar, bảng dữ liệu, HTMX modal, pagination và workflow quản lý phải giữ nguyên.

Các phần được phép thay:

- `templates/quanly/quanly.html`: title, meta description, favicon, logo header, footer copyright.
- `templates/quanly/marketing_email_form.html`: placeholder/default copy có brand cũ.
- email sender/context liên quan nếu admin gửi email marketing.
- mọi logo/favicon/domain cũ còn sót trong template admin.

Không thay trong nhóm này:

- không đổi dashboard layout
- không đổi sidebar/navigation structure
- không đổi table/list/form markup trừ khi chỉ sửa brand text/logo
- không đổi HTMX target `#dialog`, toast, pagination, modal form
- không đưa class/layout public như `kc-page`, `kc-auth-page`, `kc-list-card` vào admin

Lưu ý:

- Kiểm tra các URL `/quanly/...` vẫn render/redirect như trước sau khi thay logo/title.
- Quy ước HTMX của trang quản lý (partial `#<entity>-list-container` + `hx-swap="outerHTML"`, init JS qua `htmx.onLoad` thay vì `htmx:afterSwap`) xem mục 4 của [BACKEND-SKILL.md](BACKEND-SKILL.md); không phá các quy ước này khi đụng tới template quanly.
- Nếu sau này muốn redesign admin UI đầy đủ, tách thành task riêng vì blast radius lớn.

#### Nhóm G: Missing/legacy route audit

Sau khi cập nhật các nhóm trên, rà các view render template không tồn tại hoặc route legacy:

```bash
rg -n "return render\\(request, '[^']+'" <app_name>/views.py
rg --files templates | sort
```

Ví dụ cần xử lý nếu view còn render nhưng template không tồn tại:

- `/yeu-thich/` -> `wishlist.html`
- `/so-sanh/` -> `compare.html`

Với route không còn phù hợp domain mới, chọn một trong ba hướng:

- tạo template mới theo design system
- redirect về trang phù hợp
- gỡ route nếu chắc chắn không dùng

Giữ nguyên contract với view hiện tại:

- tên biến context
- form field names
- pagination object
- HTMX target/partial nếu đang dùng
- URL names trong `{% url %}`

Nếu partial cũ đang được HTMX gọi, cập nhật cả partial thay vì chỉ cập nhật page wrapper.

### 8.1. Audit hiện tại của repo này: các trang chưa cập nhật giao diện mới

Cập nhật ngày 2026-07-07. Quy ước trong danh sách này:

- "Chưa cập nhật" nghĩa là template vẫn dùng layout Bootstrap/card/table/form cũ, class legacy, copy demo, hoặc branding cũ thay vì đồng bộ với giao diện public mới đang nằm ở `base.html`, `home.html`, `static/website/css/main.css`.
- `base.html` và `home.html` đã có nền giao diện mới cho PTcom, nhưng `base.html` vẫn còn favicon/footer/script eApp nên vẫn cần vòng rà branding.
- Không tính các template `quanly/*` là trang public cần redesign; nhóm admin chỉ cần thay logo/title/favicon/footer/copy brand cũ nếu còn.

#### Public core chưa cập nhật/hoàn thiện

- `/san-pham/`, `/danh-muc/<slug:slug_category>/`, `/danh-muc/<slug:slug_category>/<slug:slug_subcategory>/` -> `templates/product_all.html`
  - Đã có một số class mới như `filter-card`, nhưng layout vẫn là filter/sidebar Bootstrap cũ; cần đồng bộ list page, empty state, mobile filter và pagination.
- `/san-pham/<slug:slug_category>/<slug:slug_product>/` -> `templates/product_detail.html`
  - Vẫn dùng `fluid-container mx-4`, inline CSS, carousel/table/form Bootstrap cũ; cần cập nhật gallery, variant selector, review form và related products theo design system.
- `/bai-viet/`, `/chu-de/<slug:slug_subject>/`, `/chu-de/<slug:slug_subject>/<slug:slug_subsubject>/` -> `templates/post_all.html`
  - Vẫn dùng filter/sidebar Bootstrap cũ và `filter-container bg-light`; cần đồng bộ với list page mới.
- `/bai-viet/<slug:slug_subject>/<slug:slug_post>/` -> `templates/post_detail.html`
  - Vẫn dùng blog layout cũ, sidebar inline/sticky và related posts cũ; cần cập nhật article layout, comment/reply nếu có.
- `/lien-he/` -> `templates/contact.html`
  - Nội dung đã theo PTcom nhưng layout form/map/info vẫn cũ; cần đồng bộ visual, spacing, mobile và CTA.
- `/gioi-thieu/` -> `templates/about.html`
  - Nội dung đã theo PTcom nhưng còn layout cũ, inline padding, card Bootstrap và section cũ; cần làm lại theo design system.

Partial public đi kèm cần cập nhật cùng nhóm trên:

- `templates/partials/products.html`
- `templates/partials/products_pagination.html`
- `templates/partials/posts.html`
- `templates/partials/posts_pagination.html`
- `templates/partials/subcategory_checkboxes.html`
- `templates/partials/comment.html`
- `templates/partials/reply_form.html`
- `templates/partials/menu_top_post.html`
- `templates/partials/menu_bottom_post.html`
- `templates/partials/categories`

#### Auth/account chưa cập nhật

- `/dang-nhap/` -> `templates/login.html`
- `/dang-ky/` -> `templates/register.html`
- `/doi-mat-khau/` -> `templates/registration/change_password.html`
- `/dat-lai-mat-khau/yeu-cau/` -> `templates/registration/reset_form.html`
- `/dat-lai-mat-khau/da-gui/` -> `templates/registration/reset_done.html`
- `/dat-lai-mat-khau/<uidb64>/<token>/xac-nhan/` -> `templates/registration/reset_confirm.html`
- `/dat-lai-mat-khau/hoan-tat/` -> `templates/registration/reset_complete.html`
- `/thong-tin-tai-khoan/` -> `templates/edit_profile.html`
- `/dia-chi-giao-hang/` -> `templates/edit_info.html`
- `/don-hang-da-mua/` -> `templates/order_cus.html`
- account sidebar -> `templates/partials/account_sidebar.html`

Ghi chú: `reset_done.html`, `reset_confirm.html`, `reset_complete.html` còn class/copy legacy như `organic-breadcrumb`, `Home`, `Shop`, `category.html`, `Fashon Category`.

#### Cart/order/checkout chưa cập nhật

- `/gio-hang/` -> `templates/cart/cart_view.html`
- HTMX cart partials -> `templates/cart/cart_items.html`, `templates/cart/cart_menu.html`, `templates/cart/cart_update.html`
- `/thanh-toan/` -> `templates/cart/checkout.html`
- `/don-hang/thanh-cong/<int:order_id>/` -> `templates/cart/order_success.html`
- `/don-hang/<int:order_id>/` -> `templates/cart/order_detail.html`
- invoice -> `templates/invoice.html`

Ghi chú: `invoice.html` còn logo eApp và brand "Nhà Yến Ngân Hà"; `order_detail.html` còn thông tin chuyển khoản demo `Ngân hàng XYZ`, `123456789`, `Công ty ABC`.

#### Static utility/legacy chưa cập nhật

- `/thanh-cong/` -> `templates/success.html`
- `/ctv/` -> `templates/CTV.html`
- `templates/view_cart.html` nếu route/include cũ còn dùng

Ghi chú: `CTV.html` còn nội dung tuyển cộng tác viên bán Yến Sào và số điện thoại cũ; `view_cart.html` còn class legacy như `hero`, `untree_co-section`, `site-blocks-table`.

#### Branding, meta, SEO, email chưa cập nhật

- `templates/partials/meta.html`
- `templates/partials/meta_product.html`
- `templates/partials/meta_post.html`
- `templates/partials/contact_modal.html`
- `templates/partials/error_404_500.html`
- `templates/partials/navbar.html` nếu còn được include ở route cũ
- `templates/robots.txt`
- `templates/sitemap.xml` nếu có trong repo
- `App_Core/sitemap.py`
- email templates trong `templates/registration/*.html` và `templates/registration/*.email`
- favicon/logo/footer/chat script trong `templates/base.html`
- logo/brand trong `templates/invoice.html`

Ghi chú cụ thể đang thấy:

- `base.html` còn favicon `canhan/img/logo-eapp/favicon-eapp.ico`, footer link `eApp.vn` và script `chatbox.eapp.vn`.
- `partials/meta*.html` và `robots.txt` còn domain `demoweb.eapp.vn`, keyword/copy eApp và logo eApp.
- Email templates còn link/logo `https://eapp.vn/`, `khoa.eapp@gmail.com` và copy "Ứng Dụng Miễn Phí".
- `partials/navbar.html` còn logo eApp; nếu template này không còn dùng thì có thể xóa hoặc để ngoài flow sau khi xác nhận.

#### Admin/quanly còn cần thay branding cơ bản

Không redesign admin trong task public UI, nhưng còn các điểm brand cũ cần thay:

- `templates/quanly/quanly.html`: favicon eApp, logo eApp, footer `eApp.vn`.
- `templates/quanly/marketing_email_form.html`: kiểm tra default copy/placeholder trước khi gửi marketing email.
- Email marketing/admin templates trong `templates/registration/*.email`: logo/domain/copy eApp.

#### Route render template nhưng template chưa tồn tại

Các route này đang render template không có trong thư mục `templates`, nên cần tạo template theo design system, redirect sang trang phù hợp, hoặc gỡ route nếu không dùng:

- `/yeu-thich/` -> `wishlist.html`
- `/so-sanh/` -> `compare.html`

### 9. Hoàn thiện content và SEO sau khi giao diện mới ổn

Khi public UI đã render đúng và dùng dữ liệu thật, phải thực hiện một vòng hậu giao diện trước khi bàn giao. Không xem thay UI là hoàn tất nếu các nội dung sau vẫn còn branding cũ, copy demo hoặc SEO mặc định.

Nguồn nội dung nên đọc trước:

```bash
rg --files docs | rg "customer|persona|brand|seo|content|profile"
sed -n '1,260p' docs/customer_info.md
sed -n '1,260p' docs/customer_persona.md
```

Nếu repo không có `docs/customer_info.md` hoặc `docs/customer_persona.md`, yêu cầu user cung cấp file/thông tin tương đương. Chỉ fallback sang nội dung hiện có, footer, trang liên hệ, email template và yêu cầu gần nhất của user khi user xác nhận không có tài liệu riêng.

Các việc bắt buộc:

- Cập nhật copy chính trên `home.html`, `about.html`, `contact.html`, list/detail page theo persona, pain point, lợi ích và CTA thật.
- Rà toàn bộ số điện thoại, email, địa chỉ, Zalo, social, domain trong `base.html`, footer, contact page, product detail, invoice và email templates.
- Cập nhật `templates/partials/meta.html`, `meta_product.html`, `meta_post.html`: description, keywords, Open Graph, Twitter card, robots meta và fallback description khi dữ liệu DB trống.
- Cập nhật structured data JSON-LD: dùng đúng loại schema phù hợp (`LocalBusiness`, `Organization`, `Product`, `Article`, `Service`), logo, ảnh, địa chỉ, điện thoại, email, `areaServed`, `sameAs`.
- Cập nhật `templates/robots.txt`: chặn admin, tài khoản, cart/checkout, search/filter rác; không tạo group bot riêng `Allow: /` làm vô hiệu rule chặn.
- Cập nhật `App_Core/sitemap.py` và `templates/sitemap.xml`: URL canonical, priority/changefreq theo trọng tâm business, `lastmod`, image sitemap URL tuyệt đối và caption sạch HTML.
- Chuẩn hóa route quan trọng nếu cần: dùng trailing slash nhất quán, redirect 301 từ legacy URL sang URL chuẩn, đảm bảo sitemap trỏ URL chuẩn.
- Rà email transactional/marketing để không còn logo, domain, số điện thoại, địa chỉ hoặc subject của brand cũ. Phân biệt rõ email quản lý nhận thông báo (`kienanbuild@gmail.com`) với email/tài khoản SMTP gửi đi trong `.env`.
- Rà title/meta của admin/quanly ở mức branding cơ bản, nhưng không đổi UI quản trị nếu không được yêu cầu.

Lệnh rà nhanh:

```bash
rg -n "demo|example|Lorem|090|info@|old-domain|brand cũ|BÁO GIÁ SỬA CHỮA" templates App_Core App_Product App_Post Project docs -S
rg -n "meta|og:|twitter|ld\\+json|robots|sitemap|canonical" templates App_Core App_Product App_Post Project -S
python3 manage.py shell -c "from django.test import Client; c=Client(); urls=['/','/lien-he/','/gioi-thieu/','/san-pham/','/bai-viet/','/robots.txt','/sitemap.xml']; print([(u,c.get(u).status_code,c.get(u).get('Content-Type')) for u in urls])"
```

Sau khi sửa SEO, render thêm ít nhất một trang detail sản phẩm và một trang detail bài viết nếu database có dữ liệu:

```bash
python3 manage.py shell -c "from django.test import Client; from App_Product.models import Product; from App_Post.models import Post; c=Client(); urls=[]; p=Product.objects.first(); a=Post.objects.first(); urls += [p.get_absolute_url()] if p else []; urls += [a.get_absolute_url()] if a else []; print([(u,c.get(u).status_code) for u in urls])"
```

### 10. Kiểm tra bắt buộc theo từng nhóm

Chạy system check:

```bash
python3 manage.py check
```

Kiểm tra JS nếu có file JS riêng:

```bash
node --check static/website/js/<brand_slug>.js
```

Render nhanh bằng Django test client:

```bash
python3 manage.py shell -c "from django.test import Client; c=Client(HTTP_USER_AGENT='Mozilla/5.0'); urls=['/','/san-pham/','/bai-viet/','/lien-he/']; print([(u,c.get(u).status_code) for u in urls])"
```

Khi nhóm có trang cần đăng nhập, login test user trước:

```bash
python3 manage.py shell -c "from django.test import Client; c=Client(HTTP_USER_AGENT='Mozilla/5.0'); print(c.login(username='quanly', password='quanly123')); urls=['/thong-tin-tai-khoan/','/dia-chi-giao-hang/','/don-hang-da-mua/']; print([(u,c.get(u).status_code) for u in urls])"
```

Khi nhóm có form bình luận/đánh giá, test cả anonymous và authenticated:

```bash
python3 manage.py shell -c "from django.test import Client; urls=['/san-pham/<category>/<product>/','/bai-viet/<subject>/<post>/']; c=Client(HTTP_USER_AGENT='Mozilla/5.0'); print('anon', [(u,c.get(u).status_code) for u in urls]); c.login(username='quanly', password='quanly123'); print('auth', [(u,c.get(u).status_code) for u in urls])"
```

Nếu có server local:

```bash
curl -A Mozilla/5.0 -I http://127.0.0.1:8000/
curl -A Mozilla/5.0 -I http://127.0.0.1:8000/static/website/css/<brand_slug>.css
```

Kiểm tra HTML đã dùng media/static đúng:

```bash
curl -A Mozilla/5.0 -s http://127.0.0.1:8000/ -o /tmp/ui_home.html
rg -n "/static/website|/media/|images/" /tmp/ui_home.html
```

Chụp screenshot desktop/mobile khi thay đổi giao diện đáng kể:

```bash
playwright screenshot --viewport-size=1440,1200 http://127.0.0.1:8000/ /tmp/ui_desktop.png
playwright screenshot --viewport-size=390,1200 http://127.0.0.1:8000/ /tmp/ui_mobile.png
```

Kiểm tra trực quan:

- navbar không tràn chữ
- dropdown không bị che
- mobile offcanvas mở từ trái sang phải, có backdrop, click bên ngoài đóng được
- mobile spacing/font/card compact hơn desktop, không tạo khoảng trắng lớn
- section nhiều card dùng grid hoặc slider/swiper phù hợp
- slider/swiper có nút previous/next nổi, nền mờ, không che nội dung chính
- hàng card không có vệt tối ngang do `box-shadow`, scrollbar, overflow hoặc block sát bên dưới
- ảnh render từ static/media
- CTA/form không mất CSRF
- comment/review/cart/account forms không mất field name hoặc HTMX target
- text không đè lên nhau
- trang list/detail dùng dữ liệu DB thật

### 11. Ghi nhận sau khi hoàn tất

Khi báo cáo kết quả, nêu ngắn gọn:

- template nào đã thay
- static/JS/CSS nào đã thêm
- backup nằm ở đâu
- seed command tên gì và tài khoản admin nếu có
- lệnh validation đã chạy
- content/SEO/meta/sitemap/robots đã cập nhật theo persona hoặc brand brief
- lỗi/chỗ chưa kiểm tra được nếu có

Không yêu cầu user copy file thủ công nếu file đã nằm trong repo.

## Checklist nhanh

- [ ] Đã đọc UI mới và template cũ
- [ ] Đã đọc file thông tin khách hàng/brand brief
- [ ] Đã đọc file customer persona
- [ ] Đã backup template cũ
- [ ] Đã copy asset vào `static`
- [ ] Đã tách CSS/JS khỏi HTML tĩnh
- [ ] Font chữ hỗ trợ đầy đủ tiếng Việt ở các weight đang dùng và có fallback rõ ràng
- [ ] `base.html` giữ đủ Django blocks/context hooks
- [ ] Navbar lấy category từ DB, không hard-code detail URL
- [ ] Mobile navbar dùng offcanvas trái sang phải, có backdrop và click ngoài để đóng
- [ ] Mobile UI đã giảm padding/margin/gap/font/card size để hiển thị nhiều thông tin hơn
- [ ] Section nhiều card dùng grid hoặc slider/swiper, có next/previous nổi và mờ khi cần
- [ ] Shadow của card/slider không dính vào scrollbar hoặc block khác tạo vệt tối ngang
- [ ] Homepage dùng queryset thật
- [ ] Database đã backup trước khi flush/seed
- [ ] Seed command chạy lại được, không nhân đôi dữ liệu
- [ ] Các trang con dùng cùng design system
- [ ] Nhóm public core đã thay
- [ ] Nhóm branding/meta/email đã thay
- [ ] Email quản lý nhận form là `kienanbuild@gmail.com`; SMTP/from-email vẫn theo `.env`
- [ ] Content public đã cập nhật theo persona/brand brief, không còn copy demo
- [ ] Contact info, social, domain, email template, invoice đã đồng bộ
- [ ] SEO meta/OG/Twitter/JSON-LD đã cập nhật
- [ ] `robots.txt` và `sitemap.xml`/`sitemap.py` đã rà theo URL chuẩn
- [ ] Legacy URL quan trọng đã redirect/canonical nhất quán nếu cần
- [ ] Nhóm auth/account đã thay
- [ ] Nhóm comment/review giữ đủ form nghiệp vụ
- [ ] Nhóm cart/order/checkout đã thay
- [ ] Nhóm static utility/landing phụ đã thay
- [ ] Admin/quanly chỉ thay branding/favicon/logo/title/footer, không đổi UI quản trị
- [ ] Missing/legacy route đã audit
- [ ] `manage.py check` OK
- [ ] Render URL chính trả 200
- [ ] Desktop/mobile screenshot không lỗi layout lớn
