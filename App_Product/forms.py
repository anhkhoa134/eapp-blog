from django import forms
from django.core.exceptions import ValidationError
from django_ckeditor_5.widgets import CKEditor5Widget

from App_Core.constants import INPUT_ATTRS, IS_PAID, LIMIT_PRODUCT_OR_POST, STATUS_ORDER
from .models import (
    Attribute,
    Category,
    Order,
    PaymentMethod,
    Product,
    ProductPhoto,
    ProductSpecification,
    ProductSpecification_2,
    ProductSpecification_3,
    ProductSpecification_4,
    ProductVariant,
    SubCategory,
    VariantAttribute,
)

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result




class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'image']
        widgets = {'name':forms.TextInput(INPUT_ATTRS),
                    'image':forms.FileInput(INPUT_ATTRS),}
        labels = {
            'name': 'Tên danh mục',
            'image': 'Ảnh'
        }
        
class SubCategoryForm(forms.ModelForm):
    class Meta:
        model = SubCategory
        fields = ['category', 'name', 'image']
        widgets = {
            'category':forms.Select(attrs={'class':'form-select'}), 
            'name':forms.TextInput(INPUT_ATTRS), 
            'image':forms.FileInput(INPUT_ATTRS),
        }
        labels = {
            'category': 'Thuộc danh mục',
            'name': 'Tên danh mục phụ',
            'image': 'Ảnh',
        }
        
class ProductPhotoForm(forms.ModelForm):
    photo = MultipleFileField(required=False, label='Những ảnh phụ')
    class Meta:
        model = ProductPhoto
        fields = ['photo']

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        # viết ở đây cho form cho fields, viết ở widgets là form để render HTML
        # is_stock = forms.BooleanField() #required=True bắt buộc người dùng chọn, dùng cho chính sách điều khoản
        fields = ['category', 'subcategory', 'name' ,'description', 
                  'featured', 
                  'price', 'price_sale', 'stock', 'image',
                  ]
        widgets = {
                    'category': forms.Select(attrs={'class': 'form-control', 'id': 'category', 'data-searchable': 'true'}),
                    'subcategory': forms.Select(attrs={'class': 'form-control', 'id': 'subcategory', 'data-searchable': 'true'}),
                    'name':forms.TextInput(INPUT_ATTRS),
                    'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
                    'featured': forms.Select(choices=[(True, 'Có'), (False, 'Không')], 
                                            attrs={'class': 'form-select'}),
                    'price': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_price'}),
                    'price_sale': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_price_sale'}),
                    'stock': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_stock'}),
                    'image':forms.FileInput(INPUT_ATTRS), # bỏ đi widgets của image này, thì form edit hiển thị đường link của image đang dùng
                    }
        labels = {
            'category': 'Tên danh mục',
            'subcategory': 'Tên danh mục phụ',
            'name': 'Tên sản phẩm',
            'description': 'Mô tả ngắn',
            'featured': 'Nổi bật',
            'price': 'Giá',
            'price_sale': 'Giá khuyến mãi',
            'stock': 'Số lượng tồn',
            'image': 'Ảnh chính',
        }
        
    def clean_price(self):
        price = self.cleaned_data.get('price')
        if isinstance(price, str):  # Kiểm tra xem giá trị có phải là chuỗi không
            price = price.replace(',', '')  # Xóa dấu phẩy
        return int(price) if price else 0  # Trả về giá trị số nguyên

    def clean_price_sale(self):
        price_sale = self.cleaned_data.get('price_sale')
        if isinstance(price_sale, str):  # Kiểm tra xem giá trị có phải là chuỗi không
            price_sale = price_sale.replace(',', '')  # Xóa dấu phẩy
        return int(price_sale) if price_sale else 0  # Trả về giá trị số nguyên

    def clean_stock(self):
        stock = self.cleaned_data.get('stock')
        if isinstance(stock, str):
            stock = stock.replace(',', '')
        stock = int(stock) if stock else 0
        if stock < 0:
            raise ValidationError('Số lượng tồn không được nhỏ hơn 0.')
        return stock
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        # Get the current instance if it exists (for editing)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            # If editing, exclude the current product from the check
            if Product.objects.filter(name=name).exclude(pk=instance.pk).exists():
                raise ValidationError('Tên sản phẩm này đã tồn tại.')
        else:
            # If creating new product
            if Product.objects.filter(name=name).exists():
                raise ValidationError('Tên sản phẩm này đã tồn tại.')
        return name

    def clean(self):
        cleaned_data = super().clean()

        if not self.instance.pk and Product.objects.count() >= LIMIT_PRODUCT_OR_POST:
            raise ValidationError(f'Số lượng Sản Phẩm không được vượt quá {LIMIT_PRODUCT_OR_POST}.')
        return cleaned_data

    def save(self, commit=True):
        product = super().save(commit=False)
        product.is_stock = (product.stock or 0) > 0
        if commit:
            product.save()
            self.save_m2m()
        return product


