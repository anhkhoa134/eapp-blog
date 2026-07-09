from django.db import models


class Contact(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)



class PageView(models.Model):
    path = models.CharField(max_length=255, unique=True)  # Lưu URL của trang
    view_count = models.PositiveIntegerField(default=0)  # Lưu số lần truy cập

    def __str__(self):
        return f"{self.path}: {self.view_count} lượt truy cập"

######################################## Cấu hình trang quản lý ########################################
