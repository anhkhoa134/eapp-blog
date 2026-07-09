# myapp/storage.py

import os
from urllib.parse import urljoin
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from PIL import Image, UnidentifiedImageError
from io import BytesIO
from django.core.files.base import ContentFile


# class CustomStorage(FileSystemStorage):
#     """Lưu trữ tùy chỉnh cho hình ảnh của django_ckeditor_5."""
#     location = os.path.join(settings.MEDIA_ROOT, "django_ckeditor_5")
#     base_url = urljoin(settings.MEDIA_URL, "django_ckeditor_5/")



# class CustomStorage(FileSystemStorage):
#     """Lưu trữ tùy chỉnh cho hình ảnh của django_ckeditor_5."""

#     def __init__(self, user_id, username, *args, **kwargs):
#         self.user_id = user_id
#         self.username = username
#         location = os.path.join(settings.MEDIA_ROOT, f"user_{user_id}_{username}", "django_ckeditor_5")
#         base_url = urljoin(settings.MEDIA_URL, f"user_{user_id}_{username}/django_ckeditor_5/")
#         super().__init__(location, base_url, *args, **kwargs)

#     def _save(self, name, content):
#         return super()._save(name, content)



class CustomStorage(FileSystemStorage):
    """Lưu trữ tùy chỉnh cho hình ảnh của django_ckeditor_5."""

    def __init__(self, user_id=None, username=None, *args, **kwargs):
        self.user_id = user_id
        self.username = username
        if user_id and username:
            location = os.path.join(settings.MEDIA_ROOT, f"{user_id}", "django_ckeditor_5")
            base_url = urljoin(settings.MEDIA_URL, f"{user_id}/django_ckeditor_5/")
        else:
            location = os.path.join(settings.MEDIA_ROOT, "django_ckeditor_5")
            base_url = urljoin(settings.MEDIA_URL, "django_ckeditor_5/")
        super().__init__(location, base_url, *args, **kwargs)

    def _save(self, name, content):
        # File không phải hình ảnh (pdf, doc...), ảnh động hoặc ảnh lỗi thì lưu nguyên trạng
        try:
            image = Image.open(content)

            # GIF/WebP động lưu nguyên trạng vì convert sẽ mất animation
            if getattr(image, 'is_animated', False):
                content.seek(0)
                return super()._save(name, content)

            # Chuyển đổi hình ảnh sang định dạng WebP (giữ kênh trong suốt nếu có)
            if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
                image = image.convert('RGBA')
            else:
                image = image.convert('RGB')

            # Resize hình ảnh nếu chiều rộng lớn hơn 500px
            max_width = 500
            if image.width > max_width:
                ratio = max_width / float(image.width)
                new_height = int((float(image.height) * float(ratio)))
                image = image.resize((max_width, new_height), Image.LANCZOS)

            # WebP giới hạn mỗi chiều tối đa 16383px nên phải chặn cả chiều cao
            max_height = 16383
            if image.height > max_height:
                ratio = max_height / float(image.height)
                new_width = max(1, int(float(image.width) * float(ratio)))
                image = image.resize((new_width, max_height), Image.LANCZOS)

            # Lưu hình ảnh vào buffer
            image_io = BytesIO()
            image.save(image_io, format='WEBP', quality=70)
        except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError):
            content.seek(0)
            return super()._save(name, content)

        # Đổi phần mở rộng file sang .webp
        name = f'{os.path.splitext(name)[0]}.webp'
        image_content = ContentFile(image_io.getvalue(), name=name)

        return super()._save(name, image_content)
