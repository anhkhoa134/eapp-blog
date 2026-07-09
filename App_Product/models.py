import os

from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_delete, post_save, pre_delete
from django.dispatch import receiver
from django.urls import reverse
from django.utils.html import mark_safe
from django_ckeditor_5.fields import CKEditor5Field

from App_Core.constants import (
    STATUS_ORDER,
    category_icon_url,
    default_thumbnail_url,
    product_icon_url,
    static_placeholder,
    subcategory_icon_url,
)
from App_Core.model_utils import (
    compress_image,
    create_slug,
    user_directory_path_category,
    user_directory_path_product,
    user_directory_path_productphoto,
    user_directory_path_profile,
    user_directory_path_subcategory,
)

class PaymentMethod(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    name = models.CharField(max_length=100)
    account_name = models.CharField(max_length=255, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    image = models.ImageField(upload_to=user_directory_path_profile, blank=True, null=True)  # QR code for e-wallets, etc.

    class Meta:
        verbose_name_plural = 'PaymentMethod'
        ordering = ('-id', )

    def __str__(self):
        return str(self.user) 
    
    def save(self, *args, **kwargs):
        """Override save để nén ảnh và tạo thumbnail khi lưu"""
        is_new_image = False

        # Kiểm tra trường hợp chỉnh sửa (edit)
        if self.pk:  # Nếu sản phẩm đã tồn tại
            old_instance = PaymentMethod.objects.filter(pk=self.pk).first()
            if old_instance and old_instance.image != self.image: 
                is_new_image = True
                if old_instance.image:  # Xóa ảnh cũ nếu có ảnh mới
                    old_image_path = old_instance.image.path
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
        else:
            # Trường hợp thêm mới, luôn coi ảnh là ảnh mới
            is_new_image = True

        # Nén hình ảnh (image) nếu có ảnh mới
        if self.image and is_new_image:
            self.image = compress_image(self.image, max_width=600, max_height=600)

        super().save(*args, **kwargs)  # Lưu model sau khi xử lý
            
    def get_image(self):
        if self.image:
            return self.image.url
        else:
            # return 'https://via.placeholder.com/240x200.jpg'   
            return static_placeholder
        
    def get_icon(self): # chỉ cần gọi {{product.get_icon}}, ko cần bọc trong tag <img>
        if self.image:
            return mark_safe('<img src="%s" width="35" height="35" style="border-radius: 8px;" />' % (self.image.url))
        else:
            # return mark_safe('<img src="%s" width="35" height="35" style="border-radius: 8px;" />' % ('https://via.placeholder.com/20x20.jpg'))
            return mark_safe('<img src="%s" width="35" height="35" style="border-radius: 8px;" />' % static_placeholder)

@receiver(pre_delete, sender=PaymentMethod)
def payment_pre_delete(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)
    


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    # slug = AutoSlugField(populate_from='name', unique=True)
    slug = models.SlugField(unique=True, blank=True, null=True)
    description = models.TextField(default='', blank=True, null=True)
    # image = models.ImageField(upload_to='categories/', blank=True, null=True)
    image = models.ImageField(upload_to=user_directory_path_category, blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Category'
        ordering = ('-id', )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = create_slug(self.name)
        
        """Override save để nén ảnh và tạo thumbnail khi lưu"""
        is_new_image = False

        # Kiểm tra trường hợp chỉnh sửa (edit)
        if self.pk:  # Nếu sản phẩm đã tồn tại
            old_instance = Category.objects.filter(pk=self.pk).first()
            if old_instance and old_instance.image != self.image: 
                is_new_image = True
                if old_instance.image:  # Xóa ảnh cũ nếu có ảnh mới
                    old_image_path = old_instance.image.path
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
        else:
            # Trường hợp thêm mới, luôn coi ảnh là ảnh mới
            is_new_image = True

        # Nén hình ảnh (image) nếu có ảnh mới
        if self.image and is_new_image:
            self.image = compress_image(self.image, max_width=600, max_height=600)

        super().save(*args, **kwargs)  # Lưu model sau khi xử lý
            
    def get_image(self):
        if self.image:
            return self.image.url
        else:
            # return 'https://via.placeholder.com/240x200.jpg'   
            return default_thumbnail_url
            
    def get_icon(self): # chỉ cần gọi {{product.get_icon}}, ko cần bọc trong tag <img>
        if self.image:
            return mark_safe('<img src="%s" width="35" height="35" style="border-radius: 8px;" />' % (self.image.url))
        else:
            # return mark_safe('<img src="%s" width="35" height="35" style="border-radius: 8px;" />' % ('https://via.placeholder.com/20x20.jpg'))
            return mark_safe('<img src="%s" width="35" height="35" style="border-radius: 8px;" />' % category_icon_url)

    def get_absolute_url(self):
        return reverse('product:product_all', kwargs={'slug_category': self.slug})

@receiver(pre_delete, sender=Category)
def category_pre_delete(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)
        
class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=255, blank=True, null=True)
    slug = models.SlugField(blank=True, null=True)
    description = models.TextField(default='', blank=True, null=True)
    # image = models.ImageField(upload_to='categories/', blank=True, null=True)
    image = models.ImageField(upload_to=user_directory_path_subcategory, blank=True, null=True)

    class Meta:
        verbose_name_plural = 'SubCategory'
        ordering = ('-id', )
        unique_together = ('category', 'name')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = create_slug(self.name)
        
        """Override save để nén ảnh và tạo thumbnail khi lưu"""
        is_new_image = False

        # Kiểm tra trường hợp chỉnh sửa (edit)
        if self.pk:  # Nếu sản phẩm đã tồn tại
            old_instance = SubCategory.objects.filter(pk=self.pk).first()
            if old_instance and old_instance.image != self.image: 
                is_new_image = True
                if old_instance.image:  # Xóa ảnh cũ nếu có ảnh mới
                    old_image_path = old_instance.image.path
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
        else:
            # Trường hợp thêm mới, luôn coi ảnh là ảnh mới
            is_new_image = True

        # Nén hình ảnh (image) nếu có ảnh mới
        if self.image and is_new_image:
            self.image = compress_image(self.image, max_width=600, max_height=600)

        super().save(*args, **kwargs)  # Lưu model sau khi xử lý
            
    def get_image(self):
        if self.image:
            return self.image.url
        else:
            # return 'https://via.placeholder.com/240x200.jpg'   
            return default_thumbnail_url
            
    def get_icon(self): # chỉ cần gọi {{product.get_icon}}, ko cần bọc trong tag <img>
        if self.image:
            return mark_safe('<img src="%s" width="35" height="35" style="border-radius: 8px;" />' % (self.image.url))
        else:
            # return mark_safe('<img src="%s" width="35" height="35" style="border-radius: 8px;" />' % ('https://via.placeholder.com/20x20.jpg'))
              # sử dụng static để lấy đường dẫn tới ảnh tĩnh
            return mark_safe('<img src="%s" width="35" height="35" style="border-radius: 8px;" />' % subcategory_icon_url)

@receiver(pre_delete, sender=SubCategory)
def subcategory_pre_delete(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)

class Product(models.Model):
    # user = models.ForeignKey(User, blank=True, null=True, related_name='products', on_delete=models.CASCADE)
    category = models.ForeignKey(Category, blank=True, null=True, related_name='products', on_delete=models.SET_NULL)
    subcategory = models.ForeignKey(SubCategory, blank=True, null=True, related_name='products', on_delete=models.SET_NULL)
    name = models.CharField(max_length=255, unique=True)
    # slug = AutoSlugField(populate_from='name', unique=True)
    slug = models.SlugField(unique=True, blank=True, null=True)
    description = models.TextField(default='', blank=True, null=True)
    price = models.IntegerField(blank=True, null=True, default=0) #models.DecimalField(max_digits=99999999999999, decimal_places=2, default='1.99')
    price_sale = models.IntegerField(blank=True, null=True, default=0)
    is_stock = models.BooleanField(default=True)
    stock = models.PositiveIntegerField(blank=True, null=True, default=0)
    is_sale = models.BooleanField(default=False)
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # image = models.ImageField(upload_to='products/', blank=True, null=True)
    image = models.ImageField(upload_to=user_directory_path_product, blank=True, null=True)
    thumbnail = models.ImageField(upload_to=user_directory_path_product, blank=True, null=True)
    # sku = ShortUUIDField(unique=True, length=4, max_length=10, prefix='sku', alphabet='1234567890')

    # Attribute product fields 
    # colors = models.ManyToManyField(Color, related_name='products', blank=True)
    # sizes = models.ManyToManyField(Size, related_name='products', blank=True)

    # Filter fields 
    # hashtags = models.ManyToManyField(Hashtag, related_name='products', blank=True)
    # brand = models.ForeignKey(Brand, related_name='products', on_delete=models.SET_NULL, null=True)
    # collection = models.ForeignKey(Collection, related_name='products', on_delete=models.SET_NULL, null=True, blank=True)
    # gender = models.ForeignKey(Gender, related_name='products', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Product'
        ordering = ('-id', )

    def __str__(self):
        return f"{self.name}"

    def save(self, *args, **kwargs):
        self.slug = create_slug(self.name)
        
        """Override save để nén ảnh và tạo thumbnail khi lưu"""
        is_new_image = False
        
        # Kiểm tra trường hợp chỉnh sửa (edit)
        if self.pk:  # Nếu sản phẩm đã tồn tại
            old_instance = Product.objects.filter(pk=self.pk).first()
            if old_instance and old_instance.image != self.image: 
                is_new_image = True
                
                if old_instance.image:  # Xóa ảnh cũ nếu có ảnh mới
                    old_image_path = old_instance.image.path
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                        
                    old_thumbnail_path = old_instance.thumbnail.path
                    if os.path.exists(old_thumbnail_path):
                        os.remove(old_thumbnail_path)
        else:
            # Trường hợp thêm mới, luôn coi ảnh là ảnh mới
            is_new_image = True

        # Nén hình ảnh (image) và thumbnail
        if self.image and is_new_image:
            self.image = compress_image(self.image) # Xử lý ảnh chính
            self.thumbnail = compress_image(self.image, max_width=600, max_height=600) # Xử lý thumbnail

        super().save(*args, **kwargs)  # Lưu model sau khi xử lý
                
    def get_image(self):
        if self.image:
            return self.image.url
        return default_thumbnail_url

    def get_thumbnail(self):
        if self.thumbnail:
            return self.thumbnail.url
        return default_thumbnail_url

            
    def get_icon(self): # chỉ cần gọi {{ product.get_icon }}, ko cần bọc trong tag <img>
        if self.image:
            return mark_safe('<img src="%s" width="35" height="35" style="border-radius: 8px;" />' % (self.image.url))
        else:
            return mark_safe('<img src="%s" width="35" height="35" style="border-radius: 8px;" />' % product_icon_url)

    # def price_display(self):
    #     return self.price/100

    # def price_vnd(self):
    #     if self.price:
    #         return "{:,.0f}".format(self.price)
    #     return ''    
    
    # def price_sale_vnd(self):
    #     if self.price_sale:
    #         return "{:,.0f}".format(self.price_sale)
    #     return ''
    
    def get_percentage(self):
        percent = (1 - (self.price_sale / self.price)) * 100
        return percent
    
    def get_price(self):
        if self.price_sale and self.price_sale > 0:
            return self.price_sale
        return self.price

    def get_absolute_url(self):
        return reverse('product:product_detail', kwargs={
            'slug_category': self.category.slug,
            'slug_product': self.slug
        })

@receiver(pre_delete, sender=Product)
def product_pre_delete(sender, instance, **kwargs): # Xóa cả image và thumbnail khi sản phẩm được xóa
    if instance.image:
        instance.image.delete(save=False)
    if instance.thumbnail:
        instance.thumbnail.delete(save=False)
                
class ProductPhoto(models.Model):
    product = models.ForeignKey(Product, related_name='photo_product', on_delete=models.CASCADE, blank=True, null=True)
    photo = models.FileField(upload_to=user_directory_path_productphoto, blank=True, null=True)
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return f'{str(self.product_id)} - {str(self.photo)}'

    def save(self, *args, **kwargs):
        """Override save để nén ảnh và tạo thumbnail khi lưu"""
        if self.photo:
            # Xử lý ảnh chính
            self.photo = compress_image(self.photo)

        super().save(*args, **kwargs)  # Lưu model sau khi xử lý

@receiver(pre_delete, sender=ProductPhoto)
def productphoto_pre_delete(sender, instance, **kwargs):
    if instance.photo:
        instance.photo.delete(save=False)

        
class Attribute(models.Model):
    key = models.CharField(max_length=100)
    value = models.CharField(max_length=255)

    class Meta:
        unique_together = ('key', 'value')

    def __str__(self):
        return f"{self.key}: {self.value}"
    
@receiver(post_save, sender=Attribute)
@receiver(post_delete, sender=Attribute)
def update_variants_on_attribute_change(sender, instance, **kwargs):
    # Lấy tất cả các Variant liên quan đến Attribute
    variant_attributes = VariantAttribute.objects.filter(attribute=instance)
    variants = ProductVariant.objects.filter(attributes__in=variant_attributes)

    # Cập nhật name và slug cho từng Variant
    for variant in variants:
        attributes = variant.attributes.all()
        attributes_str = ', '.join([f"{attr.attribute.key}: {attr.attribute.value}" for attr in attributes])
        name = f"{variant.product.name} ({attributes_str})" if attributes_str else f"{variant.product.name}"
        slug = create_slug(name)
        
        # Sử dụng update để tránh kích hoạt signal
        ProductVariant.objects.filter(pk=variant.pk).update(name=name, slug=slug)
        
class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=True, null=True)  # Cho phép để trống, sẽ tự động tạo
    price = models.IntegerField(default=0)
    price_sale = models.IntegerField(blank=True, null=True)
    stock = models.PositiveIntegerField(blank=True, null=True, default=0)
    slug = models.SlugField(blank=True, null=True)

    def __str__(self):
        return f"{self.name}"
    
    def get_price(self):
        if self.price_sale and self.price_sale > 0:
            return self.price_sale
        return self.price

    @property
    def attribute_summary(self):
        attributes = self.attributes.all()
        summary = [
            f"{variant_attribute.attribute.key}: {variant_attribute.attribute.value}"
            for variant_attribute in attributes
            if variant_attribute.attribute
        ]
        return ', '.join(summary) if summary else 'Mặc định'

    @property
    def attribute_values_summary(self):
        attributes = self.attributes.all()
        values = [
            variant_attribute.attribute.value
            for variant_attribute in attributes
            if variant_attribute.attribute
        ]
        return ' / '.join(values) if values else 'Mặc định'
        
# Tạo hoặc cập nhật Variant khi Product được tạo hoặc cập nhật
@receiver(post_save, sender=Product)
def create_or_update_variant(sender, instance, created, **kwargs):
    """
    Tạo hoặc cập nhật ProductVariant khi Product được tạo hoặc cập nhật.
    """
    # Lấy ProductVariant đầu tiên (nếu tồn tại)
    product_variant = ProductVariant.objects.filter(product=instance).first()

    if created:
        # Nếu Product mới được tạo và chưa có Variant
        if not product_variant:
            ProductVariant.objects.create(
                product=instance,
                name=instance.name,
                price=instance.price,
                price_sale=instance.price_sale,
            )
    else:
        # Nếu Product đã tồn tại, cập nhật Variant nếu có
        if product_variant:
            product_variant.name = instance.name
            product_variant.price = instance.price
            product_variant.price_sale = instance.price_sale
            product_variant.save(update_fields=["name", "price", "price_sale"])
        else:
            # Nếu chưa có Variant, tạo mới
            ProductVariant.objects.create(
                product=instance,
                name=instance.name,
                price=instance.price,
                price_sale=instance.price_sale,
            )

# Cập nhật name và slug của Variant khi Product thay đổi
@receiver(post_save, sender=ProductVariant)
def update_variant_name(sender, instance, **kwargs):
    attributes = instance.attributes.all()
    attributes_str = ', '.join([f"{attr.attribute.key}: {attr.attribute.value}" for attr in attributes])
    name = f"{instance.product.name} ({attributes_str})" if attributes_str else f"{instance.product.name}"
    slug = create_slug(name)
 
    # Cập nhật trực tiếp mà không gọi save()
    ProductVariant.objects.filter(pk=instance.pk).update(name=name, slug=slug)

# Cập nhật giá của Product dựa trên cặp price và price_sale của một ProductVariant
@receiver(post_save, sender=ProductVariant)
@receiver(post_delete, sender=ProductVariant)
def update_product_price(sender, instance, **kwargs):
    """
    Cập nhật giá của Product dựa trên cặp price và price_sale của một ProductVariant.
    """
    product = instance.product

    # Lấy tất cả các variants của product
    variants = ProductVariant.objects.filter(product=product)

    if variants.exists():
        # Lấy variant có giá thấp nhất theo giá hiệu lực.
        cheapest_variant = variants.annotate(
            effective_price=models.Case(
                models.When(price_sale__gt=0, then=models.F('price_sale')),
                default=models.F('price'),
                output_field=models.IntegerField(),
            )
        ).order_by('effective_price', 'id').first()

        # Lấy giá và giá giảm từ variant rẻ nhất
        price = cheapest_variant.price
        price_sale = cheapest_variant.price_sale
    else:
        # Nếu không có variant nào, đặt giá trị mặc định
        price = 0
        price_sale = None

    # Cập nhật trực tiếp product mà không gọi save()
    Product.objects.filter(pk=product.pk).update(price=price, price_sale=price_sale)


class VariantAttribute(models.Model):
    variant = models.ForeignKey(ProductVariant, related_name='attributes', on_delete=models.CASCADE)
    attribute = models.ForeignKey(Attribute, related_name='variant_attributes', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('variant', 'attribute')

    def __str__(self):
        return f"{self.variant.product.name} ({self.attribute.key}: {self.attribute.value})"

# Cập nhật name và slug của Variant khi Attribute thay đổi
@receiver(post_save, sender=VariantAttribute)
@receiver(post_delete, sender=VariantAttribute)
def update_variant_name(sender, instance, **kwargs):
    variant = instance.variant
    attributes = variant.attributes.all()
    attributes_str = ', '.join([f"{attr.attribute.key}: {attr.attribute.value}" for attr in attributes])
    name = f"{variant.product.name} ({attributes_str})" if attributes_str else f"{variant.product.name}"
    slug = create_slug(name)

    # Cập nhật trực tiếp mà không gọi save()
    ProductVariant.objects.filter(pk=variant.pk).update(name=name, slug=slug)





        
####################### Specification #######################
# class ProductSpecification(models.Model):
#     product = models.OneToOneField(Product, on_delete=models.CASCADE, blank=True, null=True)
#     specification = CKEditor5Field(default='', blank=True, null=True)
#     previous_image_urls = models.TextField(editable=False, blank=True, default='')
    
#     class Meta:
#         verbose_name_plural = 'ProductSpecification'
#         ordering = ('-id', )
        
#     def __str__(self):
#         return self.product.name
    
#     def save(self, *args, **kwargs):
#         # Lấy ra các tên file hình ảnh đã được upload trước đó
#         if self.pk:
#             old_instance = ProductSpecification.objects.get(pk=self.pk)
#             old_images = self._extract_uploaded_images(old_instance.specification)
#         else:
#             old_images = []

#         super().save(*args, **kwargs)

#         # Lấy các hình ảnh mới sau khi lưu
#         new_images = self._extract_uploaded_images(self.specification)

#         # Xác định các hình ảnh cần xóa
#         images_to_delete = set(old_images) - set(new_images)
#         self._delete_uploaded_images(images_to_delete)

#         # Lưu lại các URL mới
#         self.previous_image_urls = ','.join(new_images)
#         super().save(update_fields=['previous_image_urls'])

#     def _extract_uploaded_images(self, specification):
#         # Trích xuất tên các file hình ảnh đã được upload từ trường CKEditor5Field
#         uploaded_images = []
#         if specification:
#             soup = BeautifulSoup(specification, 'html.parser')
#             img_tags = soup.find_all('img')
#             for img_tag in img_tags:
#                 src = img_tag.get('src', '')
#                 if src.startswith(settings.MEDIA_URL):
#                     uploaded_images.append(src.replace(settings.MEDIA_URL, ''))
#         return uploaded_images

#     def _delete_uploaded_images(self, images_to_delete):
#         # Xóa các file hình ảnh trong thư mục media
#         for image in images_to_delete:
#             path = os.path.join(settings.MEDIA_ROOT, image)
#             if os.path.exists(path):
#                 os.remove(path)


# # Khi tạo Product thì tự động tạo ProductSpecification
# @receiver(post_save, sender=Product)
# def create_ProductSpecification(sender, instance, created, **kwargs):
#     if created:
#         ProductSpecification.objects.create(product=instance)

# # Hàm xử lý tín hiệu để xóa các file được upload trong CKEditor5Field khi một ProductSpecification bị xóa.
# @receiver(post_delete, sender=ProductSpecification)
# def delete_uploaded_files(sender, instance, **kwargs):
#     if instance.specification:
#         # Xác định các file được upload trong CKEditor5Field
#         media_root = settings.MEDIA_ROOT
#         media_url = settings.MEDIA_URL

#         # Tìm tất cả các URL file trong nội dung CKEditor
#         soup = BeautifulSoup(instance.specification, 'html.parser')
#         for img in soup.find_all('img'):
#             file_url = img['src']
#             if file_url.startswith(media_url):
#                 file_path = os.path.join(media_root, file_url[len(media_url):])
#                 if os.path.isfile(file_path):
#                     os.remove(file_path)




# class ProductSpecification_2(models.Model):
#     product = models.OneToOneField(Product, on_delete=models.CASCADE, blank=True, null=True)
#     specification = CKEditor5Field(default='', blank=True, null=True)
#     previous_image_urls = models.TextField(editable=False, blank=True, default='')

#     class Meta:
#         verbose_name_plural = 'ProductSpecification_2'
#         ordering = ('-id', )
        
#     def __str__(self):
#         return self.product.name
    
#     def save(self, *args, **kwargs):
#         # Lấy ra các tên file hình ảnh đã được upload trước đó
#         if self.pk:
#             old_instance = ProductSpecification_2.objects.get(pk=self.pk)
#             old_images = self._extract_uploaded_images(old_instance.specification)
#         else:
#             old_images = []

#         super().save(*args, **kwargs)

#         # Lấy các hình ảnh mới sau khi lưu
#         new_images = self._extract_uploaded_images(self.specification)

#         # Xác định các hình ảnh cần xóa
#         images_to_delete = set(old_images) - set(new_images)
#         self._delete_uploaded_images(images_to_delete)

#         # Lưu lại các URL mới
#         self.previous_image_urls = ','.join(new_images)
#         super().save(update_fields=['previous_image_urls'])

#     def _extract_uploaded_images(self, specification):
#         # Trích xuất tên các file hình ảnh đã được upload từ trường CKEditor5Field
#         uploaded_images = []
#         if specification:
#             soup = BeautifulSoup(specification, 'html.parser')
#             img_tags = soup.find_all('img')
#             for img_tag in img_tags:
#                 src = img_tag.get('src', '')
#                 if src.startswith(settings.MEDIA_URL):
#                     uploaded_images.append(src.replace(settings.MEDIA_URL, ''))
#         return uploaded_images

#     def _delete_uploaded_images(self, images_to_delete):
#         # Xóa các file hình ảnh trong thư mục media
#         for image in images_to_delete:
#             path = os.path.join(settings.MEDIA_ROOT, image)
#             if os.path.exists(path):
#                 os.remove(path)


# # Khi tạo Product thì tự động tạo ProductSpecification_2
# @receiver(post_save, sender=Product)
# def create_ProductSpecification_2(sender, instance, created, **kwargs):
#     if created:
#         ProductSpecification_2.objects.create(product=instance)

# # Hàm xử lý tín hiệu để xóa các file được upload trong CKEditor5Field khi một ProductSpecification_2 bị xóa.
# @receiver(post_delete, sender=ProductSpecification_2)
# def delete_uploaded_files(sender, instance, **kwargs):
#     if instance.specification:
#         # Xác định các file được upload trong CKEditor5Field
#         media_root = settings.MEDIA_ROOT
#         media_url = settings.MEDIA_URL

#         # Tìm tất cả các URL file trong nội dung CKEditor
#         soup = BeautifulSoup(instance.specification, 'html.parser')
#         for img in soup.find_all('img'):
#             file_url = img['src']
#             if file_url.startswith(media_url):
#                 file_path = os.path.join(media_root, file_url[len(media_url):])
#                 if os.path.isfile(file_path):
#                     os.remove(file_path)

class BaseProductSpecification(models.Model):
    product = models.OneToOneField('Product', on_delete=models.CASCADE, blank=True, null=True)
    specification = CKEditor5Field(default='', blank=True, null=True)
    previous_image_urls = models.TextField(editable=False, blank=True, default='')

    class Meta:
        abstract = True
        ordering = ('-id', )

    def save(self, *args, **kwargs):
        # Lấy ra các tên file hình ảnh đã được upload trước đó
        if self.pk:
            old_instance = self.__class__.objects.get(pk=self.pk)
            old_images = self._extract_uploaded_images(old_instance.specification)
        else:
            old_images = []

        super().save(*args, **kwargs)

        # Lấy các hình ảnh mới sau khi lưu
        new_images = self._extract_uploaded_images(self.specification)

        # Xác định các hình ảnh cần xóa
        images_to_delete = set(old_images) - set(new_images)
        self._delete_uploaded_images(images_to_delete)

        # Lưu lại các URL mới
        self.previous_image_urls = ','.join(new_images)
        super().save(update_fields=['previous_image_urls'])

    def _extract_uploaded_images(self, specification):
        # Trích xuất tên các file hình ảnh đã được upload từ trường CKEditor5Field
        uploaded_images = []
        if specification:
            soup = BeautifulSoup(specification, 'html.parser')
            img_tags = soup.find_all('img')
            for img_tag in img_tags:
                src = img_tag.get('src', '')
                if src.startswith(settings.MEDIA_URL):
                    uploaded_images.append(src.replace(settings.MEDIA_URL, ''))
        return uploaded_images

    def _delete_uploaded_images(self, images_to_delete):
        # Xóa các file hình ảnh trong thư mục media
        for image in images_to_delete:
            path = os.path.join(settings.MEDIA_ROOT, image)
            if os.path.exists(path):
                os.remove(path)

# Tạo các model kế thừa từ lớp trừu tượng
class ProductSpecification(BaseProductSpecification):
    class Meta(BaseProductSpecification.Meta):
        verbose_name_plural = 'ProductSpecification'

    def __str__(self):
        return self.product.name

class ProductSpecification_2(BaseProductSpecification):
    class Meta(BaseProductSpecification.Meta):
        verbose_name_plural = 'ProductSpecification_2'

    def __str__(self):
        return self.product.name

# Add more ProductSpecification models as needed
class ProductSpecification_3(BaseProductSpecification):
    class Meta(BaseProductSpecification.Meta):
        verbose_name_plural = 'ProductSpecification_3'

    def __str__(self):
        return self.product.name

class ProductSpecification_4(BaseProductSpecification):
    class Meta(BaseProductSpecification.Meta):
        verbose_name_plural = 'ProductSpecification_4'

    def __str__(self):
        return self.product.name

# Khi tạo Product thì tự động tạo ProductSpecification
@receiver(post_save, sender=Product)
def create_ProductSpecification(sender, instance, created, **kwargs):
    if created:
        ProductSpecification.objects.create(product=instance)
        ProductSpecification_2.objects.create(product=instance)
        ProductSpecification_3.objects.create(product=instance)
        ProductSpecification_4.objects.create(product=instance)

# Hàm xử lý tín hiệu để xóa các file được upload trong CKEditor5Field khi một ProductSpecification bị xóa.
@receiver(post_delete, sender=ProductSpecification)
@receiver(post_delete, sender=ProductSpecification_2)
@receiver(post_delete, sender=ProductSpecification_3)
@receiver(post_delete, sender=ProductSpecification_4)
def delete_uploaded_files(sender, instance, **kwargs):
    if instance.specification:
        media_root = settings.MEDIA_ROOT
        media_url = settings.MEDIA_URL
        soup = BeautifulSoup(instance.specification, 'html.parser')
        for img in soup.find_all('img'):
            file_url = img['src']
            if file_url.startswith(media_url):
                file_path = os.path.join(media_root, file_url[len(media_url):])
                if os.path.isfile(file_path):
                    os.remove(file_path)



######################################## Cart, CartItem, Order, OrderItem ########################################
class Cart(models.Model):
    user = models.OneToOneField(User, related_name='cart', on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.user:
            return f"Cart of {self.user.username}"
        return f"Guest cart {self.session_key or self.pk}"
    
    def total_price(self):
        return sum(item.total_price() for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, related_name='items_cart', on_delete=models.CASCADE, null=True, blank=True)
    variant = models.ForeignKey(ProductVariant, related_name='variants_cart', on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'CartItem'
        ordering = ('-id', )
        
    def __str__(self):
        return f'{self.product.name} x {self.quantity}'
    
    def total_price(self):
        if self.variant:
            return self.variant.get_price() * self.quantity
            
        if self.product:
            return self.product.get_price() * self.quantity
    
    # def price_cart_vnd(self):
    #     return "{:,.0f}".format(self.price_cart)
    
    # def subtotal_vnd(self):
    #     return "{:,.0f}".format(self.subtotal)

class Order(models.Model):
    user = models.ForeignKey(User, related_name='orders', on_delete=models.CASCADE, null=True, blank=True)
    fullname = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    shipping_address = models.TextField(null=True, blank=True)
    payment_method = models.CharField(max_length=50, default='COD')
    
    # Cập nhật trạng thái đơn hàng
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_price = models.IntegerField(default=0)

    is_paid = models.CharField(max_length=30, default='Chưa thanh toán')
    status_order = models.CharField(max_length=30, default='Chờ xử lý', choices=STATUS_ORDER)
    note = models.CharField(max_length=255, default='', null=True, blank=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural = 'Order'
        ordering = ('-id', )
        
    def __str__(self):
        customer = self.user.username if self.user else (self.fullname or 'Khách vãng lai')
        return f"Order #{self.id} by {customer}"

    def calculate_total(self):
        self.total_price = sum(item.subtotal for item in self.items.all())
        self.save()

    def total_price_vnd(self):
        return "{:,.0f}".format(self.total_price)

    @property
    def payment_method_label(self):
        if self.payment_method == 'COD':
            return 'Thanh toán khi nhận hàng (COD)'
        if self.payment_method == 'BANK':
            return 'Chuyển khoản ngân hàng'
        if self.payment_method and self.payment_method.startswith('PM:'):
            paymentmethod_id = self.payment_method.replace('PM:', '', 1)
            if paymentmethod_id.isdigit():
                paymentmethod = PaymentMethod.objects.filter(id=paymentmethod_id).first()
                if paymentmethod:
                    return paymentmethod.name
        return self.payment_method
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE, blank=True, null=True)
    product = models.ForeignKey(Product, related_name='items_order', on_delete=models.SET_NULL, blank=True, null=True)
    variant = models.ForeignKey(ProductVariant, related_name='variants_order', on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.IntegerField(null=True, blank=True)  # Lưu giá tại thời điểm mua hàng
    subtotal = models.IntegerField(null=True, blank=True)  # Tổng tiền tại thời điểm mua hàng

    class Meta:
        verbose_name_plural = 'OrderItem'
        ordering = ('-id', )
        
    def __str__(self):
        return f"{self.quantity} x {self.product.name} in order #{self.order.id}"

    def total_price(self):
        if self.variant:
            return self.variant.get_price() * self.quantity

        if self.product:
            return self.product.get_price() * self.quantity
    
    # def price_cart_vnd(self):
    #     return "{:,.0f}".format(self.price_cart)
    
    # def subtotal_vnd(self):
    #     return "{:,.0f}".format(self.subtotal)



class Wishlist(models.Model):
    user = models.ForeignKey(User, related_name='wishlist', on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    product = models.ForeignKey(Product, related_name='wishlisted_by', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')  # Ensure the same product isn't added to wishlist multiple times

    def __str__(self):
        owner = self.user.username if self.user else f"Guest {self.session_key or self.pk}"
        return f"{owner} - {self.product.name} (Wishlist)"

class Compare(models.Model):
    user = models.ForeignKey(User, related_name='comparisons', on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, related_name='compared_in')

    def __str__(self):
        return f"{self.user} - {self.products}"
    
class Review(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='reviews', on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()  # Rating từ 1 đến 5
    content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')  # Đảm bảo mỗi người dùng chỉ đánh giá một lần

    def __str__(self):
        return f"{self.user.username} - {self.product.name} - Rating: {self.rating} sao"
