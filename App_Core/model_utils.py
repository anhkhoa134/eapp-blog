import io
import os
from datetime import datetime

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.text import slugify
from PIL import Image as PILImage


def create_slug(name):
    name = name.replace("Đ", "D").replace("đ", "d")
    return slugify(name)


def get_default_datetime():
    now = datetime.now()
    return now.replace(second=0, microsecond=0)


def user_directory_path_product(instance, filename):
    if instance.request.user:
        return f'{instance.request.user.id}/products/{filename}'
    return f'products/{filename}'


def user_directory_path_productphoto(instance, filename):
    if instance.request.user:
        return f'{instance.request.user.id}/productphotos/{filename}'
    return f'productphotos/{filename}'


def user_directory_path_category(instance, filename):
    if instance.request.user:
        return f'{instance.request.user.id}/categories/{filename}'
    return f'categories/{filename}'


def user_directory_path_subcategory(instance, filename):
    if instance.request.user:
        return f'{instance.request.user.id}/subcategories/{filename}'
    return f'subcategories/{filename}'


def user_directory_path_post(instance, filename):
    if instance.request.user:
        return f'{instance.request.user.id}/post/{filename}'
    return f'post/{filename}'


def user_directory_path_postphoto(instance, filename):
    if instance.request.user:
        return f'{instance.request.user.id}/postphotos/{filename}'
    return f'postphotos/{filename}'


def user_directory_path_subject(instance, filename):
    if instance.request.user:
        return f'{instance.request.user.id}/subjects/{filename}'
    return f'subjects/{filename}'


def user_directory_path_subsubject(instance, filename):
    if instance.request.user:
        return f'{instance.request.user.id}/subsubjects/{filename}'
    return f'subsubjects/{filename}'


def user_directory_path_profile(instance, filename):
    if instance.user:
        return f'home/{instance.user.id}/user/{filename}'
    return f'home/user/{filename}'


def compress_image(image, max_width=1200, max_height=1200):
    img = PILImage.open(image)
    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
        img = img.convert('RGBA')
    else:
        img = img.convert('RGB')
    img.thumbnail((max_width, max_height), PILImage.LANCZOS)

    output = io.BytesIO()
    img.save(output, format='WEBP', quality=70)
    output.seek(0)

    return InMemoryUploadedFile(
        output,
        'ImageField',
        f'{os.path.splitext(image.name)[0]}.webp',
        'image/webp',
        output.getbuffer().nbytes,
        None,
    )
