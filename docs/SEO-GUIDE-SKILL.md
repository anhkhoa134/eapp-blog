---
name: django-interface-seo
description: Use this skill after creating, replacing, or significantly changing a Django website interface, especially when the project needs reusable SEO setup across different repositories: page meta, canonical URLs, robots rules, sitemap, structured data, image SEO, analytics hooks, and verification.
---

# Django Interface SEO Skill

Phiên bản: 2026-07-09

## Khi dùng

Dùng skill này sau khi tạo giao diện mới, thay giao diện cũ, hoặc đưa một bộ HTML/CSS/JS tĩnh vào project Django mà vẫn cần bảo đảm SEO cơ bản hoạt động đúng.

Skill này áp dụng được cho nhiều project khác nhau, không phụ thuộc vào tên domain, app, model hoặc template cụ thể. Khi dùng cho repo mới, luôn đọc code hiện tại rồi thay các ví dụ như `App_Product`, `Product`, `Post`, `templates/base.html` bằng tên thật của project.

Ưu tiên dùng cùng:

- [UI-REPLACEMENT-SKILL.md](UI-REPLACEMENT-SKILL.md) khi vừa thay giao diện Django.
- [SECURITY-DEBUG-ISSUES.md](SECURITY-DEBUG-ISSUES.md) khi cần kiểm tra production/debug/security trước khi deploy.
- [GOOGLE-LOGIN-SETUP.md](GOOGLE-LOGIN-SETUP.md) khi giao diện mới có luồng đăng nhập Google.

## Nguyên tắc

- Không hard-code brand, địa chỉ, số điện thoại, email, social profile, keyword hoặc slogan nếu chưa có nguồn trong repo hoặc user cung cấp.
- Không dùng placeholder kiểu `Tên Công Ty`, `example.com`, `path/to/image.jpg` trong code bàn giao.
- Không index trang cá nhân, giỏ hàng, checkout, login, admin, API utility, endpoint HTMX hoặc trang search/filter mỏng.
- Không tạo structured data giả. Chỉ thêm `rating`, `review`, `price`, `availability`, `sku`, `author`, `publisher.logo` khi có dữ liệu thật.
- Canonical mặc định nên bỏ query string, trừ khi URL query là một trang có giá trị SEO riêng và được thiết kế để index.
- Static CSS/JS/image phải crawl được; không chặn `/static/` hoặc asset cần render trong `robots.txt`.

## Input cần xác định

Trước khi sửa SEO, tìm cấu trúc project:

```bash
rg --files | sort
rg --files docs | rg "customer|persona|brand|seo|content|profile|setup|skill"
rg -n "TEMPLATES|STATIC_URL|STATICFILES_DIRS|MEDIA_URL|MEDIA_ROOT|ALLOWED_HOSTS|SITE_ID" . -g "*settings.py" -S
rg -n "urlpatterns|sitemap|robots|TemplateView|def .*home|class .*Sitemap|get_absolute_url" . -S
rg -n "class .*Category|class .*Product|class .*Post|class .*Article|class .*Service|class .*Page" . -S
rg -n "<title>|block title|block meta|canonical|og:title|ld\\+json|robots" templates -S
```

Xác định:

- domain production và domain staging nếu có
- template base/layout chính
- template trang chủ, listing, detail, contact/about, auth/account, cart/checkout nếu có
- app Django chính và URL names quan trọng
- model public cần index, ví dụ product, category, post, service, collection, landing page
- field slug, title, description, image, updated_at, status/published/active
- nguồn thông tin thương hiệu: file docs, footer hiện tại, trang contact, settings, env hoặc brief từ user
- sitemap/robots hiện có hay chưa

Nếu thiếu thông tin thương hiệu, chỉ triển khai khung kỹ thuật và dùng dữ liệu đang có trong model/template. Không tự viết claim marketing mới.

## Quy trình triển khai

### 1. Audit head và layout

Đọc template base trước:

```bash
sed -n '1,260p' templates/base.html
rg -n "{% block title|{% block meta|canonical|viewport|charset|og:|twitter:|ld\\+json" templates -S
```

Base layout nên có:

```django
<html lang="{{ LANGUAGE_CODE|default:'vi' }}">
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{% block title %}{{ site_name }}{% endblock title %}</title>
{% block meta %}{% endblock meta %}
{% block canonical %}
<link rel="canonical" href="{{ request.scheme }}://{{ request.get_host }}{{ request.path }}">
{% endblock canonical %}
```

Nếu project chưa luôn truyền `request` vào template, kiểm tra context processor:

```python
"django.template.context_processors.request"
```

### 2. Tạo partial meta dùng chung

Tạo hoặc chuẩn hóa các partial theo nhóm trang:

```text
templates/partials/meta_default.html
templates/partials/meta_noindex.html
templates/partials/meta_listing.html
templates/partials/meta_detail.html
```

