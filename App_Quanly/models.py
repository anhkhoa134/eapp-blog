from django.db import models


class QuanlyMenuConfig(models.Model):
    """Cấu hình thành phần hiển thị ở sidebar trang quản lý (singleton, chỉnh trong Django admin)."""

    # Nhóm kinh doanh
    show_dashboard = models.BooleanField(default=True, verbose_name='Dashboard')
    show_product = models.BooleanField(default=True, verbose_name='Sản Phẩm')
    show_productvariant = models.BooleanField(default=True, verbose_name='Biến Thể')
    show_category = models.BooleanField(default=True, verbose_name='Danh Mục')
    show_order = models.BooleanField(default=True, verbose_name='Đơn Hàng')
    show_customer = models.BooleanField(default=True, verbose_name='Khách Hàng')
    show_review = models.BooleanField(default=True, verbose_name='Đánh giá')

    # Nhóm nội dung
    show_post = models.BooleanField(default=True, verbose_name='Bài Viết')
    show_subject = models.BooleanField(default=True, verbose_name='Chủ Đề')
    show_comment = models.BooleanField(default=True, verbose_name='Bình Luận')

    # Nhóm hệ thống
    show_contact = models.BooleanField(default=True, verbose_name='Liên Hệ')
    show_email = models.BooleanField(default=True, verbose_name='Email')
    show_payment = models.BooleanField(default=True, verbose_name='Thanh Toán')
    show_pageview = models.BooleanField(default=True, verbose_name='Truy Cập')

    # (mã trang, nhãn hiển thị, cờ ẩn/hiện tương ứng, tên url)
    PAGE_REGISTRY = [
        ('dashboard', 'Dashboard', 'show_dashboard', 'quanly:dashboard'),
        ('product', 'Sản Phẩm', 'show_product', 'quanly:product_view'),
        ('productvariant', 'Biến Thể', 'show_productvariant', 'quanly:productvariant_view'),
        ('category', 'Danh Mục', 'show_category', 'quanly:category_view'),
        ('order', 'Đơn Hàng', 'show_order', 'quanly:order_view'),
        ('customer', 'Khách Hàng', 'show_customer', 'quanly:customer_view'),
        ('review', 'Đánh giá', 'show_review', 'quanly:review_view'),
        ('post', 'Bài Viết', 'show_post', 'quanly:post_view'),
        ('subject', 'Chủ Đề', 'show_subject', 'quanly:subject_view'),
        ('comment', 'Bình Luận', 'show_comment', 'quanly:comment_view'),
        ('contact', 'Liên Hệ', 'show_contact', 'quanly:contact_view'),
        ('email', 'Email', 'show_email', 'quanly:email_view'),
        ('payment', 'Thanh Toán', 'show_payment', 'quanly:paymentmethod_view'),
        ('pageview', 'Truy Cập', 'show_pageview', 'quanly:view_view'),
    ]

    default_page = models.CharField(
        max_length=20,
        choices=[(code, label) for code, label, _, _ in PAGE_REGISTRY],
        default='dashboard',
        verbose_name='Trang mặc định',
        help_text='Trang sẽ mở khi truy cập /quanly/. Nếu ẩn menu Dashboard, hãy chọn trang khác.',
    )

    class Meta:
        verbose_name = 'Cấu hình menu quản lý'
        verbose_name_plural = 'Cấu hình menu quản lý'

    def __str__(self):
        return 'Cấu hình menu trang quản lý'

    @property
    def default_page_url_name(self):
        for code, _, _, url_name in self.PAGE_REGISTRY:
            if code == self.default_page:
                return url_name
        return 'quanly:dashboard'

    def is_page_visible(self, code):
        for page_code, _, show_field, _ in self.PAGE_REGISTRY:
            if page_code == code:
                return getattr(self, show_field)
        return True

    def save(self, *args, **kwargs):
        self.pk = 1  # luôn ghi đè bản ghi duy nhất
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    # Các cờ gộp nhóm để template quyết định hiển thị <hr> phân cách
    @property
    def any_business(self):
        return self.show_product or self.show_productvariant or self.show_category or self.show_order or self.show_customer or self.show_review

    @property
    def any_content(self):
        return self.show_post or self.show_subject or self.show_comment

    @property
    def any_system(self):
        return self.show_contact or self.show_email or self.show_payment or self.show_pageview

    @property
    def any_above_content(self):
        return self.show_dashboard or self.any_business

    @property
    def any_above_system(self):
        return self.any_above_content or self.any_content


class CommerceBehaviorConfig(models.Model):
    """Cấu hình hành vi thương mại của website (singleton, chỉnh trong Django admin)."""

    allow_guest_cart = models.BooleanField(
        default=False,
        verbose_name='Cho phép thêm giỏ hàng khi chưa đăng nhập',
    )
    allow_guest_wishlist = models.BooleanField(
        default=False,
        verbose_name='Cho phép thêm yêu thích khi chưa đăng nhập',
    )

    class Meta:
        verbose_name = 'Cấu hình thương mại'
        verbose_name_plural = 'Cấu hình thương mại'

    def __str__(self):
        return 'Cấu hình thương mại'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
