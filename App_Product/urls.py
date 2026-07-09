from django.urls import path

from . import views


app_name = 'product'

urlpatterns = [
    path('san-pham/', views.product_all, name='product_all'),
    path('danh-muc/<slug:slug_category>/', views.product_all, name='product_all'),
    path('danh-muc/<slug:slug_category>/<slug:slug_subcategory>/', views.product_all, name='product_all'),
    path('san-pham/<slug:slug_category>/<slug:slug_product>/', views.product_detail, name='product_detail'),
    path('san-pham/<slug:slug_category>/<slug:slug_product>/<slug:variant_slug>/', views.product_detail, name='product_detail'),
    path('htmx/tai-danh-muc-phu/', views.load_subcategories, name='load_subcategories'),
    path('gio-hang/', views.cart_view, name='cart_view'),
    path('htmx/menu-cart/', views.hx_menu_cart, name='hx_menu_cart'),
    path('htmx/tong-tien/', views.hx_total_price, name='hx_total_price'),
    path('htmx/add-simple/<int:product_id>/', views.add_to_cart_simple, name='add_to_cart_simple'),
    path('htmx/add-detail/<int:product_id>/', views.add_to_cart_detail, name='add_to_cart_detail'),
    path('htmx/remove/<int:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('htmx/update/<int:cart_item_id>/', views.update_cart_item, name='update_cart_item'),
    path('htmx/decrease/<int:cart_item_id>/', views.decrease_cart_item, name='decrease_cart_item'),
    path('htmx/increase/<int:cart_item_id>/', views.increase_cart_item, name='increase_cart_item'),
    path('thanh-toan/', views.checkout, name='checkout'),
    path('don-hang/thanh-cong/<int:order_id>/', views.order_success, name='order_success'),
    path('don-hang/<int:order_id>/', views.order_detail, name='order_detail'),
    path('yeu-thich/', views.wishlist_view, name='wishlist_view'),
    path('yeu-thich/them/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('yeu-thich/xoa/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('so-sanh/', views.compare_view, name='compare_view'),
    path('so-sanh/them/<int:product_id>/', views.add_to_compare, name='add_to_compare'),
    path('so-sanh/xoa/<int:product_id>/', views.remove_from_compare, name='remove_from_compare'),
    path('danh-gia/them/<int:product_id>/', views.add_review, name='add_review'),
]