Tên file có thể đổi theo convention repo. Mục tiêu là tách rõ:

- `meta_default`: trang chủ, about, contact, trang public chung
- `meta_listing`: category, collection, subject, service list, blog list
- `meta_detail`: product, article, service detail, landing detail
- `meta_noindex`: auth, account, cart, checkout, order, admin-like, utility endpoint

Ví dụ `meta_noindex.html`:

```html
<meta name="robots" content="noindex, nofollow">
```

Với listing có search/filter/sort:

```django
{% if request.GET %}
<meta name="robots" content="noindex, follow">
{% else %}
<meta name="robots" content="index, follow">
{% endif %}
```

### 3. Title và description

Mỗi trang public cần title và description riêng:

- Trang chủ: brand hoặc category chính, value proposition ngắn, không nhồi keyword.
- Listing: tên category/collection/subject và nội dung thật của nhóm.
- Detail: tên object, thuộc tính quan trọng, brand hoặc category.
- Blog/article: tiêu đề bài viết, mô tả tóm tắt, ngày cập nhật nếu có.

Giới hạn thực dụng:

- title khoảng 45-65 ký tự khi có thể
- description khoảng 120-160 ký tự khi có thể
- tránh cùng một description cho nhiều URL indexable
- dùng filter `striptags`, `truncatechars`, `default` để tránh HTML thô hoặc giá trị rỗng

Ví dụ:

```django
<meta name="description" content="{{ object.meta_description|default:object.description|striptags|truncatechars:155 }}">
```

### 4. Open Graph và Twitter Card

Trang public nên có:

```html
<meta property="og:type" content="website">
<meta property="og:title" content="...">
<meta property="og:description" content="...">
<meta property="og:url" content="{{ request.scheme }}://{{ request.get_host }}{{ request.path }}">
<meta property="og:image" content="...absolute image URL...">
<meta name="twitter:card" content="summary_large_image">
```

Với detail:

- product/service detail: `og:type` thường là `product` hoặc `website` tùy dữ liệu.
- article detail: `og:type` là `article`.
- image phải là absolute URL, đủ lớn cho share card, ưu tiên tỷ lệ gần 1200x630.

### 5. Canonical

Canonical mặc định nên dùng path sạch:

```django
<link rel="canonical" href="{{ request.scheme }}://{{ request.get_host }}{{ request.path }}">
```

Không dùng mặc định:

```django
{{ request.build_absolute_uri }}
```

làm canonical toàn site nếu project có search/filter/sort bằng query string.

Quy tắc:

- URL filter/search/sort: `noindex, follow` hoặc canonical về listing gốc.
- Pagination: giữ index nếu mỗi trang có giá trị, nhưng title nên có số trang.
- Biến thể sản phẩm: canonical về sản phẩm chính nếu biến thể không có nội dung độc lập.
- HTTP/HTTPS và www/non-www phải thống nhất ở reverse proxy hoặc settings production.

### 6. Robots.txt

Tạo hoặc kiểm tra route `robots.txt`. Nội dung mẫu:

```txt
User-agent: *
Disallow: /admin/
Disallow: /login/
Disallow: /logout/
Disallow: /register/
Disallow: /account/
Disallow: /cart/
Disallow: /checkout/
Disallow: /orders/
Disallow: /api/
Disallow: /htmx/
Disallow: /*?*

Sitemap: https://your-domain.example/sitemap.xml
```

Điều chỉnh path theo URL thật của project. Không chặn:

- `/static/`
- `/media/` nếu ảnh public cần index/share
- CSS/JS/font/image cần Google render trang

Lưu ý deindex: nếu URL đã bị index, `Disallow` có thể làm bot không thấy thẻ `noindex`. Khi cần gỡ index, cho crawl URL đó và trả `noindex` trước, sau khi biến mất khỏi index mới cân nhắc disallow.

### 7. Sitemap

Nếu project dùng `django.contrib.sitemaps`, tạo sitemap cho các nhóm public:

```python
from django.contrib.sitemaps import Sitemap

class PublicObjectSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return PublicObject.objects.filter(is_active=True)

    def lastmod(self, obj):
        return getattr(obj, "updated_at", None)
```

Checklist:

- chỉ đưa object public, active, published vào sitemap
- loại object thiếu slug/category nếu `get_absolute_url()` sẽ lỗi
- `location()` hoặc `get_absolute_url()` phải trả URL ổn định
- thêm static pages quan trọng: home, about, contact, pricing nếu có
- thêm category/collection/subject nếu là trang indexable thật
- nếu trên 50.000 URL, tách sitemap index
- nếu có image SEO quan trọng, cân nhắc custom sitemap có image namespace

### 8. Structured data

Chỉ thêm schema phù hợp với dữ liệu thật:

