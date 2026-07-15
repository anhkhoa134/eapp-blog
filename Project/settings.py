from pathlib import Path
import os
import sys
from django.contrib.messages import constants as messages

from environ import Env
env = Env()
Env.read_env()
ENVIRONMENT = env('ENVIRONMENT', default='prod') or 'prod'
if ENVIRONMENT == 'dev':
    DEBUG = True
else:
    DEBUG = False
TESTING = 'test' in sys.argv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# Môi trường phát triển sản phẩm
# DEBUG = True
# ALLOWED_HOSTS = ['*']

# Môi trường sản xuất thương mại
# DEBUG = False
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '.ngrok-free.app', env('VPS'), env('DOMAIN'), f"www.{env('DOMAIN')}", 'testserver']


LOGIN_URL = '/dang-nhap/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
CSRF_FAILURE_VIEW = 'App_Core.views.csrf_failure' # Lỗi CSRF ở trang login -> redirect về login kèm thông báo, nơi khác -> trang 403

# SESSION_COOKIE_AGE = 1800  # Thời gian tính bằng giây, ở đây là 30 phút
# SESSION_EXPIRE_AT_BROWSER_CLOSE = True # Session sẽ hết hạn khi đóng trình duyệt
# request.session.flush()  # Xóa toàn bộ dữ liệu session
# request.session.clear_expired()  # Xóa các session hết hạn
# del request.session['next_url']  # Xóa 1 key trong session


MESSAGE_TAGS = {
    messages.DEBUG: 'secondary',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}


# Application definition
INSTALLED_APPS = [
    'jazzmin',
    
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'django_celery_beat',
    'django_celery_results',
    
    'App_Core',
    'App_Account',
    'App_Product',
    'App_Post',
    'App_Quanly',

    'templated_email',
    'django_ckeditor_5',
    'corsheaders',
    'autoslug',
    'widget_tweaks',
    'django_filters',
    'django_extensions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware', # Xác thực người dùng
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    'App_Core.middleware.SecurityMiddleware', # Middleware bảo mật chặn truy cập đáng ngờ
    'App_Core.middleware.UploadLimitMiddleware', # Giới hạn dung lượng upload của User
    'App_Core.middleware.PageViewMiddleware', # Đếm số lần truy cập vào các trang

]

APPEND_SLASH = True
USE_THOUSAND_SEPARATOR=True

ROOT_URLCONF = 'Project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                
                'App_Core.context_processors.cart',
                'App_Quanly.context_processors.quanly_menu',

            ],
            'libraries': {
                'custom_tags': 'templatetags.custom_tags',
            },
        },
    },
]

WSGI_APPLICATION = 'Project.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Ho_Chi_Minh'

USE_I18N = True

# USE_TZ = True # chuyển đổi sang UTC
USE_TZ = False # sử dụng múi giờ GMT+7 hiện tại


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = '/static/'                 # URL mà từ đó các tệp tĩnh sẽ được phục vụ
STATICFILES_DIRS = [                    # Danh sách các thư mục bổ sung để Django tìm kiếm c>
    os.path.join(BASE_DIR, 'static'),
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') # Thư mục đích mà Django sẽ thu thập tất>

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# python manage.py findstatic admin/js/cancel.js admin/js/popup_response.js
# STATICFILES_FINDERS = [
#     'django.contrib.staticfiles.finders.FileSystemFinder',
#     'django.contrib.staticfiles.finders.AppDirectoriesFinder',
# ]

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
        'OPTIONS': {
            'location': os.path.join(BASE_DIR, 'media'),  # Đường dẫn đến thư mục media
        },
    },
    'staticfiles': {
        'BACKEND': (
            'django.contrib.staticfiles.storage.StaticFilesStorage'
            if DEBUG or TESTING
            else 'whitenoise.storage.CompressedManifestStaticFilesStorage'
        ),
    },
}



# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

customColorPalette = [
        {
            'color': 'hsl(4, 90%, 58%)',
            'label': 'Red'
        },
        {
            'color': 'hsl(340, 82%, 52%)',
            'label': 'Pink'
        },
        {
            'color': 'hsl(291, 64%, 42%)',
            'label': 'Purple'
        },
        {
            'color': 'hsl(262, 52%, 47%)',
            'label': 'Deep Purple'
        },
        {
            'color': 'hsl(231, 48%, 48%)',
            'label': 'Indigo'
        },
        {
            'color': 'hsl(207, 90%, 54%)',
            'label': 'Blue'
        },
    ]

