import json

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Case, F, IntegerField, Q, Subquery, When
from django.db.models.functions import Coalesce
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from templated_email import send_templated_mail

from App_Account.models import Checkout_info
from App_Product.models import (
    Cart,
    CartItem,
    Category,
    Compare,
    Order,
    OrderItem,
    PaymentMethod,
    Product,
    ProductVariant,
    Review,
    SubCategory,
    VariantAttribute,
    Wishlist,
)


def _wishlist_product_ids(request):
    if request.user.is_authenticated:
        return set(request.user.wishlist.values_list('product_id', flat=True))
    return set()

def generate_response(message, type='bg-success'):
    # print(message, type)
    return HttpResponse(
        status=204,
        headers={
            'HX-Trigger': json.dumps({
                "listChange": None,
                "showMessage": {"message": message, "type": type}
            })
        }
    )

def _variant_effective_price():
    return Case(
        When(price_sale__gt=0, then=F('price_sale')),
        default=F('price'),
        output_field=IntegerField(),
    )

def _product_variants(product):
    return (
        product.variants
        .prefetch_related('attributes__attribute')
        .annotate(effective_price=_variant_effective_price())
        .order_by('effective_price', 'id')
    )

def _get_prefetched_cart(cart):
    return (
        Cart.objects
        .prefetch_related('items__product', 'items__variant__attributes__attribute')
        .get(pk=cart.pk)
    )

def _get_order_paymentmethod(payment_method):
    if payment_method and payment_method.startswith('PM:'):
        paymentmethod_id = payment_method.replace('PM:', '', 1)
        if paymentmethod_id.isdigit():
            return PaymentMethod.objects.filter(id=paymentmethod_id).first()
    return None

def _payment_method_display(payment_method, paymentmethod=None):
    if paymentmethod:
        return paymentmethod.name
    if payment_method == 'COD':
        return 'Thanh toán khi nhận hàng (COD)'
    if payment_method == 'BANK':
        return 'Chuyển khoản ngân hàng'
    return payment_method or ''


def hx_menu_cart(request):
    cart = None
    cart_items = []
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).prefetch_related('items').first()
        cart_items = list(cart.items.all()) if cart else []
    return render(request, 'partials/menu_cart.html', {'cart': cart, 'cart_items': cart_items})


def hx_total_price(request):
    total_price_vnd = 0
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).prefetch_related('items__product', 'items__variant').first()
        total_price_vnd = cart.total_price() if cart else 0
    return render(request, 'partials/total_price.html', {'total_price_vnd': total_price_vnd})

