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
    default_thumbnail_url,
    post_icon_url,
    subject_icon_url,
    subsubject_icon_url,
)
from App_Core.model_utils import (
    compress_image,
    create_slug,
    get_default_datetime,
    user_directory_path_post,
    user_directory_path_postphoto,
    user_directory_path_subject,
    user_directory_path_subsubject,
)

class Subject(models.Model):
    title = models.CharField(max_length=255, unique=True)
    # slug = AutoSlugField(populate_from='title', unique=True)
    slug = models.SlugField(unique=True, blank=True, null=True)
    description = models.TextField(default='', blank=True, null=True)
    # image = models.ImageField(upload_to='subjects/', blank=True, null=True)
    image = models.ImageField(upload_to=user_directory_path_subject, blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Subject'
        ordering = ('-id', )

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.slug = create_slug(self.title)
        
        """Override save để nén ảnh và tạo thumbnail khi lưu"""
        is_new_image = False

        # Kiểm tra trường hợp chỉnh sửa (edit)
        if self.pk:  # Nếu sản phẩm đã tồn tại
            old_instance = Subject.objects.filter(pk=self.pk).first()
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
            return default_thumbnail_url
            
    def get_icon(self): # chỉ cần gọi {{product.get_icon}}, ko cần bọc trong tag <img>
        if self.image:
            return mark_safe('<img src="%s" width="35" height="35" style="border-radius: 8px;" />' % (self.image.url))
        else:
            return mark_safe('<img src="%s" width="35" height="35" style="border-radius: 8px;" />' % subject_icon_url)
    
    def get_absolute_url(self):
        return reverse('post:subject', kwargs={'slug_subject': self.slug})

@receiver(pre_delete, sender=Subject)
def subject_pre_delete(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)
        
class SubSubject(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='subsubjects')
    title = models.CharField(max_length=255, blank=True, null=True)
    slug = models.SlugField(blank=True, null=True)
    description = models.TextField(default='', blank=True, null=True)
    image = models.ImageField(upload_to=user_directory_path_subsubject, blank=True, null=True)

    class Meta:
        verbose_name_plural = 'SubSubject'
        ordering = ('-id', )
        unique_together = ('subject', 'title')
        
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        self.slug = create_slug(self.title)
        
        """Override save để nén ảnh và tạo thumbnail khi lưu"""
        is_new_image = False

        # Kiểm tra trường hợp chỉnh sửa (edit)
        if self.pk:  # Nếu sản phẩm đã tồn tại
            old_instance = SubSubject.objects.filter(pk=self.pk).first()
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
            return default_thumbnail_url
            
    def get_icon(self): # chỉ cần gọi {{product.get_icon}}, ko cần bọc trong tag <img>
        if self.image:
            return mark_safe('<img src="%s" width="35" height="35" style="border-radius: 8px;" />' % (self.image.url))
        else:
            return mark_safe('<img src="%s" width="35" height="35" style="border-radius: 8px;" />' % subsubject_icon_url)
    
@receiver(pre_delete, sender=SubSubject)
def subsubject_pre_delete(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)
        
class Post(models.Model):
    # user = models.ForeignKey(User, blank=True, null=True, related_name='posts', on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, blank=True, null=True, related_name='posts', on_delete=models.SET_NULL)
    subsubject = models.ForeignKey(SubSubject, blank=True, null=True, related_name='posts', on_delete=models.SET_NULL)

    title = models.CharField(max_length=255, unique=True)
    # slug = AutoSlugField(populate_from='title', unique=True)
    slug = models.SlugField(unique=True, blank=True, null=True)
    description = models.TextField(default='', blank=True, null=True)
    author = models.CharField(max_length=50, default='', blank=True, null=True)
    is_sale = models.BooleanField(default=False)
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    display_at = models.DateTimeField(default=get_default_datetime, null=True, blank=True)
    # image = models.ImageField(upload_to='posts/', blank=True, null=True)
    image = models.ImageField(upload_to=user_directory_path_post, blank=True, null=True)
    thumbnail = models.ImageField(upload_to=user_directory_path_post, blank=True, null=True)
    
    price = models.IntegerField(null=True, blank=True) 
    address = models.CharField(max_length=255, default='', null=True, blank=True)
    
    class Meta:
        verbose_name_plural = 'Post'
        ordering = ('-id', )

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.slug = create_slug(self.title)
        
        """Override save để nén ảnh và tạo thumbnail khi lưu"""
        is_new_image = False
        
        # Kiểm tra trường hợp chỉnh sửa (edit)
        if self.pk:  # Nếu sản phẩm đã tồn tại
            old_instance = Post.objects.filter(pk=self.pk).first()
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

    def get_icon(self): # chỉ cần gọi {{post.get_icon}}, ko cần bọc trong tag <img>
        if self.image:
            return mark_safe('<img src="%s" width="35" height="35" style="border-radius: 8px;" />' % (self.image.url))
        else:
            return mark_safe('<img src="%s" width="35" height="35" style="border-radius: 8px;" />' % post_icon_url)
        
    def price_vnd(self):
        if self.price:
            return "{:,.0f}".format(self.price)
        return ''    

    def get_absolute_url(self):
        return reverse('post:post_detail', kwargs={
            'slug_subject': self.subject.slug,
            'slug_post': self.slug
        })

@receiver(pre_delete, sender=Post)
def post_pre_delete(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)
    if instance.thumbnail:
        instance.thumbnail.delete(save=False)

class PostPhoto(models.Model):
    post = models.ForeignKey(Post, related_name='photo_post', on_delete=models.CASCADE, blank=True, null=True)
    photo = models.FileField(upload_to=user_directory_path_postphoto, blank=True, null=True)
    
    def __str__(self):
        return f'{str(self.post_id)} - {str(self.photo)}'

    def save(self, *args, **kwargs):
        """Override save để nén ảnh và tạo thumbnail khi lưu"""
        if self.photo:
            # Xử lý ảnh chính
            self.photo = compress_image(self.photo)

        super().save(*args, **kwargs)  # Lưu model sau khi xử lý

@receiver(pre_delete, sender=PostPhoto)
def postphoto_pre_delete(sender, instance, **kwargs):
    if instance.photo:
        instance.photo.delete(save=False)
        
class PostContent(models.Model):
    post = models.OneToOneField(Post, on_delete=models.CASCADE, blank=True, null=True)
    content = CKEditor5Field(default='', blank=True, null=True)
    previous_image_urls = models.TextField(editable=False, blank=True, default='')
    
    class Meta:
        verbose_name_plural = 'PostContent'
        ordering = ('-id', )
        
    def __str__(self):
        return self.post.title
    
    def save(self, *args, **kwargs):
        # Lấy ra các tên file hình ảnh đã được upload trước đó
        if self.pk:
            old_instance = PostContent.objects.get(pk=self.pk)
            old_images = self._extract_uploaded_images(old_instance.content)
        else:
            old_images = []

        super().save(*args, **kwargs)

        # Lấy các hình ảnh mới sau khi lưu
        new_images = self._extract_uploaded_images(self.content)

        # Xác định các hình ảnh cần xóa
        images_to_delete = set(old_images) - set(new_images)
        self._delete_uploaded_images(images_to_delete)

        # Lưu lại các URL mới
        self.previous_image_urls = ','.join(new_images)
        super().save(update_fields=['previous_image_urls'])

    def _extract_uploaded_images(self, content):
        # Trích xuất tên các file hình ảnh đã được upload từ trường CKEditor5Field
        uploaded_images = []
        if content:
            soup = BeautifulSoup(content, 'html.parser')
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


# Khi tạo Post thì tự động tạo PostContent
@receiver(post_save, sender=Post)
def create_PostContent(sender, instance, created, **kwargs):
    if created:
        PostContent.objects.create(post=instance)

# Hàm xử lý tín hiệu để xóa các file được upload trong CKEditor5Field khi một PostContent bị xóa.
@receiver(post_delete, sender=PostContent)
def postcontent_post_delete(sender, instance, **kwargs):
    uploaded_images = instance._extract_uploaded_images(instance.content)
    instance._delete_uploaded_images(uploaded_images)


class Comment(models.Model):
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='comments', on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)
    # parent = models.ForeignKey('self', null=True, blank=True, related_name='child_comments', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.post.title}"
    
    def is_reply(self):
        return self.parent is not None

class Reply(models.Model):
    comment = models.ForeignKey(Comment, related_name='replies', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='replies', on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - Reply to comment {self.comment.id}"
    
######################################## View ########################################