- `Organization` hoặc `LocalBusiness`: brand, logo, contact, sameAs.
- `WebSite` + `SearchAction`: khi có search nội bộ public.
- `BreadcrumbList`: detail và listing có breadcrumb thật.
- `Product`: product detail có tên, ảnh, mô tả, giá, tiền tệ, tình trạng hàng.
- `Article` hoặc `BlogPosting`: bài viết có author/publisher/date.
- `Service`: trang dịch vụ nếu project bán dịch vụ.

Ví dụ breadcrumb tổng quát:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {"@type": "ListItem", "position": 1, "name": "Trang chủ", "item": "{{ request.scheme }}://{{ request.get_host }}/"},
    {"@type": "ListItem", "position": 2, "name": "{{ parent.title|escapejs }}", "item": "{{ request.scheme }}://{{ request.get_host }}{{ parent.get_absolute_url }}"},
    {"@type": "ListItem", "position": 3, "name": "{{ object.title|escapejs }}", "item": "{{ request.scheme }}://{{ request.get_host }}{{ request.path }}"}
  ]
}
</script>
```

Sau khi thêm schema, kiểm tra bằng Rich Results Test hoặc Schema Markup Validator.

### 9. Image SEO

Kiểm tra ảnh trong giao diện mới:

- ảnh nội dung cần `alt` mô tả đúng object hoặc ngữ cảnh
- ảnh trang trí dùng `alt=""`
- ảnh card/listing dùng alt theo tên product/post/service
- ảnh OG phải tồn tại, absolute URL, không quá nhỏ
- ảnh lớn nên có kích thước rõ để giảm layout shift
- nếu upload rich text, cho phép nhập alt hoặc xử lý fallback hợp lý

Lệnh tìm nhanh:

```bash
rg -n "<img[^>]*(alt=\"\"|alt=''|alt=|>)|og:image|twitter:image" templates -S
```

### 10. Trang không nên index

Tìm và đổi sang `meta_noindex.html` cho các nhóm:

- login, register, logout, password reset
- account/profile/address/order history
- cart, checkout, payment, order success
- admin, dashboard, management
- API, webhook, HTMX, modal fragment, AJAX utility
- search/filter/sort query nếu không có landing SEO riêng
- trang lỗi hoặc trang trạng thái tạm

Không chỉ dựa vào `robots.txt`; template vẫn nên trả robots meta phù hợp khi bot/user truy cập được URL.

### 11. Analytics và verification

Nếu user yêu cầu analytics, dùng biến môi trường hoặc settings, không hard-code ID:

- `GA_MEASUREMENT_ID`
- `GTM_CONTAINER_ID`
- `GOOGLE_SITE_VERIFICATION`
- `BING_SITE_VERIFICATION`

Checklist sau deploy:

1. Xác minh domain trong Google Search Console.
2. Submit `/sitemap.xml`.
3. Kiểm tra `robots.txt`.
4. Kiểm tra indexing coverage.
5. Kiểm tra Core Web Vitals.
6. Kiểm tra Rich Results cho các trang có schema.
7. Kiểm tra Facebook Sharing Debugger hoặc công cụ share card tương đương.

## Lệnh kiểm tra

Local Django:

```bash
python3 manage.py check
```

Khi server local đang chạy:

```bash
curl -I http://127.0.0.1:8000/robots.txt
curl -I http://127.0.0.1:8000/sitemap.xml
curl -s http://127.0.0.1:8000/ | rg -i "canonical|og:title|og:image|twitter:card|ld\\+json|robots"
```

Kiểm tra URL có query:

```bash
curl -s "http://127.0.0.1:8000/path/?q=test&sort=new" | rg -i "canonical|robots"
```

Kiểm tra sitemap object nếu dùng Django shell:

```bash
python3 manage.py shell -c "from django.contrib.sitemaps.views import sitemap; print('sitemap import ok')"
```

## Checklist bàn giao

Trước khi kết thúc task SEO cho giao diện mới:

- base template có charset, viewport, title block, meta block, canonical block
- các trang public có title/description riêng
- trang private/utility có noindex
- canonical không sinh query string ngoài ý muốn
- robots.txt không chặn asset render
- sitemap chỉ chứa URL public hợp lệ
- structured data không có dữ liệu giả
- ảnh quan trọng có alt và OG image hợp lệ
- `python3 manage.py check` chạy được hoặc lỗi được ghi rõ
- kiểm tra ít nhất home, listing, detail, contact, auth/cart/checkout nếu tồn tại

## Ghi chú khi dùng cho project khác

Khi copy skill này sang project khác, đặt tại:

```text
$CODEX_HOME/skills/django-interface-seo/SKILL.md
```

Hoặc giữ trong repo tại `docs/SEO-GUIDE-SKILL.md` như tài liệu vận hành nội bộ. Mọi ví dụ trong file này là mẫu triển khai, không phải yêu cầu giữ nguyên tên file, tên route hoặc tên model.
