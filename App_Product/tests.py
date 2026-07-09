import shutil
import tempfile
from io import BytesIO
from unittest.mock import patch

from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image as PILImage

from App_Account.forms import CustomPasswordChangeForm
from App_Quanly.models import CommerceBehaviorConfig
from App_Product.management.commands.seed_products import MockRequest, seed_category_images, seed_product_variants
from App_Product.models import (
    Attribute,
    Cart,
    CartItem,
    Category,
    Order,
    PaymentMethod,
    Product,
    ProductVariant,
    VariantAttribute,
    Wishlist,
)


class ProductVariantCartTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='customer', password='test-pass-123')
        self.category = Category.objects.create(name='Thời trang nam nữ')
        self.product = Product.objects.create(
            category=self.category,
            name='Ví da bò sáp handmade',
            price=500000,
            price_sale=0,
            stock=10,
            is_stock=True,
        )
        self.product.variants.all().delete()

        color_brown = Attribute.objects.create(key='Màu', value='Nâu')
        color_black = Attribute.objects.create(key='Màu', value='Đen')
        style_zip = Attribute.objects.create(key='Kiểu', value='Khóa kéo')
        style_snap = Attribute.objects.create(key='Kiểu', value='Nút bấm')

        self.brown_variant = ProductVariant.objects.create(
            product=self.product,
            price=500000,
            price_sale=450000,
            stock=3,
        )
        VariantAttribute.objects.create(variant=self.brown_variant, attribute=color_brown)
        VariantAttribute.objects.create(variant=self.brown_variant, attribute=style_zip)

        self.black_variant = ProductVariant.objects.create(
            product=self.product,
            price=520000,
            price_sale=0,
            stock=2,
        )
        VariantAttribute.objects.create(variant=self.black_variant, attribute=color_black)
        VariantAttribute.objects.create(variant=self.black_variant, attribute=style_snap)

        self.product.refresh_from_db()
        self.brown_variant.refresh_from_db()
        self.black_variant.refresh_from_db()

    def test_product_detail_lists_generic_variant_attributes(self):
        url = reverse(
            'product:product_detail',
            kwargs={
                'slug_category': self.category.slug,
                'slug_product': self.product.slug,
                'variant_slug': self.brown_variant.slug,
            },
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Chọn biến thể')
        self.assertContains(response, 'Màu: Nâu')
        self.assertContains(response, 'Kiểu: Khóa kéo')
        self.assertContains(response, 'Màu: Đen, Kiểu: Nút bấm')

    def test_add_to_cart_detail_uses_selected_variant(self):
        self.client.force_login(self.user)
        url = reverse('product:add_to_cart_detail', kwargs={'product_id': self.product.id})

        response = self.client.post(url, {'variant_id': self.black_variant.id})

        self.assertEqual(response.status_code, 200)
        cart_item = CartItem.objects.get(cart__user=self.user, product=self.product)
        self.assertEqual(cart_item.variant, self.black_variant)
        self.assertEqual(cart_item.quantity, 1)

    def test_add_to_cart_simple_uses_cheapest_variant(self):
        self.client.force_login(self.user)
        url = reverse('product:add_to_cart_simple', kwargs={'product_id': self.product.id})

        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        cart_item = CartItem.objects.get(cart__user=self.user, product=self.product)
        self.assertEqual(cart_item.variant, self.brown_variant)

    def test_guest_add_to_cart_when_enabled(self):
        CommerceBehaviorConfig.objects.create(allow_guest_cart=True)
        url = reverse('product:add_to_cart_simple', kwargs={'product_id': self.product.id})

        response = self.client.post(url, HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        cart = Cart.objects.get(user__isnull=True)
        cart_item = CartItem.objects.get(cart=cart, product=self.product)
        self.assertEqual(cart_item.variant, self.brown_variant)

    def test_guest_add_to_wishlist_when_enabled(self):
        CommerceBehaviorConfig.objects.create(allow_guest_wishlist=True)
        url = reverse('product:add_to_wishlist', kwargs={'product_id': self.product.id})

        response = self.client.post(url, HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Wishlist.objects.filter(user__isnull=True, product=self.product).exists())

    def test_product_detail_without_variant_slug_uses_cheapest_variant(self):
        url = reverse(
            'product:product_detail',
            kwargs={
                'slug_category': self.category.slug,
                'slug_product': self.product.slug,
            },
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['active_variant'], self.brown_variant)

    def test_product_all_search_includes_out_of_stock_products(self):
        product = Product.objects.create(
            category=self.category,
            name='iPhone 15 Pro Max 256GB',
            price=29990000,
            price_sale=27990000,
            stock=0,
            is_stock=False,
        )

        response = self.client.get(reverse('product:product_all'), {'product_name': 'Pro Max'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'iPhone 15 Pro Max 256GB')
        self.assertContains(response, 'Hết hàng')
        self.assertContains(response, 'btn-add-cart disabled')
        self.assertNotContains(
            response,
            f'hx-post="{reverse("product:add_to_cart_simple", kwargs={"product_id": product.id})}"',
        )

    def test_product_all_filters_by_variant_attribute(self):
        response = self.client.get(reverse('product:product_all'), {'attributes': 'Màu:Nâu'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)

    def test_product_all_returns_empty_for_unknown_variant_attribute(self):
        response = self.client.get(reverse('product:product_all'), {'attributes': 'Màu:Đỏ'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Không có sản phẩm nào được tìm thấy.')
        self.assertNotContains(response, self.product.name)

    def test_add_to_cart_detail_requires_variant_id(self):
        self.client.force_login(self.user)
        url = reverse('product:add_to_cart_detail', kwargs={'product_id': self.product.id})

        response = self.client.post(url)

        self.assertEqual(response.status_code, 400)
        self.assertIn('HX-Trigger', response.headers)
        self.assertFalse(CartItem.objects.filter(cart__user=self.user, product=self.product).exists())

    def test_add_to_cart_detail_rejects_variant_from_other_product(self):
        other_product = Product.objects.create(
            category=self.category,
            name='Ví da khác',
            price=600000,
            price_sale=0,
            stock=5,
            is_stock=True,
        )
        other_variant = other_product.variants.first()
        self.client.force_login(self.user)
        url = reverse('product:add_to_cart_detail', kwargs={'product_id': self.product.id})

        response = self.client.post(url, {'variant_id': other_variant.id})

        self.assertEqual(response.status_code, 404)
        self.assertFalse(CartItem.objects.filter(cart__user=self.user, product=self.product).exists())

    def test_cart_view_lists_managed_payment_methods(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=cart,
            product=self.product,
            variant=self.brown_variant,
            quantity=1,
        )
        paymentmethod = PaymentMethod.objects.create(
            user=self.user,
            name='Ví điện tử MoMo',
            account_name='PTcom',
            account_number='0938717380',
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('product:cart_view'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Giỏ hàng & giao hàng')
        self.assertContains(response, f'value="PM:{paymentmethod.id}"')
        self.assertContains(response, 'Ví điện tử MoMo')
        self.assertContains(response, '0938717380')

    def test_checkout_get_redirects_to_cart_view(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('product:checkout'))

        self.assertRedirects(response, reverse('product:cart_view'))

    @patch('App_Product.views.send_templated_mail')
    def test_guest_checkout_when_guest_cart_enabled(self, mocked_send_mail):
        CommerceBehaviorConfig.objects.create(allow_guest_cart=True)
        User.objects.create_user(username='quanly', password='test-pass-123', email='quanly@example.com')
        self.client.post(reverse('product:add_to_cart_simple', kwargs={'product_id': self.product.id}))

        response = self.client.post(reverse('product:checkout'), {
            'fullname': 'Khach vang lai',
            'phone': '0900000000',
            'shipping_address': '123 Nguyen Trai',
            'payment_method': 'COD',
        })

        order = Order.objects.get(phone='0900000000')
        self.assertIsNone(order.user)
        self.assertEqual(order.fullname, 'Khach vang lai')
        self.assertRedirects(response, reverse('product:order_success', args=[order.id]))
        self.assertIn(order.id, self.client.session.get('guest_order_ids', []))
        self.assertEqual(mocked_send_mail.call_count, 1)


class SeedProductVariantTests(TestCase):
    def test_seed_product_variants_reuses_default_variant_and_updates_stock(self):
        category = Category.objects.create(name='Điện thoại & Máy tính')
        product = Product.objects.create(
            category=category,
            name='iPhone 15 Pro Max 256GB',
            price=29990000,
            price_sale=27990000,
            stock=0,
            is_stock=False,
        )
        default_variant = product.variants.first()
        variants_data = [
            {
                'price': 29990000,
                'price_sale': 27990000,
                'stock': 12,
                'attributes': [('Màu sắc', 'Titan Tự Nhiên'), ('Dung lượng', '256GB')],
            },
            {
                'price': 34990000,
                'price_sale': 32990000,
                'stock': 5,
                'attributes': [('Màu sắc', 'Titan Đen'), ('Dung lượng', '512GB')],
            },
        ]

        seed_product_variants(product, variants_data, default_variant)

        product.refresh_from_db()
        default_variant.refresh_from_db()
        self.assertEqual(product.variants.count(), 2)
        self.assertEqual(default_variant.stock, 12)
        self.assertTrue(product.is_stock)
        self.assertEqual(product.stock, 17)
        self.assertTrue(
            default_variant.attributes.filter(attribute__key='Màu sắc', attribute__value='Titan Tự Nhiên').exists()
        )
        self.assertTrue(
            product.variants.filter(
                attributes__attribute__key='Dung lượng',
                attributes__attribute__value='512GB',
            ).exists()
        )


class SeedCategoryImageTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.settings_override = override_settings(MEDIA_ROOT=self.media_root)
        self.settings_override.enable()

    def tearDown(self):
        self.settings_override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def test_seed_category_images_uses_product_image_from_same_category(self):
        user = User.objects.create_user(username='seed-admin', password='test-pass-123')
        category = Category.objects.create(name='Điện thoại & Máy tính')
        product = Product(
            category=category,
            name='iPhone 15 Pro Max 256GB',
            price=29990000,
            price_sale=27990000,
            stock=12,
            is_stock=True,
        )
        product.request = MockRequest(user)

        image_buffer = BytesIO()
        PILImage.new('RGB', (20, 20), color='red').save(image_buffer, format='JPEG')
        product.image.save('iphone-seed.jpg', ContentFile(image_buffer.getvalue()), save=True)

        seed_category_images({category.name: category}, user)

        category.refresh_from_db()
        self.assertTrue(category.image)
        self.assertIn('/categories/', category.image.name)
        self.assertTrue(category.image.name.endswith('.webp'))


class PasswordStrengthValidationTests(TestCase):
    def test_check_password1_rejects_simple_passwords(self):
        url = reverse('account:check_password1')

        for password in ['123', 'abc', '12345678', 'abcdefgh', 'qwerty123', 'abababab']:
            with self.subTest(password=password):
                response = self.client.post(url, {'password1': password})

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'Mật khẩu')
                self.assertNotContains(response, 'Mật khẩu phù hợp')

    def test_check_password1_rejects_password_containing_username(self):
        response = self.client.post(reverse('account:check_password1'), {
            'username': 'customer',
            'password1': 'customer2026!',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'thông tin cá nhân')

    def test_check_password1_accepts_less_predictable_password(self):
        response = self.client.post(reverse('account:check_password1'), {
            'password1': 'Shop2026!Safe',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mật khẩu phù hợp')

    def test_change_password_form_rejects_simple_password_on_submit(self):
        user = User.objects.create_user(username='customer', password='CurrentPass2026!')
        form = CustomPasswordChangeForm(user=user, data={
            'old_password': 'CurrentPass2026!',
            'password1': 'abc12345',
            'password2': 'abc12345',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('Mật khẩu không được chứa chuỗi liên tiếp', str(form.errors))

    def test_check_password2_only_reports_match_status(self):
        response = self.client.post(reverse('account:check_password2'), {
            'password1': 'abc12345',
            'password2': 'abc12345',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Xác nhận mật khẩu trùng khớp')
        self.assertNotContains(response, 'Mật khẩu phù hợp')

    def test_check_password2_reports_mismatch(self):
        response = self.client.post(reverse('account:check_password2'), {
            'password1': 'abc12345',
            'password2': 'abc12346',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'không trùng với mật khẩu mới')
