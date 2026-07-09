import os
from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponse
from django.template.loader import render_to_string
import json
from App_Core.constants import MAX_UPLOAD_REQUEST_SIZE, MAX_UPLOAD_SIZE

def generate_response(message, type='bg-success'):
    # print(message, type)
    return HttpResponse(
        status=204,
        headers={
            'HX-Trigger': json.dumps({
                "listChange": None,
                "showMessage": {"message": message, "type": type}
            })
        }
    )

# Tính tổng dung lượng thư mục
def get_directory_size(directory):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return total_size

# Cấu hình Middleware chạy khi User thực hiện Upload (điều kiện yêu cầu User phải đăng nhập)
# Nếu một lần upload hoặc tổng dung lượng toàn Project vượt giới hạn thì không được Upload
class UploadLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == 'POST' and request.FILES and request.user.is_authenticated:
            total_size = get_directory_size(settings.BASE_DIR)
            file_size = sum(
                file.size
                for _, files in request.FILES.lists()
                for file in files
            )

            if file_size > MAX_UPLOAD_REQUEST_SIZE:
                return generate_response(
                    f"Mỗi lần upload không được vượt quá {MAX_UPLOAD_REQUEST_SIZE // (1024 * 1024)}MB.",
                    type='bg-danger',
                )

            if total_size + file_size > MAX_UPLOAD_SIZE:
                # html_content = render_to_string('partials/upload_limit_exceeded.html')
                # return HttpResponse(html_content)
                # return HttpResponseForbidden('You have exceeded your upload limit.')
                return generate_response(f"Vượt quá tổng dung lượng Project cho phép.", type='bg-danger')

        response = self.get_response(request)
        return response

# Cấu hình Middleware để đếm số lần truy cập vào các trang
# và lưu vào model PageView
def PageViewMiddleware(get_response):
    def middleware(request):
        # Import PageView khi cần thiết để tránh vòng lặp
        from App_Core.models import PageView
        import logging

        path = request.path
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        ip_address = request.META.get('REMOTE_ADDR', '')

        # Danh sách các đường dẫn đáng ngờ cần theo dõi
        suspicious_patterns = [
            # PHP và web files
            '.php', '.env', 'config.php', 'wp-', 'admin', 'api', 
            'swagger', 'openapi', 'docker', 'backup', 'log',
            'database', 'credentials', 'aws', 'ssh', 'git',
            
            # Git và IDE files
            '.gitignore', '.cursorignore', '.vscode', '.idea', '.vs',
            '.gitattributes', '.gitmodules', '.gitkeep',
            '.editorconfig', '.prettierrc', '.eslintrc',
            
            # SQL files và database
            '.sql', '.db', '.sqlite', '.sqlite3', '.mdb', '.accdb',
            'database.sql', 'schema.sql', 'migration.sql',
            'backup.sql', 'dump.sql', 'export.sql',
            'db_backup', 'db_dump', 'database_backup',
            
            # File extensions đáng ngờ (không phải static files)
            '.doc', '.docx', '.md', '.markdown', '.rtf',
            '.pdf', '.xls', '.xlsx', '.ppt', '.pptx', '.odt',
            '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',
            '.exe', '.bat', '.cmd', '.sh', '.ps1', '.vbs',
            '.ini', '.cfg', '.conf', '.config', '.properties',
            '.log', '.tmp', '.temp', '.bak', '.old', '.orig',
            '.key', '.pem', '.crt', '.cer', '.p12', '.pfx',
            '.py', '.pl', '.rb', '.go', '.java', '.cpp', '.c',
            '.asp', '.aspx', '.jsp', '.cfm', '.cgi', '.fcgi'
        ]
        
        # Loại trừ các file hợp lệ
        allowed_files = [
            'robots.txt', 'sitemap.xml', 'favicon.ico',
            '.well-known/appspecific/com.chrome.devtools.json',
            'admin-guide'
        ]
        
        # Kiểm tra nếu là file được phép
        if any(allowed in path for allowed in allowed_files):
            # Không coi là đáng ngờ
            pass
        else:
            # Kiểm tra nếu có pattern đáng ngờ
            is_suspicious = any(pattern in path.lower() for pattern in suspicious_patterns)
            
            if is_suspicious:
                # Log các truy cập đáng ngờ
                logger = logging.getLogger('App_Core')
                logger.warning(f"Suspicious access attempt: {path} from IP: {ip_address}, User-Agent: {user_agent}")
        
        # Chỉ đếm các đường dẫn hợp lệ
        if not path.startswith('/admin/') and not path.startswith('/static/') and not path.startswith('/media/') and not path.startswith('/quan-ly/') and not path.startswith('/quanly/') and not path.startswith('/htmx/'):
            page_view, created = PageView.objects.get_or_create(path=path)
            page_view.view_count += 1
            page_view.save()

        response = get_response(request)
        return response

    return middleware

