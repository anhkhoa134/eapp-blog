# Tổng hợp các hằng số dùng chung của App_Core về 1 nơi
from django.templatetags.static import static
from django.utils.functional import lazy

# static() chỉ được gọi khi giá trị thực sự được dùng (lazy),
# tránh lỗi "Missing staticfiles manifest entry" khi chạy collectstatic
# (lúc đó manifest chưa được tạo nhưng models.py đã import file này)
static_lazy = lazy(static, str)

# Giới hạn số lượng sản phẩm và bài viết
LIMIT_PRODUCT_OR_POST = 1000

# Giới hạn tổng dung lượng toàn Project
MAX_UPLOAD_SIZE = 1000 * 1024 * 1024  # 1000MB

# Giới hạn tổng dung lượng file trong một lần upload
MAX_UPLOAD_REQUEST_SIZE = 50 * 1024 * 1024  # 50MB


############# Choices dùng cho models / forms / filters #############
GENDER_CHOICES = [('', ''),
                  ('Nam', 'Nam'),
                  ('Nữ', 'Nữ'),
                  ('Khác', 'Khác'), ]

# Dạng boolean, dùng cho ProductForm và ProductFilter (is_stock là BooleanField)
IS_STOCK_BOOL = [(True, 'Còn hàng'),
                 (False, 'Hết hàng')]

IS_PAID =  [('Đã thanh toán', 'Đã thanh toán'),
            ('Chưa thanh toán', 'Chưa thanh toán'),]

STATUS_ORDER = [('Chờ xử lý', 'Chờ xử lý'),
                ('Đang vận chuyển', 'Đang vận chuyển'),
                ('Giao thành công', 'Giao thành công'),
                ('Đã huỷ', 'Đã huỷ'),]


############# Widget attrs mặc định cho forms #############
INPUT_ATTRS = {'class': 'form-control'}


############# Tài khoản không tính là khách hàng (thống kê, danh sách user) #############
excluded_usernames = ["admin", "quanly", "nhanvien", ]


############# Ảnh tĩnh mặc định (icon, placeholder) #############
# sử dụng static_lazy để lấy đường dẫn tới ảnh tĩnh
profile_icon_url = static_lazy('canhan/img/icon/avatar.webp')
static_placeholder = static_lazy('canhan/img/placeholder.webp')
default_thumbnail_url = static_lazy('canhan/img/placeholder.webp')
static_avatar = static_lazy('canhan/img/icon/avatar.webp')

category_icon_url = static_lazy('canhan/img/icon/3d-category-icon.webp')
subcategory_icon_url = static_lazy('canhan/img/icon/3d-subcategory-icon.webp')
product_icon_url = static_lazy('canhan/img/icon/3d-product-icon.webp')
subject_icon_url = static_lazy('canhan/img/icon/3d-subject-icon.webp')
subsubject_icon_url = static_lazy('canhan/img/icon/3d-subsubject-icon.webp')
post_icon_url = static_lazy('canhan/img/icon/3d-post-icon.webp')
