import calendar
import json
import logging
import os
import shutil
import zipfile
from collections import defaultdict
from datetime import datetime
from calendar import month_name
from heapq import nlargest, nsmallest
from urllib.parse import urlencode

import pandas as pd
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.contrib.staticfiles import finders
from django.db.models import Avg, Case, Count, F, IntegerField, Max, Min, OuterRef, Q, Subquery, Sum, When
from django.db.models.functions import Coalesce, ExtractDay, ExtractHour, ExtractMonth, ExtractWeekDay, ExtractYear
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from templated_email import send_templated_mail

from App_Account.models import Checkout_info, Profile
from App_Core.constants import LIMIT_PRODUCT_OR_POST, MAX_UPLOAD_SIZE, excluded_usernames
from App_Core.middleware import get_directory_size
from App_Core.model_utils import compress_image
from App_Core.models import Contact, PageView
from App_Post.filters import PostFilter
from App_Post.forms import ContentForm, PostForm, PostPhotoForm, SubSubjectForm, SubjectForm
from App_Post.models import Comment, Post, PostContent, PostPhoto, Reply, SubSubject, Subject
from App_Product.filters import OrderFilter, ProductFilter
from App_Product.forms import (
    AttributeForm,
    CategoryForm,
    OrderForm,
    PaymentMethodForm,
    ProductForm,
    ProductPhotoForm,
    ProductVariantForm,
    SpecificationForm,
    SpecificationForm_2,
    SpecificationForm_3,
    SpecificationForm_4,
    SubCategoryForm,
)
from App_Product.models import (
    Attribute,
    Cart,
    CartItem,
    Category,
    Order,
    OrderItem,
    PaymentMethod,
    Product,
    ProductPhoto,
    ProductSpecification,
    ProductSpecification_2,
    ProductSpecification_3,
    ProductSpecification_4,
    ProductVariant,
    Review,
    SubCategory,
    VariantAttribute,
)
from App_Quanly.models import QuanlyMenuConfig

logger = logging.getLogger(__name__)

from .decorators import quanly_required


def generate_response(message, type='bg-success'):
    return HttpResponse(
        status=204,
        headers={
            'HX-Trigger': json.dumps({
                'listChange': None,
                'showMessage': {'message': message, 'type': type}
            })
        }
    )


############################################## App quanly ##############################################    
def round_price(number):
    if number < 1000:
        return round(number, -2)
    elif number < 10000:
        return round(number, -3)
    elif number < 100000:
        return round(number, -4)
    elif number < 1000000:
        return round(number, -5)
    elif number < 10000000:
        return round(number, -6)
    else:
        return round(number, -7)

def currency_vnd(price):
    try:
        return "{:,.0f}".format(price)
    except:
        return ''
    
# Tạo một Q object để lọc ra các tài khoản cần loại trừ (excluded_usernames đã chuyển sang constants.py)
excluded_users_filter = ~Q(username__in=excluded_usernames) & ~Q(username__startswith='quanly_') & ~Q(username__startswith='nhanvien_')

from django.db.models.functions import TruncMonth
from collections import defaultdict
from datetime import datetime


@quanly_required
def dashboard(request):
    # /quan-ly/ redirect theo "Trang mặc định"; /quan-ly/thang-nay/ luôn vào thẳng dashboard.
    if request.resolver_match and request.resolver_match.url_name == 'dashboard':
        config = QuanlyMenuConfig.load()
        if config.default_page != 'dashboard':
            return redirect(config.default_page_url_name)

    # nếu muốn thêm chức năng lọc theo năm
    # if year is None:
    #     current_year = timezone.now().year
    # else:
    #     current_year = int(year)

    # if category:
    #         orders = orders.filter(category=category)

    # current_year = timezone.now().year
    # orders = Order.objects.filter(created_at__year=current_year)
    
    # Lấy tháng, năm hiện tại
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    orders = Order.objects.filter(created_at__year=current_year,
                                created_at__month=current_month)
    
    # orders = Order.objects.all()
    orderitems = OrderItem.objects.filter(order__in=orders)
    
    ############# Card #############
    aggregate = orders.aggregate(tong_doanhso=Sum('total_price'),
                                 tong_donhang=Count('id'))
    
    tong_doanhso = currency_vnd(aggregate['tong_doanhso'])
    tong_donhang = currency_vnd(aggregate['tong_donhang'])
    tong_khachhang = orders.values('user').distinct().count() # Đếm số lượng khách hàng duy nhất đã mua hàng trong tháng này

    ############# Area chart: giờ #############
    lst_hours = list(range(24))
    group_hour_revenue = orders.annotate(hour=ExtractHour("created_at")) \
                                .values("hour") \
                                .annotate(revenue=Sum("total_price")) \
                                .order_by("hour")
    hour_revenue_dict = {entry["hour"]: entry["revenue"] for entry in group_hour_revenue}
    lst_rev_hours = [hour_revenue_dict.get(hour, 0) for hour in lst_hours]

    ############# Area chart: thứ #############
    lst_weekday = ['Chủ Nhật', 'Thứ Hai', 'Thứ Ba', 'Thứ Tư', 'Thứ Năm', 'Thứ Sáu', 'Thứ Bảy']
    group_weekday_revenue = orders.annotate(weekday=ExtractWeekDay("created_at")) \
                                .values("weekday") \
                                .annotate(revenue=Sum("total_price")) \
                                .order_by("weekday")
    weekday_revenue_dict = {entry["weekday"]: entry["revenue"] for entry in group_weekday_revenue}
    lst_rev_weekday = [weekday_revenue_dict.get(index + 1, 0) for index in range(7)]  # index từ 0 đến 6

    ############# Area chart: ngày #############
    lst_days = list(range(1, 32))
    group_day_revenue = orders.annotate(day=ExtractDay("created_at")) \
                                .values("day") \
                                .annotate(revenue=Sum("total_price")) \
                                .order_by("day")
    day_revenue_dict = {entry["day"]: entry["revenue"] for entry in group_day_revenue}
    lst_rev_days = [day_revenue_dict.get(day, 0) for day in lst_days]

    context = {
        'orders': orders,
        'orderitems':orderitems,
        
        'tong_doanhso':tong_doanhso,
        'tong_donhang':tong_donhang,
        'tong_khachhang':tong_khachhang,
        
        'lst_days':lst_days,
        'lst_rev_days':lst_rev_days,
        
        'lst_hours':lst_hours,
        'lst_rev_hours':lst_rev_hours,

        'lst_weekday':lst_weekday,
        'lst_rev_weekday':lst_rev_weekday,
    }
    return render(request, 'quanly/dashboard.html', context)    

@quanly_required
def fulltime(request):    
    orders = Order.objects.all()
    orderitems = OrderItem.objects.filter(order__in=orders)
    
    ############# Card #############
    aggregate = orders.aggregate(tong_doanhso=Sum('total_price'),
                                 tong_donhang=Count('id'))
    
    tong_doanhso = currency_vnd(aggregate['tong_doanhso'])
    tong_donhang = currency_vnd(aggregate['tong_donhang'])
    tong_khachhang = Order.objects.values('user').distinct().count()
    tong_taikhoan = User.objects.filter(excluded_users_filter).count()

    ########################## Combo chart: doanh số, số lượng, khách hàng theo tháng ##########################
    # Tạo danh sách các tháng
    lst_month = list(range(1, 13))

    # Tính doanh thu, số lượng sản phẩm và số lượng khách hàng theo từng tháng
    group_month_data = OrderItem.objects.annotate(month=ExtractMonth("order__created_at")) \
                                        .values("month") \
                                        .annotate(
                                            revenue=Sum("subtotal"),
                                            total_quantity=Sum("quantity"),
                                            customer_count=Count("order__user", distinct=True),
                                            order_count=Count("order__id", distinct=True),
                                        ) \
                                        .order_by("month")
    
    # Khởi tạo dictionary mặc định
    month_data_dict = defaultdict(lambda: {'revenue': 0, 'total_quantity': 0, 'customer_count': 0, 'order_count': 0})
    
    # Điền dữ liệu vào dictionary
    for entry in group_month_data:
        month_data_dict[entry["month"]] = {
            'revenue': entry["revenue"],
            'total_quantity': entry["total_quantity"],
            'customer_count': entry["customer_count"],
            'order_count': entry["order_count"],
        }

    # Tạo danh sách dữ liệu cho từng tháng
    lst_rev_month = [month_data_dict[month]['revenue'] for month in lst_month]
    lst_qty_month = [month_data_dict[month]['total_quantity'] for month in lst_month]
    lst_cust_month = [month_data_dict[month]['customer_count'] for month in lst_month]
    lst_order_month = [month_data_dict[month]['order_count'] for month in lst_month]

    ########################## Donut chart ##########################
    # Lấy tất cả các category
    categories = Category.objects.all()

    # Tính doanh số tổng cho từng category
    doanhthu_category = []
    for category in categories:
        # Lọc các OrderItem theo category của product
        total_revenue = OrderItem.objects.filter(product__category=category).aggregate(total_revenue=Sum('subtotal'))['total_revenue'] or 0
        # Thêm thông tin doanh số vào danh sách doanhthu_category
        doanhthu_category.append({'name': category.name, 'value': total_revenue})
    
    ########################## Bar chart: top 5 sản phẩm ##########################
    group_product = orderitems.exclude(product__name__isnull=True)\
                                .values('product__name')\
                                .annotate(total_subtotal=Sum('subtotal'))\
                                .order_by('product__name')\
                                        
    # Chỉ lấy ra top 5 sản phẩm có doanh thu cao nhất
    top_products = nlargest(5, group_product, key=lambda x: x['total_subtotal'])

    lst_product = []
    lst_rev_product = []
    for i in top_products:
        lst_product.append(i['product__name'])
        lst_rev_product.append(i['total_subtotal'])
            
    ########################## Column chart: top 5 khách hàng ##########################
    group_customer = orderitems.values('order__user__username')\
                                .annotate(total_subtotal=Sum('subtotal'))\
                                .order_by('order__user__username')        
    # Chỉ lấy ra top 5 khách hàng có doanh thu cao nhất
    top_customer = nlargest(5, group_customer, key=lambda x: x['total_subtotal'])

    lst_customer = []
    lst_rev_customer = []
    for i in top_customer:
        lst_customer.append(i['order__user__username'])
        lst_rev_customer.append(i['total_subtotal'])
        
        
    ########################## Table: bottom 8 sản phẩm doanh thu và số lượng thấp ##########################
    # Tính tổng doanh thu và tổng số lượng theo sản phẩm
    group_product_data = OrderItem.objects.values('product__name')\
                                        .annotate(total_subtotal=Sum('subtotal'), total_quantity=Sum('quantity'))\
                                        .order_by('product__name')

    # Lấy ra danh sách tất cả sản phẩm, kể cả những sản phẩm không có doanh thu (tương đương doanh thu bằng 0)
    all_products = Product.objects.all().values('name')
    all_product_data = []
    for product in all_products:
        product_name = product['name']
        product_data = next((item for item in group_product_data if item['product__name'] == product_name), None)
        if product_data is None:
            all_product_data.append({'product__name': product_name, 'total_subtotal': 0, 'total_quantity': 0})
        else:
            all_product_data.append(product_data)

    # Chỉ lấy ra top 8 sản phẩm có doanh thu thấp nhất
    bottom_revenue_products = nsmallest(8, all_product_data, key=lambda x: x['total_subtotal'])

    # Tạo danh sách tên sản phẩm, tổng doanh thu và tổng số lượng của 8 sản phẩm có doanh thu thấp nhất
    lst_product_bottom = [item['product__name'] for item in bottom_revenue_products]
    lst_rev_total_bottom = [item['total_subtotal'] for item in bottom_revenue_products]
    lst_qty_total_bottom = [item['total_quantity'] for item in bottom_revenue_products]
    
    context = {
        'orders': orders,
        'orderitems':orderitems,
        
        'tong_doanhso':tong_doanhso,
        'tong_donhang':tong_donhang,
        'tong_taikhoan':tong_taikhoan,
        'tong_khachhang':tong_khachhang,
        
        'doanhthu_category':doanhthu_category,

        'lst_product':lst_product,
        'lst_rev_product':lst_rev_product,
        
        'lst_customer':lst_customer,
        'lst_rev_customer':lst_rev_customer,
                                                                
        'lst_product':lst_product,
        'lst_rev_product':lst_rev_product,
                                                                
        'combined_list': zip(lst_product_bottom, lst_qty_total_bottom, lst_rev_total_bottom),
            
        'months': lst_month,
        'total_revenue': lst_rev_month,
        'total_quantity': lst_qty_month,
        'customer_count': lst_cust_month,
        'order_count':lst_order_month,
}
    return render(request, 'quanly/fulltime.html', context)    