def product_all(request, slug_category=None, slug_subcategory=None):
    # Lọc sản phẩm theo Category và SubCategory cho href button
    if slug_category and slug_subcategory: # products thuộc Subcategory
        products = Product.objects.filter(category__slug=slug_category, 
                                    subcategory__slug=slug_subcategory).order_by('-id')
    elif slug_category: # products thuộc category
        products = Product.objects.filter(category__slug=slug_category).order_by('-id')
    else: # tất cả products
        products = Product.objects.all().order_by('-id')
    
    # Số lượng sản phẩm trước khi lọc
    total_products = products.count()
    
    # Lấy các bộ lọc
    categories_filter = request.GET.getlist('categories')
    subcategories_filter = request.GET.getlist('subcategories')
    attributes_filter = request.GET.getlist('attributes')  # Lọc theo attributes
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    order_by = request.GET.get('order_by')
    search_query = request.GET.get('product_name')  # Tìm kiếm theo tên sản phẩm
    
    # Thêm category và subcategory vào filter khi có slug từ URL
    if slug_category and not categories_filter:
        try:
            category_obj = Category.objects.get(slug=slug_category)
            categories_filter = [str(category_obj.id)]
        except Category.DoesNotExist:
            pass
    
    if slug_subcategory and not subcategories_filter:
        try:
            subcategory_obj = SubCategory.objects.get(slug=slug_subcategory)
            subcategories_filter = [str(subcategory_obj.id)]
        except SubCategory.DoesNotExist:
            pass

    # Áp dụng tìm kiếm theo tên sản phẩm
    if search_query:
        products = products.filter(name__icontains=search_query)

    # Áp dụng bộ lọc Category và SubCategory
    if categories_filter:
        products = products.filter(category__id__in=categories_filter)
    if subcategories_filter:
        products = products.filter(subcategory__id__in=subcategories_filter)

    # Áp dụng các bộ lọc khác

    if price_min:
        products = products.filter(Q(price_sale__gte=price_min) | Q(price_sale__isnull=True, price__gte=price_min))
    if price_max:
        products = products.filter(Q(price_sale__lte=price_max) | Q(price_sale__isnull=True, price__lte=price_max))
    
    # Áp dụng bộ lọc theo Attributes với phép "OR"
    if attributes_filter:
        attribute_conditions = Q()
        for attribute in attributes_filter:
            key, value = attribute.split(':')
            # Thêm điều kiện "OR" cho mỗi thuộc tính
            attribute_conditions |= Q(
                variants__attributes__attribute__key=key,
                variants__attributes__attribute__value=value
            )
        # Lọc sản phẩm với tất cả các điều kiện "OR"
        products = products.filter(attribute_conditions).distinct()
            
    # Lấy danh sách sản phẩm unique
    unique_product_ids = products.distinct().values('id')
    # Lọc các sản phẩm chính dựa trên subquery
    products = Product.objects.filter(id__in=Subquery(unique_product_ids))

    # Số lượng sản phẩm sau khi lọc
    filtered_products_count = products.count()
    
    # Nhóm attributes theo key
    attributes = VariantAttribute.objects.values_list('attribute__key', 'attribute__value').distinct()
    # Khởi tạo dictionary rỗng
    grouped_attributes = {}

    # Lặp qua từng cặp key-value từ truy vấn
    for key, value in attributes:
        # Kiểm tra nếu key đã tồn tại trong dictionary
        if key in grouped_attributes:
            # Thêm value vào danh sách của key
            grouped_attributes[key].append(value)
        else:
            # Tạo key mới với value là một danh sách
            grouped_attributes[key] = [value]
    # print("Grouped Attributes:", grouped_attributes)
    
    # Áp dụng sắp xếp
    if order_by == 'name_asc':
        products = products.order_by('name')
    elif order_by == 'name_desc':
        products = products.order_by('-name')
    elif order_by == 'price_asc':
        products = products.order_by(Coalesce('price_sale', 'price').asc())
    elif order_by == 'price_desc':
        products = products.order_by(Coalesce('price_sale', 'price').desc())
    # elif order_by == 'price_asc':
    #     products = products.order_by('variants__price')
    # elif order_by == 'price_desc':
    #     products = products.order_by('-variants__price')
    elif order_by == 'newest':
        products = products.order_by('-created_at')
    elif order_by == 'oldest':
        products = products.order_by('created_at')

    # Phân trang
    paginator = Paginator(products, 12)  # 12 sản phẩm mỗi trang
    page = request.GET.get('page')
    products = paginator.get_page(page)
    
    # Chuẩn bị context
    context = {
        'category': Category.objects.get(slug=slug_category) if slug_category else None,
        'subcategory': SubCategory.objects.get(slug=slug_subcategory) if slug_subcategory else None,
        'products': products,
        'total_products': total_products,
        'filtered_products_count': filtered_products_count,
        'categories': Category.objects.all(),
        'subcategories': SubCategory.objects.all() if not categories_filter else SubCategory.objects.filter(category_id__in=categories_filter),
        'grouped_attributes': grouped_attributes,  # Truyền attributes theo nhóm
        'selected_categories': categories_filter,
        'selected_subcategories': subcategories_filter,
        'selected_attributes': attributes_filter,
        'price_min': price_min,
        'price_max': price_max,
        'order_by': order_by,
        'search_query': search_query,
        'wishlist_product_ids': _wishlist_product_ids(request),

        'target_content_id': '#product-content',
        'include_form_filter_id': '#product-filter-form',
    }

    # Xử lý yêu cầu HTMX nếu có
    if request.headers.get('HX-Request'):
        return render(request, 'partials/products_pagination.html', context)
    
    return render(request, 'product_all.html', context)