################ Specification ################
# class SpecificationForm(forms.ModelForm):
# 	class Meta:
# 		model = ProductSpecification
# 		fields = ['specification']
# 		widgets = {'specification':CKEditor5Widget(attrs={'class':'django_ckeditor_5'}), }
# 		labels = {'specification': False,}

# class SpecificationForm_2(forms.ModelForm):
# 	class Meta:
# 		model = ProductSpecification_2
# 		fields = ['specification']
# 		widgets = {'specification':CKEditor5Widget(attrs={"class": "django_ckeditor_5"})}
# 		labels = {'specification': False,}

class BaseSpecificationForm(forms.ModelForm):
    class Meta:
        fields = ['specification']
        widgets = {'specification': CKEditor5Widget(attrs={'class': 'django_ckeditor_5'})}
        labels = {'specification': False}

# Tạo các form kế thừa từ lớp trừu tượng
class SpecificationForm(BaseSpecificationForm):
    class Meta(BaseSpecificationForm.Meta):
        model = ProductSpecification

class SpecificationForm_2(BaseSpecificationForm):
    class Meta(BaseSpecificationForm.Meta):
        model = ProductSpecification_2

# Add more Specification forms as needed
class SpecificationForm_3(BaseSpecificationForm):
    class Meta(BaseSpecificationForm.Meta):
        model = ProductSpecification_3

class SpecificationForm_4(BaseSpecificationForm):
    class Meta(BaseSpecificationForm.Meta):
        model = ProductSpecification_4


########################################## ProductVariant: Sản phẩm nhiều thuộc tính ##########################################
class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['product', 'price', 'price_sale', 'stock']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select', 'data-searchable': 'true'}),
            'price': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_price_var'}),
            'price_sale': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_price_sale_var'}),
            'stock': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_stock_var'}),
        }
        labels = {
            'product': 'Sản phẩm',
            'price': 'Giá',
            'price_sale': 'Giá khuyến mãi',
            'stock': 'Số lượng tồn',
        }
        
    def clean_price(self):
        price = self.cleaned_data.get('price')
        if isinstance(price, str):  # Kiểm tra xem giá trị có phải là chuỗi không
            price = price.replace(',', '')  # Xóa dấu phẩy
        return int(price) if price else 0  # Trả về giá trị số nguyên

    def clean_price_sale(self):
        price_sale = self.cleaned_data.get('price_sale')
        if isinstance(price_sale, str):  # Kiểm tra xem giá trị có phải là chuỗi không
            price_sale = price_sale.replace(',', '')  # Xóa dấu phẩy
        return int(price_sale) if price_sale else 0  # Trả về giá trị số nguyên

    def clean_stock(self):
        stock = self.cleaned_data.get('stock')
        if isinstance(stock, str):
            stock = stock.replace(',', '')
        stock = int(stock) if stock else 0
        if stock < 0:
            raise ValidationError('Số lượng tồn không được nhỏ hơn 0.')
        return stock

class CustomVariantAttributeFormSet(forms.BaseInlineFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)
        if self.can_delete:
            form.fields['DELETE'].label = 'Xoá'  # Thay đổi label của trường DELETE

# Sử dụng FormSet tùy chỉnh
VariantAttributeFormSet = forms.inlineformset_factory(
    ProductVariant, VariantAttribute,
    formset=CustomVariantAttributeFormSet,
    fields=('attribute',),
    extra=5,
    max_num=5,
    can_delete=True,
    widgets={'attribute': forms.Select(attrs={'class': 'form-select form-select-sm'})},
    labels={'attribute': 'Thuộc tính'}
)
       
class AttributeForm(forms.ModelForm):
    class Meta:
        model = Attribute
        fields = ['key', 'value']
        widgets = {'key':forms.TextInput(INPUT_ATTRS),
                    'value':forms.TextInput(INPUT_ATTRS),}
        labels = {
            'key': 'Thuộc tính',
            'value': 'Giá trị',
        }


########################################## Order ##########################################
class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['is_paid', 'status_order', 'note']
        widgets = {
            # 'price_order':forms.TextInput(attrs={'class':'form-control'}),
            'note':forms.TextInput(attrs={'class':'form-control'}),
            'is_paid':forms.Select(choices=IS_PAID, attrs={'class': 'form-select'}),
            'status_order':forms.Select(choices=STATUS_ORDER, attrs={'class': 'form-select'}),
            # 'created_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }   
        labels = {
            'is_paid': 'Trạng thái thanh toán',
            'status_order': 'Trạng thái đơn hàng',
            'note': 'Ghi chú',
        }






class PaymentMethodForm(forms.ModelForm):
    class Meta:
        model = PaymentMethod
        fields = ['name', 'account_name', 'account_number', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phương thức thanh toán'}),
            'account_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Chủ tài khoản'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Số tài khoản'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'placeholder': 'Ảnh'}),
        }
        labels = {
            'name': 'Phương thức thanh toán',
            'account_name': 'Chủ tài khoản',
            'account_number': 'Số tài khoản',
            'image': 'Ảnh',
        }