@quanly_required
def profile_quanly(request):
    profile = Profile.objects.get(user=request.user)
    # Dung lượng toàn bộ Project — quét đĩa tốn thời gian nên cache 10 phút
    uploaded_size = cache.get('project_dir_size')
    if uploaded_size is None:
        uploaded_size = get_directory_size(settings.BASE_DIR)
        cache.set('project_dir_size', uploaded_size, 600)
    
    if request.method == 'POST':
        user = request.user
        user.email = request.POST.get('email')
        user.save()
        
        profile.fullname = request.POST.get('fullname')
        profile.phone = request.POST.get('phone')
        profile.address = request.POST.get('address')
        if request.POST.get('birthday'):
            profile.birthday = request.POST.get('birthday')
        else:
            profile.birthday = None
        profile.gender = request.POST.get('gender')
        profile.email = request.POST.get('email')
        profile.note = request.POST.get('note')
        if 'image' in request.FILES:
            profile.image = request.FILES['image']
        # if 'qr-code' in request.FILES:
        #     profile.qr_code = request.FILES['qr-code']
        profile.request = request
        profile.save()
        messages.success(request, "Cập nhật Thông tin tài khoản.")
        return redirect('quanly:profile_quanly')

    return render(request, 'quanly/profile_quanly.html', {'profile':profile,
                                                                    'uploaded_size': uploaded_size,
                                                                    'max_upload_size': MAX_UPLOAD_SIZE,
                                                                    'Limit_Product_Or_Post': LIMIT_PRODUCT_OR_POST,
                                                                    'product_count': Product.objects.count(),
                                                                    'post_count': Post.objects.count(),
                                                                    })





############# Product #############
@login_required
def product_view(request):        
    return render(request, 'quanly/product_view.html', {})

@login_required
def productvariant_view(request):
    return render(request, 'quanly/productvariant_view.html', {})

@quanly_required
def product_list(request):
    # Lấy ra query string từ request
    query_params = request.GET.copy()

    # Remove the 'page' parameter from query_params to avoid duplication
    query_params.pop('page', None)

    # Lấy danh sách sản phẩm
    products = Product.objects.all()
    
    # Số lượng sản phẩm trước khi lọc
    total_products = products.count()

    # Lấy tiêu chí sắp xếp từ query string
    sort_by = request.GET.get('sort_by', '-id')  # Mặc định là sắp xếp theo id (sản phẩm mới nhất)
    
    # Kiểm tra nếu có "price_sale", sắp xếp theo "price_sale", nếu không có thì sắp xếp theo "price"
    if sort_by == 'price_asc':
        products = products.order_by(Coalesce('price_sale', 'price').asc())
    elif sort_by == 'price_desc':
        products = products.order_by(Coalesce('price_sale', 'price').desc())
    elif sort_by == 'name_asc':
        products = products.order_by('name')
    elif sort_by == 'name_desc':
        products = products.order_by('-name')
    elif sort_by == 'newest':
        products = products.order_by('-id')  # Sản phẩm mới nhất
    elif sort_by == 'oldest':
        products = products.order_by('id')  # Sản phẩm cũ nhất
    else:
        products = products.order_by('category__name', 'subcategory__name', 'name')  # Mặc định

    # Apply filtering
    product_filter = ProductFilter(query_params, queryset=products)
    form = product_filter.form
    products = product_filter.qs

    # Số lượng sản phẩm sau khi lọc
    filtered_products_count = products.count()

    # Pagination
    paginator = Paginator(products, 10)  # Show 10 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    elided_page_range = paginator.get_elided_page_range(number=page_obj.number, on_each_side=2, on_ends=1)

    # Create query string for filters, excluding 'page'
    filtered_query_params = urlencode(query_params)

    context = {
        'total_products': total_products,  # Tổng số sản phẩm
        'filtered_products_count': filtered_products_count,  # Số sản phẩm sau khi lọc

        'form': form,
        'page_obj_product': page_obj,
        'elided_page_range': elided_page_range,
        'filtered_query_params': filtered_query_params,

        'URL_name': reverse('quanly:product_list'),
        'target_container_id': '#product-list-container',
    }

    if request.headers.get('HX-Request'):
        return render(request, 'quanly/product_list.html', context)
    return render(request, 'quanly/product_list.html', context)

@quanly_required
def add_product(request):
    if request.method == 'POST':
        # Làm sạch request.POST để loại bỏ dấu phẩy
        cleaned_data = request.POST.copy()
        if 'price' in cleaned_data:
            cleaned_data['price'] = cleaned_data['price'].replace(',', '')
        if 'price_sale' in cleaned_data:
            cleaned_data['price_sale'] = cleaned_data['price_sale'].replace(',', '')

        # product_form = ProductForm(request.POST, request.FILES)
        product_form = ProductForm(cleaned_data, request.FILES)
        photo_form = ProductPhotoForm(request.POST, request.FILES)
    
        if product_form.is_valid() and photo_form.is_valid():
            product = product_form.save(commit=False)
            product.request = request  # Pass the request object to the model instance, để thực hiện hàm user_directory_path_product
            # product.user = request.user
            product.save()            

            for f in request.FILES.getlist('photo'):
                photo = ProductPhoto(product=product, photo=f)
                photo.request = request  # Pass the request object to each ProductPhoto instance
                photo.save()

            # return HttpResponse('upload multi thành công')
            return generate_response(f"Đã thêm {product.name}.")
        
        else:
            # Lấy lỗi từ form
            errors = product_form.errors.as_data()
            if 'name' in errors:
                return generate_response('Tên sản phẩm này đã tồn tại.', type='bg-danger')
            elif '__all__' in errors:
                return generate_response(f'Số lượng Sản Phẩm không được vượt quá {LIMIT_PRODUCT_OR_POST}.', type='bg-danger')
            return generate_response('Có lỗi xảy ra khi thêm sản phẩm.', type='bg-danger')

    else:
        product_form = ProductForm()
        photo_form = ProductPhotoForm()
        return render(request, 'quanly/product_form.html', {'product_form': product_form, 
                                                                        'photo_form': photo_form,})

@quanly_required
def delete_product(request, id):
    if request.method == 'POST':
        current_product = Product.objects.get(id=id)
        current_product.delete()
        return generate_response(f"Đã xóa {current_product.name}.")