def load_subcategories(request):
    categories_filter = request.GET.getlist('categories')
    # print('load_subcategories: categories_filter', len(categories_filter), categories_filter)
    
    if categories_filter:
        # Nếu có Category được chọn, lọc các SubCategory tương ứng
        subcategories = SubCategory.objects.filter(category__id__in=categories_filter).order_by('name')
    else:
        # Nếu không chọn Category, hiển thị toàn bộ SubCategory
        subcategories = SubCategory.objects.all().order_by('name')

    context = {
        'subcategories': subcategories,
        'selected_subcategories': request.GET.getlist('subcategories'),  # Giữ lại SubCategory đã chọn
    }
    
    return render(request, 'partials/subcategory_checkboxes.html', context)

def product_detail(request, slug_category, slug_product, variant_slug=None):
    product = get_object_or_404(Product, slug=slug_product) # product của Model Product
    productphotos = product.photo_product.all() # product của Model ProductPhoto
    related_products = Product.objects.filter(category=product.category).exclude(slug=slug_product)[0:5] #loại bỏ sản phẩm đang chọn, lấy 5 sản phẩm đầu

    category = product.category
    # prefetch subcategories vì nav trong base.html duyệt category.subcategories
    categories = Category.objects.prefetch_related('subcategories')

    # Lấy danh sách review hiện có của sản phẩm
    reviews = product.reviews.all()
    
    # Danh sách các biến thể
    variants = _product_variants(product)
    
    # Nếu không có variant_slug, tự động chọn biến thể có giá hiệu lực thấp nhất.
    if variant_slug:
        active_variant = get_object_or_404(variants, slug=variant_slug)
    else:
        active_variant = variants.first()
            
    context = {
        'product': product,
        'productphotos': productphotos,
        'related_products': related_products,
        
        'category': category,
        'categories': categories,
        
        'reviews': reviews,
        
        'variants': variants,
        'active_variant': active_variant,
    }
    return render(request, 'product_detail.html', context)

@login_required
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart = _get_prefetched_cart(cart)
    paymentmethods = PaymentMethod.objects.all().order_by('id')
    return render(request, 'cart/cart_view.html', {
        'cart': cart,
        'paymentmethods': paymentmethods,
    })

@login_required
def add_to_cart_simple(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        cart, created = Cart.objects.get_or_create(user=request.user)

        # Tìm ProductVariant có price_sale hoặc price thấp nhất
        cheapest_variant = _product_variants(product).first()

        if not cheapest_variant:
            response = JsonResponse({"error": "Không tìm thấy biến thể hợp lệ."}, status=400)
            response["HX-Trigger"] = json.dumps({"showMessage": {"message": "Sản phẩm không có biến thể hợp lệ.", "type": "bg-danger"}})
            return response

        # Kiểm tra nếu biến thể đã có trong giỏ hàng
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, variant=cheapest_variant)

        if not created:
            # Nếu đã có trong giỏ hàng, tăng số lượng
            cart_item.quantity += 1
            cart_item.save()

        # Render lại giỏ hàng và gửi thông báo thành công
        response = render(request, 'cart/cart_update.html', {'cart': _get_prefetched_cart(cart)})
        response["HX-Trigger"] = json.dumps({"showMessage": {"message": "Sản phẩm đã được thêm vào giỏ hàng.", "type": "bg-success"}})
        return response

    return redirect('product:cart_view')

