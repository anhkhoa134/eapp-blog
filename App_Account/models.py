import os

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils.html import mark_safe

from App_Core.constants import GENDER_CHOICES, static_avatar
from App_Core.middleware import get_directory_size
from App_Core.model_utils import compress_image, user_directory_path_profile

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    fullname = models.CharField(max_length=50, default='', null=True, blank=True)
    job = models.CharField(max_length=50, default='', null=True, blank=True)
    company = models.CharField(max_length=50, default='', null=True, blank=True)
    phone = models.CharField(max_length=50, default='', null=True, blank=True)
    address = models.CharField(max_length=255, default='', null=True, blank=True)
    email = models.EmailField(default='', null=True, blank=True)
    birthday = models.DateField(default=None, null=True, blank=True)
    gender = models.CharField(choices=GENDER_CHOICES,
                              max_length=20, default='', null=True, blank=True)

    # image = models.ImageField(upload_to="profile", null=True, blank=True)
    image = models.ImageField(upload_to=user_directory_path_profile, null=True, blank=True)
    # qr_code = models.ImageField(upload_to=user_directory_path_profile, null=True, blank=True)
    about = models.CharField(max_length=255, default='', null=True, blank=True)
    note = models.TextField(default='', null=True, blank=True)
    # verified = models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural = 'Profile'
        ordering = ('-id', )

    def __str__(self):
        return str(self.user) 
    
    def save(self, *args, **kwargs):
        """Override save để nén ảnh và tạo thumbnail khi lưu"""
        is_new_image = False

        # Kiểm tra trường hợp chỉnh sửa (edit)
        if self.pk:  # Nếu sản phẩm đã tồn tại
            old_instance = Profile.objects.filter(pk=self.pk).first()
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
            
        # Kiểm tra trường hợp chỉnh sửa (edit) cho qr_code
        # is_new_qr_code = False
        # if self.pk:  # Nếu profile đã tồn tại
        #     old_instance = Profile.objects.filter(pk=self.pk).first()
        #     if old_instance and old_instance.qr_code != self.qr_code:
        #         is_new_qr_code = True
        #         if old_instance.qr_code:  # Xóa qr_code cũ nếu có qr_code mới
        #             old_qr_code_path = old_instance.qr_code.path
        #             if os.path.exists(old_qr_code_path):
        #                 os.remove(old_qr_code_path)
        # else:
        #     # Trường hợp thêm mới, luôn coi qr_code là mới
        #     is_new_qr_code = True

        # # Nén hình ảnh (qr_code) nếu có ảnh mới
        # if self.qr_code and is_new_qr_code:
        #     self.qr_code = compress_image(self.qr_code, max_width=600, max_height=600)

        super().save(*args, **kwargs)  # Lưu model sau khi xử lý

            
    def get_image(self):
        if self.image:
            return self.image.url
        else:
            return static_avatar
    
    # def get_qr_code(self):
    #     if self.qr_code:
    #         return self.qr_code.url
    #     else:
    #         return default_thumbnail_url
            
    def get_icon(self): # chỉ cần gọi {{profile.get_icon}}, ko cần bọc trong tag <img>
        if self.image:
            return mark_safe('<img src="%s" width="35" height="35" style="border-radius: 8px;" />' % (self.image.url))
        else:
            return mark_safe('<img src="%s" width="35" height="35" style="border-radius: 8px;" />' % (static_avatar ))

    def get_uploaded_size(self):
        user_directory = os.path.join(settings.MEDIA_ROOT, f'home/user/{self.user.id}')
        return get_directory_size(user_directory)
    
# Khi tạo User thì tự động tạo Profile
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        
@receiver(pre_delete, sender=Profile)
def profile_pre_delete(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)
    # if instance.qr_code:
    #     instance.qr_code.delete(save=False)


class Checkout_info(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    fullname = models.CharField(max_length=50, default='', null=True, blank=True)
    phone = models.CharField(max_length=50, default='', null=True, blank=True)
    address = models.CharField(max_length=255, default='', null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Info'
        ordering = ('-id', )

    def __str__(self):
        return str(self.user)

# Tự động tạo Profile xong rồi thì tiếp tục tự động tạo Info
@receiver(post_save, sender=Profile)
def create_checkout_info(sender, instance, created, **kwargs):
    if created: 
        Checkout_info.objects.create(user=instance.user)
        
# Mỗi lần lưu thông tin của Profile đều chạy lệnh này (cả created và updated)
@receiver(post_save, sender=Profile)
def update_checkout_info(sender, instance, created, **kwargs):
    if not created:  # Chỉ xử lý khi instance không phải là mới được tạo
        if not instance.user.checkout_info.fullname: 
            instance.user.checkout_info.fullname = instance.fullname
            instance.user.checkout_info.save()
        if not instance.user.checkout_info.phone:
            instance.user.checkout_info.phone = instance.phone
            instance.user.checkout_info.save()
        if not instance.user.checkout_info.address:
            instance.user.checkout_info.address = instance.address
            instance.user.checkout_info.save()
            
        # Ngắt kết nối tín hiệu sau khi thực hiện xong lần đầu
        # post_save.disconnect(update_checkout_info, sender=Profile)

@receiver(post_save, sender=Checkout_info)
def update_profile(sender, instance, created, **kwargs):
    if not created:  # Chỉ xử lý khi instance không phải là mới được tạo
        if not instance.user.profile.fullname: 
            instance.user.profile.fullname = instance.fullname
            instance.user.profile.save()
        if not instance.user.profile.phone:
            instance.user.profile.phone = instance.phone
            instance.user.profile.save()
        if not instance.user.profile.address:
            instance.user.profile.address = instance.address
            instance.user.profile.save()
            
        # Ngắt kết nối tín hiệu sau khi thực hiện xong lần đầu
        # post_save.disconnect(update_profile, sender=Checkout_info)