@quanly_required
def edit_product(request, id):
    current_product = Product.objects.get(id=id)
    
    if request.method == 'POST':
        # Làm sạch request.POST để loại bỏ dấu phẩy
        cleaned_data = request.POST.copy()
        if 'price' in cleaned_data:
            cleaned_data['price'] = cleaned_data['price'].replace(',', '')
        if 'price_sale' in cleaned_data:
            cleaned_data['price_sale'] = cleaned_data['price_sale'].replace(',', '')

        product_form = ProductForm(cleaned_data, request.FILES, instance=current_product)
        photo_form = ProductPhotoForm(request.POST, request.FILES, instance=current_product)
        
        if product_form.is_valid() and photo_form.is_valid():
            product = product_form.save(commit=False)
            product.request = request  # Pass the request object to the model instance, để thực hiện hàm user_directory_path_product
            product.save()
            
            if request.FILES.get('photo'):
                ProductPhoto.objects.filter(product=product).delete() # xóa hết những photos hiện có rồi mới tạo những photos mới
                for f in request.FILES.getlist('photo'):
                    photo = ProductPhoto(product=product, photo=f)
                    photo.request = request  # Pass the request object to each ProductPhoto instance
                    photo.save()

            return generate_response(f"Cập nhật {product.name}.")
        
        else:
            # Lấy lỗi từ form
            errors = product_form.errors.as_data()
            if 'name' in errors:
                return generate_response('Tên sản phẩm này đã tồn tại.', type='bg-danger')
            elif '__all__' in errors:
                return generate_response(f'Số lượng Sản Phẩm không được vượt quá {LIMIT_PRODUCT_OR_POST}.', type='bg-danger')
            return generate_response('Có lỗi xảy ra khi cập nhật sản phẩm.', type='bg-danger')

    else:
        product_form = ProductForm(instance=current_product)
        photo_form = ProductPhotoForm(instance=current_product)
        return render(request, 'quanly/product_form.html', {'current_product':current_product,
                                                                    'product_form':product_form,
                                                                    'photo_form': photo_form})



############# Sản phẩm nhiều thuộc tính #############
############# ProductVariant
@quanly_required
def productvariant_list(request):
    productvariants = ProductVariant.objects.select_related('product', 'product__category').prefetch_related('attributes__attribute').all().order_by('name')

    paginator = Paginator(productvariants, 10)  # Show 10 productvariants per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    elided_page_range = paginator.get_elided_page_range(number=page_obj.number, on_each_side=2, on_ends=1)
    
    # Tạo query string rỗng vì productvariant_list không có filter
    filtered_query_params = ''
    
    context = {
        'page_obj_productvariant': page_obj,
        'elided_page_range': elided_page_range,
        'filtered_query_params': filtered_query_params,
        
        'URL_name':reverse('quanly:productvariant_list'),
        'target_container_id': '#productvariant-list-container',
    }
    
    if request.headers.get('HX-Request'):
        return render(request, 'quanly/productvariant_list.html', context)
    return render(request, 'quanly/productvariant_list.html', context)

def _get_variant_attribute_context(current_productvariant=None):
    attributes = Attribute.objects.all().order_by('key', 'value')
    grouped_attributes = {}
    for attribute in attributes:
        grouped_attributes.setdefault(attribute.key, []).append(attribute)

    selected_attribute_ids = []
    if current_productvariant:
        selected_attribute_ids = list(
            current_productvariant.attributes.values_list('attribute_id', flat=True)
        )

    return {
        'grouped_attributes': grouped_attributes,
        'selected_attribute_ids': selected_attribute_ids,
    }

def _get_submitted_attribute_ids(request):
    return [
        int(attribute_id)
        for attribute_id in request.POST.getlist('selected_attributes')
        if str(attribute_id).isdigit()
    ]

def _save_variant_attributes(request, productvariant):
    selected_attribute_ids = set(_get_submitted_attribute_ids(request))

    new_attribute_keys = request.POST.getlist('new_attribute_key')
    new_attribute_values = request.POST.getlist('new_attribute_value')
    for key, value in zip(new_attribute_keys, new_attribute_values):
        key = key.strip()
        value = value.strip()
        if not key or not value:
            continue

        attribute, _ = Attribute.objects.get_or_create(key=key, value=value)
        selected_attribute_ids.add(attribute.id)

    selected_attribute_ids = set(
        Attribute.objects.filter(id__in=selected_attribute_ids).values_list('id', flat=True)
    )
    VariantAttribute.objects.filter(variant=productvariant).exclude(attribute_id__in=selected_attribute_ids).delete()
    for attribute_id in selected_attribute_ids:
        VariantAttribute.objects.get_or_create(variant=productvariant, attribute_id=attribute_id)

@quanly_required
def add_productvariant(request):
    if request.method == 'POST':
        # Làm sạch request.POST để loại bỏ dấu phẩy
        cleaned_data = request.POST.copy()
        if 'price' in cleaned_data:
            cleaned_data['price'] = cleaned_data['price'].replace(',', '')
        if 'price_sale' in cleaned_data:
            cleaned_data['price_sale'] = cleaned_data['price_sale'].replace(',', '')

        variant_form = ProductVariantForm(cleaned_data, request.FILES)
        
        if variant_form.is_valid():
            productvariant = variant_form.save(commit=False)
            productvariant.request = request  # Pass the request object to the model instance, để thực hiện hàm user_directory_path_productvariant
            productvariant.save()
            _save_variant_attributes(request, productvariant)
                
            return generate_response(f"Đã thêm {productvariant.name}.")
    else:
        variant_form = ProductVariantForm()
    
    context = {'variant_form': variant_form}
    context.update(_get_variant_attribute_context())
    if request.method == 'POST':
        context['selected_attribute_ids'] = _get_submitted_attribute_ids(request)
    return render(request, 'quanly/productvariant_form.html', context)

@quanly_required
def delete_productvariant(request, id):
    if request.method == 'POST':
        current_productvariant = get_object_or_404(ProductVariant, id=id)
        current_productvariant.delete()
        return generate_response(f"Đã xóa {current_productvariant.name}.")
    
@quanly_required
def edit_productvariant(request, id):
    current_productvariant = get_object_or_404(ProductVariant, id=id)

    if request.method == 'POST':
        # Làm sạch request.POST để loại bỏ dấu phẩy
        cleaned_data = request.POST.copy()
        if 'price' in cleaned_data:
            cleaned_data['price'] = cleaned_data['price'].replace(',', '')
        if 'price_sale' in cleaned_data:
            cleaned_data['price_sale'] = cleaned_data['price_sale'].replace(',', '')

        variant_form = ProductVariantForm(cleaned_data, request.FILES, instance=current_productvariant)

        if variant_form.is_valid():
            productvariant = variant_form.save(commit=False)
            productvariant.request = request  # Pass the request object to the model instance, để thực hiện hàm user_directory_path_productvariant
            productvariant.save()
            _save_variant_attributes(request, productvariant)
            return generate_response(f"Cập nhật {current_productvariant.name}.")
    else:
        variant_form = ProductVariantForm(instance=current_productvariant)
        
    context = {
        'current_productvariant': current_productvariant,
        'variant_form': variant_form,
    }
    context.update(_get_variant_attribute_context(current_productvariant))
    if request.method == 'POST':
        context['selected_attribute_ids'] = _get_submitted_attribute_ids(request)
    return render(request, 'quanly/productvariant_form.html', context)

############# VariantAttribute


############# Attribute
def attribute_list(request):
    attributes = Attribute.objects.all()
    
    # Sắp xếp dữ liệu
    sorted_attributes = sorted(attributes, key=lambda x: (x.key, str(float(x.value)) if x.value.replace('.', '', 1).isdigit() else x.value))
    
    paginator = Paginator(sorted_attributes, 10)  # Show 10 attributes per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    elided_page_range = paginator.get_elided_page_range(number=page_obj.number, on_each_side=2, on_ends=1)
    attributes_on_page = list(page_obj.object_list)
    split_index = (len(attributes_on_page) + 1) // 2
    
    # Tạo query string rỗng vì attribute_list không có filter
    filtered_query_params = ''
    
    context = {
        'page_obj_attribute': page_obj,
        'attribute_columns': [
            attributes_on_page[:split_index],
            attributes_on_page[split_index:],
        ],
        'elided_page_range': elided_page_range,
        'filtered_query_params': filtered_query_params,
        
        'URL_name':reverse('quanly:attribute_list'),
        'target_container_id': '#attribute-list-container',
    }
    
    if request.headers.get('HX-Request'):
        return render(request, 'quanly/attribute_list.html', context)
    return render(request, 'quanly/attribute_list.html', context)

def add_attribute(request):
    if request.method == 'POST':
        attribute_form = AttributeForm(request.POST, request.FILES)

        if attribute_form.is_valid():
            attribute = attribute_form.save(commit=False)
            attribute.request = request
            attribute.save()
            return generate_response(f"Đã thêm {attribute.key}.")

    else:
        attribute_form = AttributeForm()
        return render(request, 'quanly/attribute_form.html', {'attribute_form': attribute_form,})

def delete_attribute(request, id):
    if request.method == 'POST':
        current_attribute = Attribute.objects.get(id=id)
        current_attribute.delete()
        return generate_response(f"Đã xóa {current_attribute.key}.")

def edit_attribute(request, id):
    current_attribute = Attribute.objects.get(id=id)
    
    if request.method == 'POST':
        attribute_form = AttributeForm(request.POST, request.FILES, instance=current_attribute)
        if attribute_form.is_valid():
            attribute = attribute_form.save(commit=False)
            attribute.request = request
            attribute.save()
            return generate_response(f"Cập nhật {attribute.key}.")
    
    else:
        attribute_form = AttributeForm(instance=current_attribute)
        return render(request, 'quanly/attribute_form.html', {'current_attribute':current_attribute,
                                                                            'attribute_form':attribute_form,})

############# Import Excel
# def process_product_images(request, product, image_folder):
#     """
#     Xử lý ảnh từ folder và lưu vào sản phẩm.
    
#     - Ảnh đầu tiên dùng làm `Image` (ảnh đại diện).
#     - Các ảnh còn lại lưu vào `Photo` (ảnh thư viện).
#     """
#     image_folder = os.path.join(settings.BASE_DIR, image_folder.lstrip("./"))
    