@login_required
def add_to_cart_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        cart, created = Cart.objects.get_or_create(user=request.user)

        variant_id = request.POST.get('variant_id')
        # print('variant_id:', variant_id)

        # Kiểm tra xem người dùng đã chọn biến thể chưa
        if not variant_id:
            response = JsonResponse({"error": "Vui lòng chọn một biến thể sản phẩm."}, status=400)
            response["HX-Trigger"] = json.dumps({
                "showMessage": {"message": "Vui lòng chọn một biến thể sản phẩm.", "type": "bg-danger"}
            })
            return response

        # Lấy biến thể sản phẩm được chọn
        active_variant = get_object_or_404(ProductVariant, id=variant_id, product=product)

        # Kiểm tra xem biến thể đã có trong giỏ hàng chưa
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product, variant=active_variant
        )

        if not created:
            cart_item.quantity += 1
            cart_item.save()

        # Tạo thông báo thành công
        response = render(request, 'cart/cart_update.html', {'cart': _get_prefetched_cart(cart)})
        response["HX-Trigger"] = json.dumps({
            "showMessage": {"message": "Sản phẩm đã được thêm vào giỏ hàng.", "type": "bg-success"}
        })
        return response

    if product.category:  # category có thể null nên phải kiểm tra trước khi lấy slug
        return redirect('product:product_detail', slug_category=product.category.slug, slug_product=product.slug)
    return redirect('product:product_all')

@login_required
def remove_from_cart(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=request.user)

    if request.method == 'POST':
        cart_item.delete()  # Xóa sản phẩm khỏi giỏ hàng
        cart = cart_item.cart # Render lại giỏ hàng với số lượng mới
        
        if request.headers.get('HX-Request'):
            return render(request, 'cart/cart_update.html', {'cart': _get_prefetched_cart(cart)})

    return redirect('product:cart_view')

@login_required
def update_cart_item(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=request.user)

    if request.method == 'POST':
        new_quantity = int(request.POST.get('quantity', 1))  # Lấy số lượng mới từ form

        if new_quantity <= 0:
            return remove_from_cart(request, cart_item_id)

        # Cập nhật số lượng
        cart_item.quantity = new_quantity
        cart_item.save()

        # Render lại giỏ hàng với số lượng mới
        cart = cart_item.cart
        
        if request.headers.get('HX-Request'):
            return render(request, 'cart/cart_update.html', {'cart': _get_prefetched_cart(cart)})

    return redirect('product:cart_view')

@login_required
def decrease_cart_item(request, cart_item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=request.user)

        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
            
        # Render lại giỏ hàng với số lượng mới
        cart = cart_item.cart
            
        if request.headers.get('HX-Request'):
            return render(request, 'cart/cart_update.html', {'cart': _get_prefetched_cart(cart)})

    return redirect('product:cart_view')

@login_required
def increase_cart_item(request, cart_item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=request.user)
        cart_item.quantity += 1
        cart_item.save()
        
        # Render lại giỏ hàng với số lượng mới
        cart = cart_item.cart
        
        if request.headers.get('HX-Request'):
            return render(request, 'cart/cart_update.html', {'cart': _get_prefetched_cart(cart)})

    return redirect('product:cart_view')

