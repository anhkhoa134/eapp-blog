from django import forms
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse

from .models import CommerceBehaviorConfig, QuanlyMenuConfig


class QuanlyMenuConfigForm(forms.ModelForm):
    class Meta:
        model = QuanlyMenuConfig
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        default_page = cleaned_data.get('default_page')
        for code, label, show_field, _ in QuanlyMenuConfig.PAGE_REGISTRY:
            if code == default_page and not cleaned_data.get(show_field):
                raise forms.ValidationError(
                    f'Trang mặc định "{label}" đang bị ẩn khỏi menu. Hãy chọn trang khác hoặc bật lại menu "{label}".'
                )
        return cleaned_data


@admin.register(QuanlyMenuConfig)
class QuanlyMenuConfigAdmin(admin.ModelAdmin):
    form = QuanlyMenuConfigForm
    fieldsets = (
        ('Trang mặc định', {
            'fields': ('default_page',),
            'description': 'Trang sẽ mở khi truy cập /quan-ly/.',
        }),
        ('Kinh doanh', {
            'fields': ('show_dashboard', 'show_product', 'show_productvariant', 'show_category', 'show_order', 'show_customer', 'show_review'),
            'description': 'Website dạng blog/nội dung có thể bỏ chọn Dashboard, Đơn Hàng, Khách Hàng...',
        }),
        ('Nội dung', {
            'fields': ('show_post', 'show_subject', 'show_comment'),
        }),
        ('Hệ thống', {
            'fields': ('show_contact', 'show_email', 'show_payment', 'show_pageview'),
        }),
    )

    def has_add_permission(self, request):
        return not QuanlyMenuConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        config = QuanlyMenuConfig.load()
        return redirect(reverse('admin:App_Quanly_quanlymenuconfig_change', args=[config.pk]))


@admin.register(CommerceBehaviorConfig)
class CommerceBehaviorConfigAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Tài khoản khách', {
            'fields': ('allow_guest_cart', 'allow_guest_wishlist'),
            'description': 'Nếu tắt, khách chưa đăng nhập sẽ được chuyển tới trang đăng nhập khi thêm giỏ hàng hoặc yêu thích.',
        }),
    )

    def has_add_permission(self, request):
        return not CommerceBehaviorConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        config = CommerceBehaviorConfig.load()
        return redirect(reverse('admin:App_Quanly_commercebehaviorconfig_change', args=[config.pk]))