#     if not os.path.exists(image_folder) or not os.path.isdir(image_folder):
#         print(f"⚠️ Folder {image_folder} không tồn tại hoặc không hợp lệ.")
#         return generate_response(f"⚠️ Folder {image_folder} không tồn tại hoặc không hợp lệ.", 'bg-danger')

#     # Lấy danh sách file ảnh (lọc file có định dạng hợp lệ)product
#     valid_extensions = (".jpg", ".jpeg", ".png", ".webp")
#     image_files = [f for f in os.listdir(image_folder) if f.lower().endswith(valid_extensions)]
    
#     if not image_files:
#         print(f"⚠️ Không tìm thấy ảnh trong {image_folder}")
#         return generate_response(f"⚠️ Không tìm thấy ảnh trong {image_folder}", 'bg-danger')
        
#     # Xử lý ảnh đại diện
#     main_image_path = os.path.join(image_folder, image_files[0])
#     with open(main_image_path, "rb") as f:
#         # product.image.save(image_files[0], File(f), save=True)  # Lưu vào model
#         product.image = File(f)
#         product.save()
    
#     # Xóa các ảnh thư viện cũ
#     ProductPhoto.objects.filter(product=product).delete()

#     # Xử lý ảnh thư viện mới
#     for img_file in image_files[1:]:
#         img_path = os.path.join(image_folder, img_file)
#         with open(img_path, "rb") as f:
#             photo = ProductPhoto(product=product, photo=File(f))  # Lưu vào model
#             photo.request = request  # Pass the request object to each ProductPhoto instance
#             photo.save()


# def upload_product_excel(request):
#     if request.method == "POST" and request.FILES.get("file"):
#         uploaded_file = request.FILES["file"]

#         # Đảm bảo thư mục tạm tồn tại
#         temp_dir = "temp"
#         os.makedirs(temp_dir, exist_ok=True)

#         # Lưu file tạm thời
#         file_path = os.path.join(temp_dir, uploaded_file.name)
#         with open(file_path, "wb") as f:
#             for chunk in uploaded_file.chunks():
#                 f.write(chunk)

#         # Kiểm tra lại tệp có tồn tại không
#         if not os.path.exists(file_path):
#             return JsonResponse({"error": "Không thể lưu file. Vui lòng thử lại."}, status=400)

#         try:
#             # Đọc file Excel
#             xls = pd.ExcelFile(file_path)

#             # Đọc dữ liệu từ Sheet "Sản phẩm"
#             if "Sản phẩm" in xls.sheet_names:
#                 df_products = pd.read_excel(xls, sheet_name="Sản phẩm")

#                 for _, row in df_products.iterrows():
#                     category_name = row["Danh mục"]
#                     # subcategory_name = row["Danh mục con"]
#                     subcategory_name = row["Danh mục con"] if pd.notna(row["Danh mục con"]) else None
#                     product_name = row["Sản phẩm"]
#                     price = row["Giá"]
#                     price_sale = row["Giá KM"]
#                     stock = row["Tồn kho"]
#                     image_folder = row["Đường dẫn đến folder ảnh sản phẩm"]

#                     # Xử lý danh mục và danh mục con
#                     category, _ = Category.objects.get_or_create(name=category_name)
#                     # subcategory, _ = SubCategory.objects.get_or_create(name=subcategory_name, category=category)
#                     # Chỉ tạo nếu có giá trị
#                     subcategory = None
#                     if subcategory_name:
#                         subcategory, _ = SubCategory.objects.get_or_create(name=str(subcategory_name).strip(), category=category)

#                     # Kiểm tra sản phẩm đã tồn tại chưa
#                     product, created = Product.objects.update_or_create(
#                         name=product_name,
#                         defaults={
#                             "category": category,
#                             "subcategory": subcategory,
#                             "price": price,
#                             "price_sale": price_sale,
#                             "stock": stock,
#                         },
#                     )
#                     product.request = request  # Pass the request object to the model instance, để thực hiện hàm user_directory_path_product

#                     # TODO: Xử lý ảnh từ folder `image_folder`
#                     process_product_images(request, product, image_folder)

#             # Đọc dữ liệu từ Sheet "Biến thể"
#             if "Biến thể" in xls.sheet_names:
#                 df_variants = pd.read_excel(xls, sheet_name="Biến thể")

#                 for _, row in df_variants.iterrows():
#                     product_name = row["Sản phẩm"]
#                     variant_price = row["Giá"]
#                     variant_price_sale = row["Giá KM"]
#                     variant_stock = row["Tồn kho"]
#                     attributes_text = row["Thuộc tính"]

#                     product = Product.objects.filter(name=product_name).first()
#                     if product:
#                         # variant, _ = ProductVariant.objects.update_or_create(
#                         #     product=product,
#                         #     defaults={"price": variant_price, "price_sale": variant_price_sale, "stock": variant_stock},
#                         # )
                        
#                         # # Xử lý thuộc tính
#                         # attributes_list = attributes_text.split(",") if pd.notna(attributes_text) else []
#                         # for attr in attributes_list:
#                         #     key, value = attr.split(":") if ":" in attr else (attr, "")
#                         #     attribute, _ = Attribute.objects.get_or_create(key=key.strip(), value=value.strip())
#                         #     VariantAttribute.objects.get_or_create(variant=variant, attribute=attribute)
                                                
#                         # Lấy tất cả biến thể của sản phẩm
#                         existing_variants = ProductVariant.objects.filter(product=product)

#                         # Chuyển đổi chuỗi thuộc tính thành danh sách (key-value)
#                         attributes_dict = {}
#                         attributes_list = attributes_text.split(",") if pd.notna(attributes_text) else []
#                         for attr in attributes_list:
#                             if ":" in attr:
#                                 key, value = attr.split(":")
#                                 attributes_dict[key.strip()] = value.strip()

#                         # Kiểm tra xem có biến thể nào trùng thuộc tính không
#                         variant = None
#                         for existing_variant in existing_variants:
#                             existing_attrs = {va.attribute.key: va.attribute.value for va in VariantAttribute.objects.filter(variant=existing_variant)}
                            
#                             if existing_attrs == attributes_dict:
#                                 variant = existing_variant
#                                 break

#                         # Nếu tìm thấy biến thể phù hợp → Cập nhật
#                         if variant:
#                             variant.price = variant_price
#                             variant.price_sale = variant_price_sale if pd.notna(variant_price_sale) else None
#                             variant.stock = variant_stock
#                             variant.save()
#                         else:
#                             # Nếu không tìm thấy → Tạo mới
#                             variant = ProductVariant.objects.create(
#                                 product=product,
#                                 price=variant_price,
#                                 price_sale=variant_price_sale if pd.notna(variant_price_sale) else None,
#                                 stock=variant_stock,
#                             )
                            
#                         # Cập nhật thuộc tính biến thể
#                         VariantAttribute.objects.filter(variant=variant).delete()  # Xóa cũ
#                         for key, value in attributes_dict.items():
#                             attribute, _ = Attribute.objects.get_or_create(key=key, value=value)
#                             VariantAttribute.objects.create(variant=variant, attribute=attribute)
                            
#             # return redirect("quanly:product_view")  # Chuyển hướng đến trang quản lý sản phẩm
#             return generate_response(f"Đã thêm.")

#         except Exception as e:
#             # return JsonResponse({"error": f"Lỗi khi xử lý file: {str(e)}"}, status=400)
#             print(f"⚠️ Lỗi khi xử lý file: {str(e)}")
#             return generate_response(f"Lỗi khi xử lý file: {str(e)}", 'bg-danger')

#         finally:
#             # Xóa file sau khi xử lý
#             if os.path.exists(file_path):
#                 os.remove(file_path)

#     # return JsonResponse({"error": "Không có file được tải lên."}, status=400)
#     print("⚠️ Không có file được tải lên.")
#     return generate_response("Không có file được tải lên.", 'bg-danger')




def cleanup_files(zip_path, extract_dir):
    """ Xóa file ZIP và thư mục extracted sau khi xử lý """
    if os.path.exists(zip_path):
        os.remove(zip_path)  # Xóa file ZIP
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)  # Xóa toàn bộ thư mục extracted

def extract_zip(file_path, extract_to):
    """ Giải nén file zip vào thư mục đích """
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        return True
    except zipfile.BadZipFile:
        return False

@quanly_required
def download_sample_product_zip(request):
    from django.http import FileResponse
    file_path = finders.find('quanly/products.zip')
    if not file_path or not os.path.exists(file_path):
        return HttpResponse("File không tồn tại", status=404)
    response = FileResponse(open(file_path, 'rb'), as_attachment=True, filename='products.zip')
    return response

@quanly_required
def upload_product_zip(request):
    if request.method == "POST":
        if "file" not in request.FILES:
            logger.warning("Product import upload missing file")
            return JsonResponse({"error": "Không có file được tải lên."}, status=400)

        uploaded_file = request.FILES["file"]
        logger.info("Product import file received: %s", uploaded_file.name)

        if not uploaded_file.name.endswith(".zip"):
            logger.warning("Product import rejected non-zip file: %s", uploaded_file.name)
            return JsonResponse({"error": "Chỉ chấp nhận file .zip."}, status=400)

        temp_dir = os.path.join(settings.BASE_DIR, "temp")
        os.makedirs(temp_dir, exist_ok=True)

        zip_path = os.path.join(temp_dir, uploaded_file.name)
        with open(zip_path, "wb") as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)

        logger.info("Product import zip saved: %s", zip_path)

        extract_dir = os.path.join(temp_dir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)

        if not extract_zip(zip_path, extract_dir):
            logger.warning("Product import zip invalid or extraction failed: %s", zip_path)
            return JsonResponse({"error": "File zip không hợp lệ hoặc bị lỗi."}, status=400)

        logger.info("Product import extracted files: %s", os.listdir(extract_dir))

        excel_path = os.path.join(extract_dir, "excel_import_san_pham.xlsx")
        if not os.path.exists(excel_path):
            logger.warning("Product import Excel file missing: %s", excel_path)
            return JsonResponse({"error": "Không tìm thấy file excel_import_san_pham.xlsx."}, status=400)

        logger.info("Product import Excel file found, processing started")
        # return process_product_excel(excel_path, extract_dir, request)
        # Xử lý file Excel
        response = process_product_excel(excel_path, extract_dir, request)

        # Dọn dẹp sau khi xử lý xong
        cleanup_files(zip_path, extract_dir)

        return response

    return JsonResponse({"error": "Yêu cầu không hợp lệ."}, status=400)