CKEDITOR_5_CUSTOM_CSS = '/static/canhan/css/editor_styles.css'
CKEDITOR_5_USER_LANGUAGE = True
CKEDITOR_5_FILE_STORAGE = "App_Core.storage.CustomStorage" # Định nghĩa class lưu trữ tùy chỉnh
CK_EDITOR_5_UPLOAD_FILE_VIEW_NAME = "core:custom_upload_file" # Chỉ định view upload file tùy chỉnh
CKEDITOR_5_ALLOW_ALL_FILE_TYPES = False # Chỉ cho phép các loại file trong CKEDITOR_5_UPLOAD_FILE_TYPES, tránh upload .svg/.html gây XSS
CKEDITOR_5_UPLOAD_FILE_TYPES = ['jpeg', 'pdf', 'png', 'jpg', 'gif', 'bmp', 'webp', 'tiff', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'] # tùy chọn
CKEDITOR_5_CONFIGS = {
    'default': {
        'toolbar': ['heading', '|', 
                    'alignment', 'bold', 'italic', 'underline', 'strikethrough', 'link', '|',
                    'fontFamily', 'fontColor', 'fontBackgroundColor', '|',
                    # 'outdent', 'indent', 
                    'bulletedList', 'numberedList', 'blockQuote', '|',
                    'imageUpload', 'insertTable', '|',
                    # 'fontSize', 'mediaEmbed',
                    ],
        
        # 'fontSize': {
        #     'options': [
        #         'tiny', 'small', 'default', 'big', 'huge'
        #     ],
        #     'supportsAllValues': True  # Cho phép sử dụng các kích thước phông chữ tùy chỉnh
        # },
        # 'mediaEmbed': {
        #     'providers': [
        #         {
        #             'name': 'YouTube',
        #             'url': r"""https://www\.youtube\.com/watch\?v=([a-zA-Z0-9_-]+)""",
        #             'html': r"""<iframe width="560" height="315" src="https://www.youtube.com/embed/$1" frameborder="0" allowfullscreen></iframe>""",
        #         },
        #         # Bạn có thể thêm các nhà cung cấp khác ở đây
        #     ]
        # },

        'removePlugins': [],  # Loại bỏ plugin lọc nội dung dán từ Word
        'extraPlugins': ['Code', 'List', 'Link', 'PasteFromOffice'],  # Thêm plugin List vào đây
        'allowedContent': True,  # Không lọc nội dung HTML dán vào
        # "link": {
        #     "decorators": {
        #         "openInNewTab": {
        #             "mode": "manual",
        #             "label": "Mở trong tab mới",
        #             "attributes": {
        #                 "target": "_blank",
        #                 "rel": "noopener noreferrer"
        #             }
        #         }
        #     }
        # },
        'link': {
            'addTargetToExternalLinks': True,  # Tự động thêm target="_blank" vào link ngoài
        },
        'clipboard': {
            'pasteFilter': 'all',  # Cho phép dán toàn bộ nội dung HTML (giữ nguyên link)
            # 'forcePlainText': True,  # Ép buộc dán văn bản chỉ có text, không mất chữ

        },


        'alignment': {
            'options': ['left', 'center', 'right', 'justify']            
        },
        'image': {
            'toolbar': ['imageTextAlternative', '|', 'imageStyle:alignLeft',
                        'imageStyle:alignRight', 'imageStyle:alignCenter', 'imageStyle:side',  '|'],
            'styles': [
                'full',
                'side',
                'alignLeft',
                'alignRight',
                'alignCenter',
            ]
        },
    },
    
    'extends': {
        'toolbar': ['heading', '|', 'outdent', 'indent', '|', 'bold', 'italic', 'link', 'underline', 'strikethrough',
                    'code','subscript', 'superscript', 'highlight', '|', 'codeBlock', 'sourceEditing', 'insertImage',
                    'bulletedList', 'numberedList', 'todoList', '|',  'blockQuote', 'imageUpload', '|',
                    'fontSize', 'fontFamily', 'fontColor', 'fontBackgroundColor', 'mediaEmbed', 'removeFormat',
                    'insertTable',],
        'image': {
            'toolbar': ['imageTextAlternative', '|', 'imageStyle:alignLeft',
                        'imageStyle:alignRight', 'imageStyle:alignCenter', 'imageStyle:side',  '|'],
            'styles': [
                'full',
                'side',
                'alignLeft',
                'alignRight',
                'alignCenter',
            ]
        },
        'table': {
            'contentToolbar': [ 'tableColumn', 'tableRow', 'mergeTableCells',
            'tableProperties', 'tableCellProperties' ],
            'tableProperties': {
                'borderColors': customColorPalette,
                'backgroundColors': customColorPalette
            },
            'tableCellProperties': {
                'borderColors': customColorPalette,
                'backgroundColors': customColorPalette
            }
        },
        'heading' : {
            'options': [
                { 'model': 'paragraph', 'title': 'Paragraph', 'class': 'ck-heading_paragraph' },
                { 'model': 'heading1', 'view': 'h1', 'title': 'Heading 1', 'class': 'ck-heading_heading1' },
                { 'model': 'heading2', 'view': 'h2', 'title': 'Heading 2', 'class': 'ck-heading_heading2' },
                { 'model': 'heading3', 'view': 'h3', 'title': 'Heading 3', 'class': 'ck-heading_heading3' }
            ]
        }
    },    
}


# DATA_UPLOAD_MAX_MEMORY_SIZE = 20971520  # 20 MB
# FILE_UPLOAD_MAX_MEMORY_SIZE = 20971520  # 20 MB

# CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = [
    'https://' + str(env('DOMAIN')),
    'https://www.' + str(env('DOMAIN')),
    "http://localhost:8000",  # Thêm localhost nếu bạn đang phát triển cục bộ
    "http://127.0.0.1:8000",
]
# CORS_ALLOWED_ORIGINS không hỗ trợ wildcard, phải dùng regex cho ngrok
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.ngrok-free\.app$",
]
CSRF_TRUSTED_ORIGINS = [
    'https://' + str(env('DOMAIN')),
    'https://www.' + str(env('DOMAIN')),
    "http://localhost:8000",  # Thêm localhost nếu bạn đang phát triển cục bộ
    "http://127.0.0.1:8000",
    'https://*.ngrok-free.app',
]
CORS_ALLOW_METHODS = [
    "GET",
    "POST",
    "PUT",
    "DELETE",

    "OPTIONS",
    "HEAD",
    "PATCH",
]
CORS_ALLOW_HEADERS = [
    "Authorization",
    "Content-Type",
    "X-CSRFToken",
    
    # "Access-Control-Allow-Origin",
    # "Access-Control-Allow-Headers",
    # "Access-Control-Allow-Methods",
    # "Access-Control-Allow-Credentials",
    # "Access-Control-Request-Headers",
    # "Access-Control-Request-Method",
    # "Request-Control-Allow-Headers",

    # "accept",
    # "authorization",
    # "content-type",
    # "user-agent",
    # "x-csrftoken",
    # "x-requested-with",
]