@login_required
def checkout(request):
    if request.method != 'POST':
        return redirect('product:cart_view')

    cart = getattr(request.user, 'cart', None)
    if not cart or not cart.items.exists():
        # Giỏ hàng trống, chuyển hướng về trang giỏ hàng với thông báo lỗi
        messages.error(request, "Giỏ hàng của bạn đang trống.")
        return redirect('product:cart_view')
    cart = _get_prefetched_cart(cart)
    paymentmethods = PaymentMethod.objects.all().order_by('id')

    if request.method == 'POST':
        # Lấy dữ liệu từ request POST
        fullname = request.POST.get('fullname')
        phone = request.POST.get('phone')
        shipping_address = request.POST.get('shipping_address')
        payment_method = request.POST.get('payment_method')
        selected_paymentmethod = _get_order_paymentmethod(payment_method)

        if payment_method and payment_method.startswith('PM:') and not selected_paymentmethod:
            messages.error(request, "Phương thức thanh toán không hợp lệ.")
            return render(request, 'cart/cart_view.html', {
                'cart': cart,
                'paymentmethods': paymentmethods,
            })

        if fullname and phone and shipping_address and payment_method:
            # Lưu thông tin giao hàng vào Checkout_info
            info, created = Checkout_info.objects.get_or_create(user=request.user)
            info.fullname = fullname
            info.phone = phone
            info.address = shipping_address
            info.save()
            
            # Tạo đơn hàng
            order = Order.objects.create(
                user=request.user,
                shipping_address=shipping_address,
                payment_method=payment_method,
                fullname=fullname,
                phone=phone
            )

            # Tạo các OrderItem từ CartItem
            cart_items = cart.items.all()
            for item in cart_items:
                price_item=item.variant.get_price()
                # if item.product.price_sale:
                #     price_item=item.product.price_sale
                # else:
                #     price_item=item.product.price
                    
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    variant=item.variant,
                    quantity=item.quantity,
                    price=price_item,
                    subtotal=item.quantity*price_item,
                )

            # Tính tổng giá trị đơn hàng
            order.calculate_total()

            # Xóa giỏ hàng
            cart.items.all().delete()
            
            # Thông tin đơn hàng 
            user = request.user.username
            email = request.user.profile.email
            fullname = request.user.checkout_info.fullname
            phone = request.user.checkout_info.phone
            address = request.user.checkout_info.address
            price = order.total_price_vnd()
            domain = request.build_absolute_uri('/')
            
            # Gửi email cho khách hàng 
            url_chitiet_donhang = request.build_absolute_uri(reverse('product:order_detail', args=[order.id]))
            send_templated_mail(
                template_name='order_email_customer',  # Không cần .html ở đây
                from_email=None,
                recipient_list=[email],
                context={
                    'order_id': order.id,
                    'url_chitiet_donhang': url_chitiet_donhang,
                    'site_name': 'PTcom',
                    'user': user,
                    'email': email,
                    'fullname':fullname,
                    'phone': phone,
                    'address': address,
                    'price': price,
                    'date_today': timezone.now().strftime('%d-%m-%Y'),
                },
            )
            
            # Gửi email cho quản lý
            quanly_email = get_user_model().objects.get(username='quanly').email
            url_quanly_donhang = request.build_absolute_uri(reverse('quanly:order_view'))
            message = f'Đơn hàng mới {price}đ'
            # send_mail(
            #     subject = "Thông báo mới từ PTcom",
            #     message = f"Đây là tin nhắn tự động. \n\nUsername: {user} \nPhone: {phone} \nNội dung: {message} \n\nTruy cập {url_quanly_donhang} để xem chi tiết.",
            #     from_email = None,
            #     recipient_list = [quanly_email],
            #     fail_silently = False,
            # )
            
            send_templated_mail(
                template_name='order_email_quanly',  # Không cần .html ở đây
                from_email=None,
                recipient_list=[quanly_email],
                context={
                    'url_quanly_donhang': url_quanly_donhang,
                    'site_name': 'PTcom',
                    'user': user,
                    'email': email,
                    'fullname':fullname,
                    'phone': phone,
                    'address': address,
                    'price': price,
                    'message': message,
                    'date_today': timezone.now().strftime('%d-%m-%Y'),
                },
            )

            

            

            # Tạo thông báo thành công
            messages.success(request, "Đặt hàng thành công!")

            # Chuyển hướng tới trang xác nhận đơn hàng
            return redirect('product:order_success', order_id=order.id)
        else:
            # Nếu thiếu thông tin cần thiết
            messages.error(request, "Vui lòng kiểm tra lại thông tin đã nhập.")

    return render(request, 'cart/cart_view.html', {
        'cart': cart,
        'paymentmethods': paymentmethods,
    })