def process_product_excel(excel_path, extract_dir, request):
    try:
        logger.info("Reading product import Excel file: %s", excel_path)
        xls = pd.ExcelFile(excel_path)
        logger.info("Product import sheets: %s", xls.sheet_names)

        if "Sản phẩm" not in xls.sheet_names:
            logger.warning("Product import missing 'Sản phẩm' sheet")
            return JsonResponse({"error": "File Excel không chứa sheet 'Sản phẩm'."}, status=400)

        df_products = pd.read_excel(xls, sheet_name="Sản phẩm")
        logger.info("Product import row count: %s", len(df_products))

        if "Sản phẩm" not in df_products.columns:
            return JsonResponse({"error": "Sheet 'Sản phẩm' thiếu cột 'Sản phẩm'."}, status=400)

        import_product_names = []
        for raw_name in df_products["Sản phẩm"]:
            if pd.isna(raw_name):
                continue
            product_name = str(raw_name).strip()
            if product_name:
                import_product_names.append(product_name)

        existing_product_names = set(
            Product.objects.filter(name__in=import_product_names).values_list('name', flat=True)
        )
        new_product_count = len(set(import_product_names) - existing_product_names)
        current_product_count = Product.objects.count()

        if current_product_count + new_product_count > LIMIT_PRODUCT_OR_POST:
            return generate_response(
                f'Số lượng Sản Phẩm không được vượt quá {LIMIT_PRODUCT_OR_POST}. '
                f'Hiện có {current_product_count}, file import có {new_product_count} sản phẩm mới.',
                type='bg-danger',
            )

        for _, row in df_products.iterrows():
            logger.debug("Processing product import row: %s", row.to_dict())
            category_name = row["Danh mục"]
            subcategory_name = row["Danh mục con"] if pd.notna(row["Danh mục con"]) else None
            product_name = str(row["Sản phẩm"]).strip() if pd.notna(row["Sản phẩm"]) else ""
            price = row.get("Giá", None)
            price_sale = row.get("Giá KM", None)
            if pd.isna(price_sale):
                price_sale = None
            stock = row.get("Tồn kho", None)
            if pd.isna(stock):
                stock = None
            image_folder = str(row.get("Đường dẫn đến folder ảnh sản phẩm", "")).strip()

            if not product_name:
                logger.warning("Skipping product import row without product name")
                continue

            category, _ = Category.objects.get_or_create(name=category_name)
            subcategory = None
            if subcategory_name:
                subcategory, _ = SubCategory.objects.get_or_create(name=subcategory_name, category=category)

            product, _ = Product.objects.update_or_create(
                name=product_name,
                defaults={
                    "category": category,
                    "subcategory": subcategory,
                    "price": price,
                    "price_sale": price_sale,
                    "stock": stock,
                },
            )
            product.request = request  # Pass the request object to the model instance, để thực hiện hàm user_directory_path_product

            logger.info("Product import upserted product: %s", product_name)

            process_product_images(request, product, os.path.join(extract_dir, image_folder))

        # return JsonResponse({"success": "Dữ liệu đã được cập nhật."})
        return generate_response(f"Dữ liệu đã được cập nhật.")

    except Exception as e:
        logger.exception("Product import Excel processing error")
        return JsonResponse({"error": f"Lỗi khi xử lý file: {str(e)}"}, status=400)

def process_product_images(request, product, image_folder):
    """ Xử lý ảnh từ folder và lưu vào sản phẩm """
    valid_extensions = (".jpg", ".jpeg", ".png", ".webp")
    if not os.path.exists(image_folder):
        return
    
    image_files = [f for f in os.listdir(image_folder) if f.lower().endswith(valid_extensions)]
    if not image_files:
        return
    
    # Ảnh đại diện
    main_image_path = os.path.join(image_folder, image_files[0])
    with open(main_image_path, "rb") as f:
        product.image = File(f)
        product.save()
    
    # Xóa ảnh cũ và thêm ảnh mới vào thư viện
    ProductPhoto.objects.filter(product=product).delete()
    for img_file in image_files[1:]:
        img_path = os.path.join(image_folder, img_file)
        with open(img_path, "rb") as f:
            # ProductPhoto.objects.create(product=product, photo=File(f))
            photo = ProductPhoto(product=product, photo=File(f))  # Lưu vào model
            photo.request = request  # Pass the request object to each ProductPhoto instance
            photo.save()






############# Specification #############
@quanly_required
def edit_specification(request, id):
    current_product = get_object_or_404(Product, id=id)
    current_specification = get_object_or_404(ProductSpecification, product=current_product)
    current_specification_2 = get_object_or_404(ProductSpecification_2, product=current_product)
    current_specification_3 = get_object_or_404(ProductSpecification_3, product=current_product)
    current_specification_4 = get_object_or_404(ProductSpecification_4, product=current_product)

    if request.method == 'POST':
        form = SpecificationForm(request.POST, request.FILES, instance=current_specification)

        if form.is_valid():
            form.save()
            messages.success(request, f"Cập nhật {current_product.name}.")
            return redirect('quanly:product_view')

    else:
        form = SpecificationForm(instance=current_specification)
        form_2 = SpecificationForm_2(instance=current_specification_2)
        form_3 = SpecificationForm_3(instance=current_specification_3)
        form_4 = SpecificationForm_4(instance=current_specification_4)
    
    return render(request, 'quanly/specification_form.html', { 'current_product':current_product,
                                                                        'form': form,
                                                                        'form_2': form_2,
                                                                        'form_3': form_3,
                                                                        'form_4': form_4, })

# def edit_specification_2(request, id):
#     current_product = get_object_or_404(Product, id=id)
#     current_specification_2 = get_object_or_404(ProductSpecification_2, product=current_product)

#     if request.method == 'POST':
#         form_2 = SpecificationForm_2(request.POST, request.FILES, instance=current_specification_2)

#         if form_2.is_valid():
#             form_2.save()
#             messages.success(request, f"Cập nhật {current_product.name}.")
#             return redirect('quanly:product_view')

#     else:
#         form_2 = SpecificationForm_2(instance=current_specification_2)
    
#     return render(request, 'quanly/specification_form.html', {'form_2': form_2,})


def edit_specification_generic(request, id, model, form_class, template_name='quanly/specification_form.html'):
    current_product = get_object_or_404(Product, id=id)
    current_specification = get_object_or_404(model, product=current_product)

    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=current_specification)

        if form.is_valid():
            form.save()
            messages.success(request, f"Cập nhật {current_product.name}.")
            return redirect('quanly:product_view')

    else:
        form = form_class(instance=current_specification)
    
    return render(request, template_name, {'form': form})

def edit_specification_2(request, id):
    return edit_specification_generic(request, id, ProductSpecification_2, SpecificationForm_2)

def edit_specification_3(request, id):
    return edit_specification_generic(request, id, ProductSpecification_3, SpecificationForm_3)

def edit_specification_4(request, id):
    return edit_specification_generic(request, id, ProductSpecification_4, SpecificationForm_4)







############# Category #############
@quanly_required
def category_view(request):
    # Annotate categories with the count of products
    categories = Category.objects.annotate(product_count=Count('products'))

    # Prepare the data for the chart
    chart_data = [{'value': category.product_count, 'name': category.name} for category in categories]    

    return render(request, 'quanly/category_view.html', {'chart_data': json.dumps(chart_data),})

@quanly_required
def category_list(request):
    categories = Category.objects.all().order_by('name')
    
    paginator = Paginator(categories, 10)  # Show 10 categories per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    elided_page_range = paginator.get_elided_page_range(number=page_obj.number, on_each_side=2, on_ends=1)
    
    # Tạo query string rỗng vì category_list không có filter
    filtered_query_params = ''
    
    context = {
        'page_obj_category': page_obj,
        'elided_page_range': elided_page_range,
        'filtered_query_params': filtered_query_params,
        
        'URL_name':reverse('quanly:category_list'),
        'target_container_id': '#category-list-container',
    }
    
    if request.headers.get('HX-Request'):
        return render(request, 'quanly/category_list.html', context)
    return render(request, 'quanly/category_list.html', context)

@quanly_required
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            category = form.save(commit=False)
            category.request = request  # Pass the request object to the model instance, để thực hiện hàm user_directory_path_category
            category.save()
            return generate_response(f"Đã thêm {category.name}.")
    else:
        form = CategoryForm()
    
    return render(request, 'quanly/category_form.html', {'form': form,})

@quanly_required
def delete_category(request, id):
    if request.method == 'POST':
        current_category = get_object_or_404(Category, id=id)
        current_category.delete()
        return generate_response(f"Đã xóa {current_category.name}.")
  