# Middleware bảo mật để chặn các truy cập đáng ngờ
class SecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path.lower()
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        # Danh sách các pattern đáng ngờ cần chặn
        blocked_patterns = [
            # PHP và web files
            '.php', '.env', 'config.php', 'wp-config', 'wp-admin', 
            'admin.php', 'phpmyadmin', 'pma', 'mysql', 'database',
            'backup', 'backup.sql', 'dump.sql', 'error.log', 'access.log',
            'docker-compose', '.git', '.svn', '.htaccess', 'php.ini',
            'swagger', 'openapi', 'api-docs', 'swagger-ui',
            'server-status', 'server-info', 'info.php', 'phpinfo',
            'aws', 'credentials', 'secrets', 'config.json', 'config.yml',
            'ssh', 'id_rsa', 'id_ed25519', 'known_hosts',
            
            # Git và IDE files
            '.gitignore', '.cursorignore', '.vscode', '.idea', '.vs',
            '.gitattributes', '.gitmodules', '.gitkeep',
            '.editorconfig', '.prettierrc', '.eslintrc',
            
            # SQL files và database
            '.sql', '.db', '.sqlite', '.sqlite3', '.mdb', '.accdb',
            'database.sql', 'schema.sql', 'migration.sql',
            'backup.sql', 'dump.sql', 'export.sql',
            'db_backup', 'db_dump', 'database_backup',
            
            # File extensions đáng ngờ (không phải static files)
            '.doc', '.docx', '.md', '.markdown', '.rtf',
            '.pdf', '.xls', '.xlsx', '.ppt', '.pptx', '.odt',
            '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',
            '.exe', '.bat', '.cmd', '.sh', '.ps1', '.vbs',
            '.ini', '.cfg', '.conf', '.config', '.properties',
            '.log', '.tmp', '.temp', '.bak', '.old', '.orig',
            '.key', '.pem', '.crt', '.cer', '.p12', '.pfx',
            '.py', '.pl', '.rb', '.go', '.java', '.cpp', '.c',
            '.asp', '.aspx', '.jsp', '.cfm', '.cgi', '.fcgi'
        ]
        
        # Loại trừ các file hợp lệ
        allowed_files = [
            'robots.txt', 'sitemap.xml', 'favicon.ico',
            '.well-known/appspecific/com.chrome.devtools.json',
            'admin-guide',
            'static/quanly/products.zip',  # File mẫu ZIP cho import sản phẩm
        ]
        
        # Kiểm tra nếu là file được phép
        if any(allowed in path for allowed in allowed_files):
            response = self.get_response(request)
            return response
        
        # Kiểm tra nếu đường dẫn chứa pattern đáng ngờ
        if any(pattern in path for pattern in blocked_patterns):
            # Log và trả về 404 để che giấu sự tồn tại của file
            import logging
            logger = logging.getLogger('App_Core')
            logger.warning(f"Blocked suspicious request: {request.path} from IP: {request.META.get('REMOTE_ADDR', '')}")
            
            from django.http import HttpResponseNotFound
            return HttpResponseNotFound()
        
        # Kiểm tra User-Agent đáng ngờ
        suspicious_user_agents = [
            'sqlmap', 'nikto', 'nmap', 'masscan', 'zap', 'burp',
            'wget', 'curl', 'python-requests', 'bot', 'crawler',
            'scanner', 'exploit', 'hack'
        ]
        
        if any(ua in user_agent for ua in suspicious_user_agents):
            import logging
            logger = logging.getLogger('App_Core')
            logger.warning(f"Blocked suspicious User-Agent: {user_agent} from IP: {request.META.get('REMOTE_ADDR', '')}")
            
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden()

        response = self.get_response(request)
        return response
