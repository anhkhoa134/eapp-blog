from django.urls import path
from django.views.generic import RedirectView

from . import views


app_name = 'quanly'

urlpatterns = [
   path('quanly/', RedirectView.as_view(pattern_name='quanly:dashboard', permanent=False), name='legacy_dashboard_redirect'),
   path('quanly/<path:remaining>', RedirectView.as_view(url='/quan-ly/%(remaining)s', permanent=False, query_string=True), name='legacy_quanly_redirect'),

   path('quan-ly/', views.dashboard, name='dashboard'),
   # path('quan-ly/', views.post_view, name='dashboard'),
   path('quan-ly/thang-nay/', views.dashboard, name='dashboard_thangnay'),
   path('quan-ly/toan-thoi-gian/', views.fulltime, name='fulltime'),
   path('quan-ly/thong-tin-tai-khoan/', views.profile_quanly, name='profile_quanly'),

   ############# Product, Category #############
   path('quan-ly/san-pham/', views.product_view, name='product_view'),
   path('quan-ly/san-pham/danh-sach/', views.product_list, name='product_list'),
   path('quan-ly/san-pham/them/', views.add_product, name='add_product'),
   path('quan-ly/san-pham/xoa/<int:id>/', views.delete_product, name='delete_product'),
   path('quan-ly/san-pham/sua/<int:id>/', views.edit_product, name='edit_product'),
   path('quan-ly/san-pham/thong-so/sua/<int:id>/', views.edit_specification, name='edit_specification'),
   path('quan-ly/san-pham/thong-so-2/sua/<int:id>/', views.edit_specification_2, name='edit_specification_2'),
   path('quan-ly/san-pham/thong-so-3/sua/<int:id>/', views.edit_specification_3, name='edit_specification_3'),
   path('quan-ly/san-pham/thong-so-4/sua/<int:id>/', views.edit_specification_4, name='edit_specification_4'),

   path('quan-ly/danh-muc/', views.category_view, name='category_view'),
   path('quan-ly/danh-muc/danh-sach/', views.category_list, name='category_list'),
   path('quan-ly/danh-muc/them/', views.add_category, name='add_category'),
   path('quan-ly/danh-muc/xoa/<int:id>/', views.delete_category, name='delete_category'),
   path('quan-ly/danh-muc/sua/<int:id>/', views.edit_category, name='edit_category'),

   path('quan-ly/danh-muc-phu/', views.subcategory_view, name='subcategory_view'),
   path('quan-ly/danh-muc-phu/danh-sach/', views.subcategory_list, name='subcategory_list'),
   path('quan-ly/danh-muc-phu/them/', views.add_subcategory, name='add_subcategory'),
   path('quan-ly/danh-muc-phu/xoa/<int:id>/', views.delete_subcategory, name='delete_subcategory'),
   path('quan-ly/danh-muc-phu/sua/<int:id>/', views.edit_subcategory, name='edit_subcategory'),

   path('htmx/lay-danh-muc-phu/', views.get_subcategories, name='get_subcategories'),

   ############# Sản phẩm nhiều thuộc tính #############
   path('quan-ly/bien-the/', views.productvariant_view, name='productvariant_view'),
   ##### ProductVariant
   path('quan-ly/bien-the/danh-sach/', views.productvariant_list, name='productvariant_list'),
   path('quan-ly/bien-the/them/', views.add_productvariant, name='add_productvariant'),
   path('quan-ly/bien-the/xoa/<int:id>/', views.delete_productvariant, name='delete_productvariant'),
   path('quan-ly/bien-the/sua/<int:id>/', views.edit_productvariant, name='edit_productvariant'),

   ##### VariantAttribute

   ##### Attribute
   path('quan-ly/thuoc-tinh/danh-sach/', views.attribute_list, name='attribute_list'),
   path('quan-ly/thuoc-tinh/them/', views.add_attribute, name='add_attribute'),
   path('quan-ly/thuoc-tinh/xoa/<int:id>/', views.delete_attribute, name='delete_attribute'),
   path('quan-ly/thuoc-tinh/sua/<int:id>/', views.edit_attribute, name='edit_attribute'),

   ##### Import Excel
   path('quan-ly/san-pham/tai-len-zip/', views.upload_product_zip, name='upload_product_zip'),
   path('quan-ly/san-pham/tai-mau-zip/', views.download_sample_product_zip, name='download_sample_product_zip'),


   ############# Order #############
   path('quan-ly/don-hang/', views.order_view, name='order_view'),
   path('quan-ly/don-hang/danh-sach/', views.order_list, name='order_list'),
   path('quan-ly/don-hang/them/', views.add_order, name='add_order'),
   path('quan-ly/don-hang/xoa/<int:id>/', views.delete_order, name='delete_order'),
   path('quan-ly/don-hang/sua/<int:id>/', views.edit_order, name='edit_order'),

   ############# Customer, Review, Comment #############
   path('quan-ly/khach-hang/', views.customer_view, name='customer_view'),
   path('quan-ly/khach-hang/danh-sach/', views.customer_list, name='customer_list'),
   path('quan-ly/danh-gia/', views.review_view, name='review_view'),
   path('quan-ly/danh-gia/danh-sach/', views.review_list, name='review_list'),
   path('quan-ly/danh-gia/xoa/<int:id>/', views.delete_review, name='delete_review'),

   path('quan-ly/binh-luan/', views.comment_view, name='comment_view'),
   path('quan-ly/binh-luan/danh-sach/', views.comment_list, name='comment_list'),
   path('quan-ly/binh-luan/xoa/<int:id>/', views.delete_comment, name='delete_comment'),


   ############# Post, Subject #############
   path('quan-ly/bai-viet/', views.post_view, name='post_view'),
   path('quan-ly/bai-viet/danh-sach/', views.post_list, name='post_list'),
   path('quan-ly/bai-viet/them/', views.add_post, name='add_post'),
   path('quan-ly/bai-viet/xoa/<int:id>/', views.delete_post, name='delete_post'),
   path('quan-ly/bai-viet/sua/<int:id>/', views.edit_post, name='edit_post'),
   path('quan-ly/bai-viet/noi-dung/sua/<int:id>/', views.edit_content, name='edit_content'),

   path('quan-ly/chu-de/', views.subject_view, name='subject_view'),
   path('quan-ly/chu-de/danh-sach/', views.subject_list, name='subject_list'),
   path('quan-ly/chu-de/them/', views.add_subject, name='add_subject'),
   path('quan-ly/chu-de/xoa/<int:id>/', views.delete_subject, name='delete_subject'),
   path('quan-ly/chu-de/sua/<int:id>/', views.edit_subject, name='edit_subject'),

   path('quan-ly/chu-de-phu/', views.subsubject_view, name='subsubject_view'),
   path('quan-ly/chu-de-phu/danh-sach/', views.subsubject_list, name='subsubject_list'),
   path('quan-ly/chu-de-phu/them/', views.add_subsubject, name='add_subsubject'),
   path('quan-ly/chu-de-phu/xoa/<int:id>/', views.delete_subsubject, name='delete_subsubject'),
   path('quan-ly/chu-de-phu/sua/<int:id>/', views.edit_subsubject, name='edit_subsubject'),

   path('htmx/lay-chu-de-phu/', views.get_subsubjects, name='get_subsubjects'),


   ############# Contact #############
   path('quan-ly/lien-he/', views.contact_view, name='contact_view'),
   path('quan-ly/lien-he/danh-sach/', views.contact_list, name='contact_list'),
   path('quan-ly/lien-he/xoa/<int:id>/', views.delete_contact, name='delete_contact'),

   ############# Email #############
   path('quan-ly/email/', views.email_view, name='email_view'),
   path('quan-ly/email/danh-sach/', views.email_list, name='email_list'),
   path('quan-ly/email/gui-marketing/', views.send_marketing_email, name='send_marketing_email'),

   ############# PaymentMethod #############
   path('quan-ly/phuong-thuc-thanh-toan/', views.paymentmethod_view, name='paymentmethod_view'),
   path('quan-ly/phuong-thuc-thanh-toan/danh-sach/', views.paymentmethod_list, name='paymentmethod_list'),
   path('quan-ly/phuong-thuc-thanh-toan/them/', views.add_paymentmethod, name='add_paymentmethod'),
   path('quan-ly/phuong-thuc-thanh-toan/xoa/<int:id>/', views.delete_paymentmethod, name='delete_paymentmethod'),
   path('quan-ly/phuong-thuc-thanh-toan/sua/<int:id>/', views.edit_paymentmethod, name='edit_paymentmethod'),

   ############# View #############
   path('quan-ly/truy-cap/', views.view_view, name='view_view'),
   path('quan-ly/truy-cap/danh-sach/', views.view_list, name='view_list'),
]