@quanly_required
def edit_category(request, id):
    current_category = get_object_or_404(Category, id=id)

    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=current_category)

        if form.is_valid():
            category = form.save(commit=False)
            category.request = request  # Pass the request object to the model instance, để thực hiện hàm user_directory_path_category
            category.save()
            return generate_response(f"Cập nhật {current_category.name}.")
    else:
        form = CategoryForm(instance=current_category)
        
    return render(request, 'quanly/category_form.html', {'current_category':current_category,
                                                                  'form': form,})



############# SubCategory #############
@quanly_required
def subcategory_view(request):
    pass

@quanly_required
def subcategory_list(request):
    subcategories = SubCategory.objects.all().order_by('category__name', 'name')
    
    paginator = Paginator(subcategories, 10)  # Show 10 subcategories per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    elided_page_range = paginator.get_elided_page_range(number=page_obj.number, on_each_side=2, on_ends=1)
    
    # Tạo query string rỗng vì subcategory_list không có filter
    filtered_query_params = ''
    
    context = {
        'page_obj_subcategory': page_obj,
        'elided_page_range': elided_page_range,
        'filtered_query_params': filtered_query_params,
        
        'URL_name':reverse('quanly:subcategory_list'),
        'target_container_id': '#subcategory-list-container',
    }

    if request.headers.get('HX-Request'):
        return render(request, 'quanly/subcategory_list.html', context)
    return render(request, 'quanly/subcategory_list.html', context)

@quanly_required
def add_subcategory(request):
    if request.method == 'POST':
        subcategory_form = SubCategoryForm(request.POST, request.FILES)

        if subcategory_form.is_valid():
            subcategory = subcategory_form.save(commit=False)
            # subcategory.user = request.user
            subcategory.request = request
            subcategory.save()
            return generate_response(f"Đã thêm {subcategory.name}.")

    else:
        subcategory_form = SubCategoryForm()
        return render(request, 'quanly/subcategory_form.html', {'subcategory_form': subcategory_form,})

@quanly_required
def delete_subcategory(request, id):
    if request.method == 'POST':
        current_subcategory = SubCategory.objects.get(id=id)
        current_subcategory.delete()
        return generate_response(f"Đã xóa {current_subcategory.name}.")

@quanly_required
def edit_subcategory(request, id):
    current_subcategory = SubCategory.objects.get(id=id)

    if request.method == 'POST':
        subcategory_form = SubCategoryForm(request.POST, request.FILES, instance=current_subcategory)
        if subcategory_form.is_valid():
            subcategory = subcategory_form.save(commit=False)
            # subcategory.user = request.user
            subcategory.request = request
            subcategory.save()
            return generate_response(f"Cập nhật {subcategory.name}.")
    
    else:
        subcategory_form = SubCategoryForm(instance=current_subcategory)
        return render(request, 'quanly/subcategory_form.html', {'current_subcategory':current_subcategory,
                                                                                    'subcategory_form':subcategory_form,})

@quanly_required
def get_subcategories(request):
    category_id = request.GET.get('category_id')
    subcategories = SubCategory.objects.filter(category_id=category_id).order_by('name')
    return JsonResponse(list(subcategories.values('id', 'name')), safe=False)


############# Order #############
@quanly_required
def order_view(request):
    Order.objects.filter(is_read=False).update(is_read=True)

    # Lấy ra query string từ request
    query_params = request.GET.copy()
    
    orders = Order.objects.all().order_by('-id')
    orderitems = OrderItem.objects.all()
    
    # số lượng đơn hàng cho mỗi người dùng
    order_counts = Order.objects.values('user').annotate(order_count=Count('user'))
    
    # Lọc queryset sử dụng query string
    order_filter = OrderFilter(query_params, queryset=orders)
    form = order_filter.form
    orders = order_filter.qs
        
    # Tạo query string mới với các tham số lọc
    filtered_query_params = query_params.urlencode()
    
    users = User.objects.filter(excluded_users_filter)

    return render(request, 'quanly/order_view.html', {'form': form,
                                                                'orders':orders,
                                                                'orderitems':orderitems,
                                                                'order_counts':order_counts,
                                                                'filtered_query_params': filtered_query_params,
                                                                
                                                                'users':users,})
    
@quanly_required
def order_list(request):
    # Lấy ra query string từ request
    query_params = request.GET.copy()
    
    # Remove the 'page' parameter from query_params to avoid duplication
    query_params.pop('page', None)

    orders = Order.objects.all().order_by('-id')
    orderitems = OrderItem.objects.all()
    
    # Số lượng sản phẩm trước khi lọc
    total_orders = orders.count()
    
    # số lượng đơn hàng cho mỗi người dùng
    order_counts = Order.objects.values('user').annotate(order_count=Count('user'))
    
    # Lọc queryset sử dụng query string
    order_filter = OrderFilter(query_params, queryset=orders)
    form = order_filter.form
    orders = order_filter.qs
    
    # Số lượng sản phẩm sau khi lọc
    filtered_orders_count = orders.count()
    
    # Implement pagination
    paginator = Paginator(orders, 10)  # Show 10 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    elided_page_range = paginator.get_elided_page_range(number=page_obj.number, on_each_side=2, on_ends=1)

    # Create query string for filters, excluding 'page'
    filtered_query_params = urlencode(query_params)
    
    users_with_unreceived_orders = set(orders.filter(status_order="Đã huỷ").values_list('user__username', flat=True))
    
    context = {
        'total_orders': total_orders,  # Tổng số sản phẩm
        'filtered_orders_count': filtered_orders_count,  # Số sản phẩm sau khi lọc
        
        'form': form,
        'page_obj': page_obj,
        'elided_page_range': elided_page_range,
        'filtered_query_params': filtered_query_params,
        
        'orders':orders,
        'orderitems':orderitems,
        'order_counts':order_counts,
        'users_with_unreceived_orders':users_with_unreceived_orders,
        
        'URL_name':reverse('quanly:order_list'),
        'target_container_id': '#order-list-container',
    }
        
    if request.headers.get('HX-Request'):
        return render(request, 'quanly/order_list.html', context)
    return render(request, 'quanly/order_list.html', context)
    
@quanly_required
def add_order(request):
    pass

@quanly_required
def delete_order(request, id):
    if request.method == 'POST':
        current_order = get_object_or_404(Order, id=id)
        current_order.delete()
        return generate_response(f"Đã xóa đơn hàng {current_order.id}.")
  
@quanly_required
def edit_order(request, id):
    current_order = get_object_or_404(Order, id=id)
    
    if request.method == 'POST':
        form = OrderForm(request.POST, request.FILES, instance=current_order)

        if form.is_valid():
            form.save()
            return generate_response(f"Cập nhật đơn hàng {current_order.id}.")
        
    else:
        form = OrderForm(instance=current_order)

    return render(request, 'quanly/order_form.html', {'current_order':current_order,
                                                                'form': form,})

############# Customer, Review, Comment #############
@quanly_required
def customer_view(request):
    return render(request, 'quanly/customer_view.html', {})

@quanly_required
def customer_list(request):
    users = User.objects.filter(excluded_users_filter).order_by('-id')
    # users = User.objects.all()
    
    # Lấy danh sách tên người dùng có đơn hàng với status_order == "Đã huỷ"
    users_with_unreceived_orders = set(Order.objects.filter(status_order="Đã huỷ").values_list('user__username', flat=True))
    
    paginator = Paginator(users, 10)  # Show 10 subcategories per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    elided_page_range = paginator.get_elided_page_range(number=page_obj.number, on_each_side=2, on_ends=1)
    
    # Tạo query string rỗng vì customer_list không có filter
    filtered_query_params = ''

    context = {
        'users':users,
        'users_with_unreceived_orders': users_with_unreceived_orders,
        
        'page_obj': page_obj,
        'elided_page_range': elided_page_range,
        'filtered_query_params': filtered_query_params,
        
        'URL_name':reverse('quanly:customer_list'),
        'target_container_id': '#customer-list-container',
    }

    if request.headers.get('HX-Request'):
        return render(request, 'quanly/customer_list.html', context)
    return render(request, 'quanly/customer_list.html', context)

@quanly_required
def review_view(request):
    return render(request, 'quanly/review_view.html', {})