# ACCESS_CONTROL_ALLOW_ORIGIN = "*"
# ACCESS_CONTROL_ALLOW_HEADERS = "*"
# ACCESS_CONTROL_ALLOW_METHODS = "*"
# ACCESS_CONTROL_ALLOW_CREDENTIALS = True




CORS_ALLOW_CREDENTIALS = True # Cho phép các yêu cầu cross-origin bao gồm thông tin xác thực (như cookies)
SECURE_CONTENT_TYPE_NOSNIFF = True # Ngăn chặn trình duyệt đoán loại nội dung, buộc nó tuân theo loại nội dung đã khai báo
X_FRAME_OPTIONS = 'DENY' # Bảo vệ chống lại clickjacking bằng cách ngăn chặn trang web được nhúng trong một khung

SECURE_SSL_REDIRECT = False # Chuyển hướng HTTP sang HTTPS để đảm bảo giao tiếp an toàn (SECURE_SSL_REDIRECT = True)

SESSION_COOKIE_SECURE = True # Đảm bảo rằng cookies phiên chỉ được gửi qua HTTPS
CSRF_COOKIE_SECURE = True # Đảm bảo rằng cookies CSRF chỉ được gửi qua HTTPS

# Thiết lập HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 3600 # Kích hoạt HTTP Strict Transport Security (HSTS) buộc trình duyệt chỉ tương tác với trang web qua HTTPS # Thời gian (giây) trình duyệt nhớ yêu cầu này (1 giờ)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True # Áp dụng HSTS cho tất cả các tên miền con của trang web
SECURE_HSTS_PRELOAD = False # Preload yêu cầu max-age >= 31536000 (1 năm); bật lại khi tăng SECURE_HSTS_SECONDS


# Logging configuration để debug lỗi production
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True) # RotatingFileHandler không tự tạo thư mục

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
        'detailed': {
            'format': '[{asctime}] {levelname} {name} {module}.{funcName}:{lineno} - {message}',
            'style': '{',
        },
    },
    'handlers': {
        'debug_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'debug.log'),
            'maxBytes': 5 * 1024 * 1024,  # 5MB
            'backupCount': 1,
            'formatter': 'detailed',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'error.log'),
            'maxBytes': 5 * 1024 * 1024,  # 5MB
            'backupCount': 1,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO' if not DEBUG else 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['error_file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'App_Core': {
            'handlers': ['debug_file', 'error_file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}



# Cấu hình backend của django-templated-email
TEMPLATED_EMAIL_BACKEND = 'templated_email.backends.vanilla_django.TemplateBackend'
TEMPLATED_EMAIL_FROM_EMAIL = None                 # String containing the email to send the email from - fallback to DEFAULT_FROM_EMAIL
TEMPLATED_EMAIL_TEMPLATE_DIR = 'registration/' # The directory containing the templates, use '' if using the top level
TEMPLATED_EMAIL_FILE_EXTENSION = 'email'          # The file extension of the template files
TEMPLATED_EMAIL_AUTO_PLAIN = True                 # Set to false to disable the behavior of calculating the plain part from the html part of the email when `html2text <https://pypi.python.org/pypi/html2text>` is installed
TEMPLATED_EMAIL_PLAIN_FUNCTION = None             # Specify a custom function that converts from HTML to the plain part



# Cấu hình cho email (ví dụ sử dụng SMTP)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = env.int('EMAIL_PORT')
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = f"eApp Blog <{env('EMAIL_HOST_USER')}>"
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')



# Cấu hình Celery
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'django-db'  # Hoặc bạn có thể sử dụng 'redis://localhost:6379/0' nếu bạn muốn lưu kết quả vào Redis
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Ho_Chi_Minh'
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
