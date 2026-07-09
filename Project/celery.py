from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Thiết lập môi trường cho Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project.settings')

# Khởi tạo Celery
app = Celery('Project')

# Sử dụng cấu hình từ Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Tự động khám phá các task trong các ứng dụng Django
app.autodiscover_tasks()