@quanly_required
def review_list(request):
    reviews = Review.objects.all().order_by('-id')
    
    paginator = Paginator(reviews, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    elided_page_range = paginator.get_elided_page_range(number=page_obj.number, on_each_side=2, on_ends=1)
    
    # Tạo query string rỗng vì review_list không có filter
    filtered_query_params = ''

    context = {
        'reviews':reviews,
        
        'page_obj': page_obj,
        'elided_page_range': elided_page_range,
        'filtered_query_params': filtered_query_params,
        
        'URL_name':reverse('quanly:review_list'),
        'target_container_id': '#review-list-container',
    }

    if request.headers.get('HX-Request'):
        return render(request, 'quanly/review_list.html', context)
    return render(request, 'quanly/review_list.html', context)

@quanly_required
def delete_review(request, id):    
    current_review = get_object_or_404(Review, id=id)
    
    if request.method == 'POST':
        current_review.delete()
        return generate_response(f"Đã xóa đánh giá {current_review}.")
    
    return render(request, 'quanly/review_form.html', {'current_review':current_review,})

@quanly_required
def comment_view(request):
    Comment.objects.filter(is_read=False).update(is_read=True)
    return render(request, 'quanly/comment_view.html', {})

@quanly_required
def comment_list(request):
    Comment.objects.filter(is_read=False).update(is_read=True)
    comments = Comment.objects.all().order_by('-id')
    
    paginator = Paginator(comments, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    elided_page_range = paginator.get_elided_page_range(number=page_obj.number, on_each_side=2, on_ends=1)
    
    # Tạo query string rỗng vì comment_list không có filter
    filtered_query_params = ''

    context = {
        'comments':comments,
        
        'page_obj': page_obj,
        'elided_page_range': elided_page_range,
        'filtered_query_params': filtered_query_params,
        
        'URL_name':reverse('quanly:comment_list'),
        'target_container_id': '#comment-list-container',
    }

    if request.headers.get('HX-Request'):
        return render(request, 'quanly/comment_list.html', context)
    return render(request, 'quanly/comment_list.html', context)

@quanly_required
def delete_comment(request, id):
    current_comment = get_object_or_404(Comment, id=id)
    
    if request.method == 'POST':
        current_comment.delete()
        return generate_response(f"Đã xóa bình luận {current_comment}.")
    
    return render(request, 'quanly/comment_form.html', {'current_comment':current_comment,})

############# Post #############
@quanly_required
def post_view(request):
    posts = Post.objects.all().order_by('-id')
        
    # Lọc queryset sử dụng query string
    # post_filter = postFilter(request.GET, queryset=posts)
    # form = post_filter.form
    # posts = post_filter.qs
        
    return render(request, 'quanly/post_view.html', {
        # 'form': form,                                                        
        'posts':posts,
        })

@quanly_required
def post_list(request):
    # Lấy ra query string từ request
    query_params = request.GET.copy()
    query_params.pop('page', None)  # Remove the 'page' parameter to avoid duplication

    # Lấy queryset ban đầu
    posts = Post.objects.all()

    # Số lượng sản phẩm trước khi lọc
    total_posts = posts.count()

    # Áp dụng bộ lọc
    post_filter = PostFilter(query_params, queryset=posts)
    form = post_filter.form
    posts = post_filter.qs

    # Số lượng bài viết sau khi lọc
    filtered_posts_count = posts.count()

    # Sắp xếp mặc định: bài viết mới nhất
    posts = posts.order_by('-id')

    # Phân trang
    paginator = Paginator(posts, 10)  # Hiển thị 10 bài viết mỗi trang
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    elided_page_range = paginator.get_elided_page_range(number=page_obj.number, on_each_side=2, on_ends=1)

    # Tạo query string cho các bộ lọc, loại bỏ 'page'
    filtered_query_params = urlencode(query_params)

    context = {
        'form': form,
        'page_obj': page_obj,
        'elided_page_range': elided_page_range,
        'filtered_query_params': filtered_query_params,
        'filtered_posts_count': filtered_posts_count,
        'total_posts': total_posts,
        'URL_name': reverse('quanly:post_list'),
        'target_container_id': '#post-list-container',
    }

    if request.headers.get('HX-Request'):
        return render(request, 'quanly/post_list.html', context)
    return render(request, 'quanly/post_list.html', context)


@quanly_required
def add_post(request):
    if request.method == 'POST':
        post_form = PostForm(request.POST, request.FILES)
        photo_form = PostPhotoForm(request.POST, request.FILES)

        if post_form.is_valid() and photo_form.is_valid():
            post = post_form.save(commit=False)
            post.request = request  # Pass the request object to the model instance, để thực hiện hàm user_directory_path_post
            # post.user = request.user
            post.save()

            for f in request.FILES.getlist('photo'):
                photo = PostPhoto(post=post, photo=f)
                photo.request = request  # Pass the request object to each ProductPhoto instance
                photo.save()

            # return HttpResponse('upload multi thành công')
            return generate_response(f"Đã thêm {post.title}.")
        else:
            # Lấy lỗi từ form
            errors = post_form.errors.as_data()
            if 'title' in errors:
                return generate_response('Tiêu đề này đã tồn tại.', type='bg-danger')
            elif '__all__' in errors:
                return generate_response(f'Số lượng Bài Viết không được vượt quá {LIMIT_PRODUCT_OR_POST}.', type='bg-danger')
            return generate_response('Có lỗi xảy ra khi thêm bài viết.', type='bg-danger')

    else:
        post_form = PostForm()
        photo_form = PostPhotoForm()
        return render(request, 'quanly/post_form.html', {'post_form': post_form,
                                                                    'photo_form': photo_form,
                                                                    })

@quanly_required
def delete_post(request, id):
    if request.method == 'POST':
        current_post = get_object_or_404(Post, id=id)
        current_post.delete()
        return generate_response(f"Đã xóa {current_post.title}.")
    
@quanly_required
def edit_post(request, id):
    current_post = Post.objects.get(id=id)

    if request.method == 'POST':
        post_form = PostForm(request.POST, request.FILES, instance=current_post)
        photo_form = PostPhotoForm(request.POST, request.FILES, instance=current_post)
        
        if post_form.is_valid() and photo_form.is_valid():
            post = post_form.save(commit=False)
            post.request = request  # Pass the request object to the model instance, để thực hiện hàm user_directory_path_product
            post.save()

            if request.FILES.get('photo'):
                PostPhoto.objects.filter(post=post).delete() # xóa hết những photos hiện có rồi mới tạo những photos mới
                for f in request.FILES.getlist('photo'):
                    photo = PostPhoto(post=post, photo=f)
                    photo.request = request  # Pass the request object to each ProductPhoto instance
                    photo.save()

            return generate_response(f"Cập nhật {post.title}.")
        else:
            # Lấy lỗi từ form
            errors = post_form.errors.as_data()
            if 'title' in errors:
                return generate_response('Tiêu đề này đã tồn tại.', type='bg-danger')
            elif '__all__' in errors:
                return generate_response(f'Số lượng Bài Viết không được vượt quá {LIMIT_PRODUCT_OR_POST}.', type='bg-danger')
            return generate_response('Có lỗi xảy ra khi cập nhật bài viết.', type='bg-danger')
    
    else:
        post_form = PostForm(instance=current_post)
        photo_form = PostPhotoForm(instance=current_post)
        return render(request, 'quanly/post_form.html', {'current_post':current_post,
                                                                    'post_form':post_form,
                                                                    'photo_form': photo_form,
                                                                    })

@quanly_required
def edit_content(request, id):
    current_post = get_object_or_404(Post, id=id)
    current_content = get_object_or_404(PostContent, post=current_post)

    if request.method == 'POST':
        form = ContentForm(request.POST, request.FILES, instance=current_content)

        if form.is_valid():
            form.save()
            messages.success(request, (f"Cập nhật {current_post.title}."))
            return redirect('quanly:post_view')

    else:
        form = ContentForm(instance=current_content)
    
    return render(request, 'quanly/content_form.html', {'current_post':current_post,
                                                                'current_content': current_content,
                                                                'form': form,})


############# Subject #############
@quanly_required
def subject_view(request):
    # Annotate subjects with the count of posts
    subjects = Subject.objects.annotate(post_count=Count('posts'))

    # Prepare the data for the chart
    chart_data = [{'value': subject.post_count, 'name': subject.title} for subject in subjects]    

    return render(request, 'quanly/subject_view.html', {'chart_data': json.dumps(chart_data),})

@quanly_required
def subject_list(request):
    subjects = Subject.objects.all().order_by('title')
    
    paginator = Paginator(subjects, 10)  # Show 10 subjects per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    elided_page_range = paginator.get_elided_page_range(number=page_obj.number, on_each_side=2, on_ends=1)
    
    # Tạo query string rỗng vì subject_list không có filter
    filtered_query_params = ''
    
    context = {
        'page_obj_subject': page_obj,
        'elided_page_range': elided_page_range,
        'filtered_query_params': filtered_query_params,
        
        'URL_name':reverse('quanly:subject_list'),
        'target_container_id': '#subject-list-container',
    }
    
    if request.headers.get('HX-Request'):
        return render(request, 'quanly/subject_list.html', context)
    return render(request, 'quanly/subject_list.html', context)

@quanly_required
def add_subject(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST, request.FILES)

        if form.is_valid():
            subject = form.save(commit=False)
            subject.request = request  # Pass the request object to the model instance, để thực hiện hàm user_directory_path_subject
            subject.save()
            return generate_response(f"Đã thêm {subject.title}.")
    else:
        form = SubjectForm()
        
    return render(request, 'quanly/subject_form.html', {'form': form,})

@quanly_required
def delete_subject(request, id):
    if request.method == 'POST':
        current_subject = get_object_or_404(Subject, id=id)
        current_subject.delete()
        return generate_response(f"Đã xóa {current_subject.title}.")

@quanly_required
def edit_subject(request, id):
    current_subject = get_object_or_404(Subject, id=id)

    if request.method == 'POST':
        form = SubjectForm(request.POST, request.FILES, instance=current_subject)

        if form.is_valid():
            subject = form.save(commit=False)
            subject.request = request  # Pass the request object to the model instance, để thực hiện hàm user_directory_path_subject
            subject.save()
            return generate_response(f"Cập nhật {current_subject.title}.")

    else:
        form = SubjectForm(instance=current_subject)
    
    return render(request, 'quanly/subject_form.html', {'current_subject': current_subject,
                                                                'form': form,})


############# SubSubject #############
@quanly_required
def subsubject_view(request):
    pass

@quanly_required
def subsubject_list(request):
    subsubjects = SubSubject.objects.all().order_by('subject__title', 'title')
    
    paginator = Paginator(subsubjects, 10)  # Show 10 subsubjects per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    elided_page_range = paginator.get_elided_page_range(number=page_obj.number, on_each_side=2, on_ends=1)
    
    # Tạo query string rỗng vì subsubject_list không có filter
    filtered_query_params = ''
    
    context = {
        'page_obj_subsubject': page_obj,
        'elided_page_range': elided_page_range,
        'filtered_query_params': filtered_query_params,
        
        'URL_name':reverse('quanly:subsubject_list'),
        'target_container_id': '#subsubject-list-container',
    }

    if request.headers.get('HX-Request'):
        return render(request, 'quanly/subsubject_list.html', context)
    return render(request, 'quanly/subsubject_list.html', context)


@quanly_required
def add_subsubject(request):
    if request.method == 'POST':
        subsubject_form = SubSubjectForm(request.POST, request.FILES)

        if subsubject_form.is_valid():
            subsubject = subsubject_form.save(commit=False)
            # subsubject.user = request.user
            subsubject.request = request
            subsubject.save()
            return generate_response(f"Đã thêm {subsubject.title}.")

    else:
        subsubject_form = SubSubjectForm()
        return render(request, 'quanly/subsubject_form.html', {'subsubject_form': subsubject_form,})

@quanly_required
def delete_subsubject(request, id):
    if request.method == 'POST':
        current_subsubject = SubSubject.objects.get(id=id)
        current_subsubject.delete()
        return generate_response(f"Đã xóa {current_subsubject.title}.")

@quanly_required
def edit_subsubject(request, id):
    current_subsubject = SubSubject.objects.get(id=id)

    if request.method == 'POST':
        subsubject_form = SubSubjectForm(request.POST, request.FILES, instance=current_subsubject)
        if subsubject_form.is_valid():
            subsubject = subsubject_form.save(commit=False)
            subsubject.request = request
            subsubject.save()
            return generate_response(f"Cập nhật {subsubject.title}.")
    
    else:
        subsubject_form = SubSubjectForm(instance=current_subsubject)
        return render(request, 'quanly/subsubject_form.html', {'current_subsubject':current_subsubject,
                                                                                    'subsubject_form':subsubject_form,})

@quanly_required
def get_subsubjects(request):
    subject_id = request.GET.get('subject_id')
    subsubjects = SubSubject.objects.filter(subject_id=subject_id).order_by('title')
    return JsonResponse(list(subsubjects.values('id', 'title')), safe=False)

############# Contact #############
@quanly_required
def contact_view(request):
    Contact.objects.filter(is_read=False).update(is_read=True)

    return render(request, 'quanly/contact_view.html', {})

@quanly_required
def contact_list(request):
    contacts = Contact.objects.all().order_by('-id')
    
    paginator = Paginator(contacts, 10)  # Show 10 contacts per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    elided_page_range = paginator.get_elided_page_range(number=page_obj.number, on_each_side=2, on_ends=1)
    
    # Tạo query string rỗng vì contact_list không có filter
    filtered_query_params = ''
    
    context = {
        'page_obj_contact': page_obj,
        'elided_page_range': elided_page_range,
        'filtered_query_params': filtered_query_params,
        
        'URL_name':reverse('quanly:contact_list'),
        'target_container_id': '#contact-list-container',
    }

    if request.headers.get('HX-Request'):
        return render(request, 'quanly/contact_list.html', context)
    return render(request, 'quanly/contact_list.html', context)

@quanly_required
def delete_contact(request, id):
    current_contact = Contact.objects.get(id=id)
    
    if request.method == 'POST':
        current_contact.delete()
        return generate_response(f"Đã xóa liên hệ {current_contact.name}.")
    
    return render(request, 'quanly/contact_form.html', {'current_contact':current_contact,})


############# email #############
@quanly_required
def email_view(request):
    return render(request, 'quanly/email_view.html', {})

@quanly_required
def email_list(request):
    users = User.objects.filter(excluded_users_filter).order_by('-id')
    contacts = Contact.objects.all().order_by('-id')
    
    # Tạo danh sách users_contacts gồm cả users và contacts, lấy các cột name, phone, email (nếu không có thì để trống)
    users_contacts = []

    # Thêm từ users
    for user in users:
        # Lấy fullname nếu có, nếu fullname rỗng thì lấy username
        if hasattr(user, 'profile'):
            fullname = getattr(user.profile, 'fullname', '')
            name = fullname if fullname else getattr(user, 'username', '')
            phone = getattr(user.profile, 'phone', '')
            birthday = getattr(user.profile, 'birthday', '')
            gender = getattr(user.profile, 'gender', '')
        else:
            name = getattr(user, 'username', '')
            phone = ''
            birthday = ''
            gender = ''
        users_contacts.append({
            'name': name,
            'phone': phone,
            'email': getattr(user, 'email', ''),
            'birthday': birthday,
            'gender': gender,
        })
    # print(f"users: {users}")

    # Thêm từ contacts
    for contact in contacts:
        users_contacts.append({
            'name': getattr(contact, 'name', ''),
            'phone': getattr(contact, 'phone', ''),
            'email': getattr(contact, 'email', ''),
        })
    # print(f"contacts: {contacts}")

    emails = users_contacts
    
    paginator = Paginator(emails, 10)  # Show 10 emails per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    elided_page_range = paginator.get_elided_page_range(number=page_obj.number, on_each_side=2, on_ends=1)
    
    # Tạo query string rỗng vì email_list không có filter
    filtered_query_params = ''
    
    context = {
        'page_obj_email': page_obj,
        'elided_page_range': elided_page_range,
        'filtered_query_params': filtered_query_params,
        
        'URL_name':reverse('quanly:email_list'),
        'target_container_id': '#email-list-container',
    }

    if request.headers.get('HX-Request'):
        return render(request, 'quanly/email_list.html', context)
    return render(request, 'quanly/email_list.html', context)

@quanly_required
def send_marketing_email(request):
    if request.method == "POST":
        subject = request.POST.get("subject", "Khuyến mãi từ PTcom")
        message = request.POST.get("message", "")
        recipient_raw = request.POST.get("recipients", "")
        recipient_list = [email.strip() for email in recipient_raw.split(",") if email.strip()]
        # print(f"recipient_list: {recipient_list}")
        
        if not recipient_list or not message:
            return JsonResponse({"error": "Vui lòng nhập đầy đủ thông tin."}, status=400)

        for email in recipient_list:
            send_templated_mail(
                template_name='marketing_email',  # Không cần .html ở đây
                from_email=None,
                recipient_list=[email],
                context={
                    'site_name': 'PTcom',
                    'subject': subject,
                    # 'name': '',
                    # 'phone': '',
                    'email': email,
                    'message': message,
                    'date_today': timezone.now().strftime('%d-%m-%Y'),
                },
            )
        return generate_response(f"Đã gửi email quảng cáo thành công.")

    return render(request, 'quanly/marketing_email_form.html', {})

############# PaymentMethod #############
def paymentmethod_view(request):
    return render(request, 'quanly/paymentmethod_view.html', {})

def paymentmethod_list(request):
    paymentmethods = PaymentMethod.objects.all().order_by('-id')
    
    paginator = Paginator(paymentmethods, 10)  # Show 10 paymentmethods per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    elided_page_range = paginator.get_elided_page_range(number=page_obj.number, on_each_side=2, on_ends=1)
    
    # Tạo query string rỗng vì paymentmethod_list không có filter
    filtered_query_params = ''
    
    context = {
        'paymentmethods': paymentmethods,
        'page_obj_paymentmethod': page_obj,
        'elided_page_range': elided_page_range,
        'filtered_query_params': filtered_query_params,
        
        'URL_name': reverse('quanly:paymentmethod_list'),
        'target_container_id': '#paymentmethod-list-container',
    }
    
    if request.headers.get('HX-Request'):
        return render(request, 'quanly/paymentmethod_list.html', context)
    return render(request, 'quanly/paymentmethod_list.html', context)

def add_paymentmethod(request):
    if request.method == 'POST':
        paymentmethod_form = PaymentMethodForm(request.POST, request.FILES)

        if paymentmethod_form.is_valid():
            paymentmethod = paymentmethod_form.save(commit=False)
            paymentmethod.user = request.user  # Gán người dùng hiện tại
            paymentmethod.request = request
            paymentmethod.save()
            return generate_response(f"Đã thêm {paymentmethod.name}.")

    else:
        paymentmethod_form = PaymentMethodForm()
        return render(request, 'quanly/paymentmethod_form.html', {'paymentmethod_form': paymentmethod_form,})

def delete_paymentmethod(request, id):
    current_paymentmethod = get_object_or_404(PaymentMethod, id=id)

    if request.method == 'POST':
        current_paymentmethod.delete()
        return generate_response(f"Đã xóa {current_paymentmethod.name}.")

    return render(request, 'quanly/paymentmethod_form.html', {'current_paymentmethod': current_paymentmethod})

def edit_paymentmethod(request, id):
    current_paymentmethod = get_object_or_404(PaymentMethod, id=id)
    
    if request.method == 'POST':
        paymentmethod_form = PaymentMethodForm(request.POST, request.FILES, instance=current_paymentmethod)
        if paymentmethod_form.is_valid():
            paymentmethod = paymentmethod_form.save(commit=False)
            paymentmethod.request = request
            paymentmethod.save()
            return generate_response(f"Cập nhật {paymentmethod.name}.")

    else:
        paymentmethod_form = PaymentMethodForm(instance=current_paymentmethod)

    return render(request, 'quanly/paymentmethod_form.html', {
        'current_paymentmethod': current_paymentmethod,
        'paymentmethod_form': paymentmethod_form,
    })
        
############# View #############
@quanly_required
def view_view(request):
    return render(request, 'quanly/view_view.html', {})

@quanly_required
def view_list(request):
    # Lấy tất cả các trang và số lượt truy cập
    page_views = PageView.objects.all().order_by('-view_count')
    
    paginator = Paginator(page_views, 10)  # Show 10 views per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    elided_page_range = paginator.get_elided_page_range(number=page_obj.number, on_each_side=2, on_ends=1)
    
    # Tạo query string rỗng vì view_list không có filter
    filtered_query_params = ''
    
    context = {
        'page_obj_view': page_obj,
        'elided_page_range': elided_page_range,
        'filtered_query_params': filtered_query_params,
        
        'URL_name':reverse('quanly:view_list'),
        'target_container_id': '#view-list-container',
    }

    if request.headers.get('HX-Request'):
        return render(request, 'quanly/view_list.html', context)
    return render(request, 'quanly/view_list.html', context)