@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    selected_paymentmethod = _get_order_paymentmethod(order.payment_method)
    paymentmethods = PaymentMethod.objects.all().order_by('id') if order.payment_method == 'BANK' else []
    return render(request, 'cart/order_success.html', {
        'order': order,
        'paymentmethods': paymentmethods,
        'selected_paymentmethod': selected_paymentmethod,
        'payment_method_display': _payment_method_display(order.payment_method, selected_paymentmethod),
    })

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product', 'items__variant__attributes__attribute'),
        id=order_id,
        user=request.user,
    )
    selected_paymentmethod = _get_order_paymentmethod(order.payment_method)
    paymentmethods = PaymentMethod.objects.all().order_by('id') if order.payment_method == 'BANK' else []
    return render(request, 'cart/order_detail.html', {
        'order': order,
        'paymentmethods': paymentmethods,
        'selected_paymentmethod': selected_paymentmethod,
        'payment_method_display': _payment_method_display(order.payment_method, selected_paymentmethod),
    })

def _is_htmx_request(request):
    return request.headers.get('HX-Request') == 'true'

def _wishlist_button_response(request, product, in_wishlist, message, type='bg-success'):
    response = render(request, 'partials/wishlist_button.html', {
        'product': product,
        'in_wishlist': in_wishlist,
    })
    response['HX-Trigger'] = json.dumps({
        'showMessage': {
            'message': message,
            'type': type,
        }
    })
    return response

@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if created:
        # Thông báo rằng sản phẩm đã được thêm vào Wishlist
        message = f"Đã thêm {product.name} vào danh sách yêu thích."
    else:
        message = f"{product.name} đã có trong danh sách yêu thích."
    if _is_htmx_request(request):
        return _wishlist_button_response(request, product, True, message, 'bg-success' if created else 'bg-info')
    if created:
        messages.success(request, message)
    else:
        messages.info(request, message)
    if product.category:  # category có thể null nên phải kiểm tra trước khi lấy slug
        return redirect('product:product_detail', slug_category=product.category.slug, slug_product=product.slug)
    return redirect('product:product_all')

@login_required
def remove_from_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.filter(user=request.user, product=product).delete()
    message = f"Đã bỏ {product.name} khỏi danh sách yêu thích."
    if _is_htmx_request(request):
        return _wishlist_button_response(request, product, False, message, 'bg-success')
    messages.success(request, message)
    return redirect('product:wishlist_view')

@login_required
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product', 'product__category').order_by('-added_at')
    return render(request, 'wishlist.html', {'wishlist_items': wishlist_items})

@login_required
def add_to_compare(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    comparison, created = Compare.objects.get_or_create(user=request.user)
    comparison.products.add(product)
    messages.success(request, f"{product.name} has been added to your comparison list.")
    return redirect('product:product_detail', slug_category=product.category.slug, slug_product=product.slug)

@login_required
def remove_from_compare(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    comparison = get_object_or_404(Compare, user=request.user)
    comparison.products.remove(product)
    messages.success(request, f"{product.name} has been removed from your comparison list.")
    return redirect('compare_view')

@login_required
def compare_view(request):
    comparison = Compare.objects.filter(user=request.user).first()
    return render(request, 'compare.html', {'comparison': comparison})

@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        rating = request.POST.get('rating')
        content = request.POST.get('content')
        review, created = Review.objects.get_or_create(user=request.user, product=product, defaults={'rating': rating, 'content': content})
        if not created:
            # Nếu người dùng đã có review trước đó, cập nhật review
            review.rating = rating
            review.content = content
            review.save()
            messages.success(request, 'Đã cập nhật đánh giá.')
        else:
            messages.success(request, 'Đã thêm đánh giá.')
        return redirect('product:product_detail', slug_category=product.category.slug, slug_product=product.slug)
