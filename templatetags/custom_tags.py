from django import template
from App_Post.models import Subject
from App_Product.models import Category

register = template.Library()

################## tags ##################
# @register.inclusion_tag("partials/menu.html")
# def menu_top():
#     categories = Category.objects.all()
#     return {'categories':categories}

# @register.inclusion_tag("partials/menu_bottom.html")
# def menu_bottom():
#     subjects = Subject.objects.all()
#     return {'subjects':subjects}

# @register.inclusion_tag("partials/menu_top_post.html")
# def menu_top_post():
#     subjects = Subject.objects.all().order_by('id')
#     return {'subjects':subjects}

# @register.inclusion_tag("partials/menu_bottom_post.html")
# def menu_bottom_post():
#     subjects = Subject.objects.all().order_by('id')
#     return {'subjects':subjects}


@register.simple_tag
def your_custom_tag():
    return {'key': 'value'}

# {% load custom_tags %}
# {% your_custom_tag as custom_context %}
# {{ custom_context.key }}


################## filters ##################
# Lấy URL hiện tại, bỏ đi dấu / ở trước và sau URL đó
@register.filter
def strip_slashes(value):
    if isinstance(value, str):
        return value.strip('/')
    return value

# {% load custom_tags %}
# <p>URL hiện tại: {{ request.path|strip_slashes }}</p>

##### trong template.html
# URL hiện tại: {{ request.get_full_path }} # giống cái trên
# Path: {{ request.path }}
# URL đầy đủ: {{ request.build_absolute_uri }}
# Query string: {{ request.META.QUERY_STRING }}
# Lấy domain: https://{{ request.get_host }}

##### trong views.py
# from django.http import HttpResponse
# 'url':request.get_host(),
# 'full_url':request.build_absolute_uri('/'),

@register.filter
def remove_commas(value): # bỏ dấu ,
    try:
        return int(value.replace(',', ''))
    except (ValueError, AttributeError):
        return value
    
    
@register.filter
def remove_percent(value): # bỏ dấu % và .
    try:
        return int(value.replace('%', '').replace('.', '')) / 100
    except (ValueError, AttributeError):
        return value
    
    
@register.filter
def percentage(value): # thêm dấu %
    try:
        value = float(value)
        return f"{value}%"
    except (ValueError, TypeError):
        return value
    
@register.filter
def thousands_separator(value): # thêm dấu . phân cách phần nghìn
    try:
        value = float(value)
        return f"{value:,.0f}"
    except (ValueError, TypeError):
        return value
    
@register.filter(name='zip_two')
def zip_two_lists(a, b):
    return zip(a, b)

@register.filter
def intcomma(value):
    """
    Custom intcomma filter to format integers with comma as thousands separator.
    Example: 1234567 -> '1,234,567'
    """
    try:
        value = int(value)
        return f"{value:,}"
    except (TypeError, ValueError):
        return value  # Return original value if it's not an integer
# <p>Giá sản phẩm: {{ product.price|intcomma }} VND</p>

@register.filter
def discount_percent(price, price_sale):
    try:
        price = float(price)
        price_sale = float(price_sale)
        if price <= 0 or price_sale <= 0 or price_sale >= price:
            return 0
        return (1 - (price_sale / price)) * 100
    except (TypeError, ValueError, ZeroDivisionError):
        return 0

# Hiển thị ký tự a,b,c... tương ứng với số index
@register.filter
def chr_from_index(value):
    try:
        return chr(ord('a') + int(value))
    except:
        return ''

# Điều kiện với ký tự bắt đầu
@register.filter
def startswith(text, prefix):
    return str(text).startswith(prefix)

# Truncate text vẫn giữ nguyên HTML
@register.filter
def truncate_html(value, max_length=100):
    soup = BeautifulSoup(value, "html.parser")
    text = soup.get_text()
    truncated = text[:max_length].rstrip() + "..."
    return truncated
