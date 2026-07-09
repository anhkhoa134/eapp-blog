#!/usr/bin/env python3
"""
Công cụ vận hành (production + security) tích hợp.
Gộp từ:
  - 2_manage_production.py (deploy/debug/server)
  - 3_security_tools.py (monitor/logs/all)

Sử dụng:
  python scripts/3_security_tools.py deploy  [--skip-backup] [--skip-debug] [--quick]
  python scripts/3_security_tools.py debug   [--check-only] [--fix-common] [--verbose]
  python scripts/3_security_tools.py server  (debug 500 errors)

  python scripts/3_security_tools.py monitor (phân tích PageView records từ DB)
  python scripts/3_security_tools.py logs    (quét file log trên disk)
  python scripts/3_security_tools.py all     (chạy monitor + logs)

  python scripts/3_security_tools.py refactor-audit (audit sau tách domain app)
"""
from __future__ import annotations

import argparse
import logging
import glob
import os
import re
import sys
from datetime import datetime
from pathlib import Path


# ──────────────────────────────────────────────
# Helpers chung (Django)
# ──────────────────────────────────────────────

def _setup_django(settings_module: str = "Project.settings") -> None:
    """Khởi tạo Django nếu chưa được setup."""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)
    import django
    django.setup()


# ──────────────────────────────────────────────
# Pattern dùng chung
# ──────────────────────────────────────────────

SUSPICIOUS_PATTERNS: list[str] = [
    # PHP và web files
    r"\.php", r"\.env", r"config\.php", r"wp-", r"admin", r"api",
    r"swagger", r"openapi", r"docker", r"backup", r"log",
    r"database", r"credentials", r"aws", r"ssh", r"git",
    r"mysql", r"phpmyadmin", r"pma", r"\.htaccess", r"php\.ini",
    r"server-status", r"server-info", r"info\.php", r"phpinfo",
    r"secrets", r"config\.json", r"config\.yml", r"id_rsa",
    r"id_ed25519", r"known_hosts", r"\.git", r"\.svn",
    # Git và IDE files
    r"\.gitignore", r"\.cursorignore", r"\.vscode", r"\.idea", r"\.vs",
    r"\.gitattributes", r"\.gitmodules", r"\.gitkeep",
    r"\.editorconfig", r"\.prettierrc", r"\.eslintrc",
    # SQL / database
    r"\.sql", r"\.db", r"\.sqlite", r"\.sqlite3", r"\.mdb", r"\.accdb",
    r"database\.sql", r"schema\.sql", r"migration\.sql",
    r"backup\.sql", r"dump\.sql", r"export\.sql",
    r"db_backup", r"db_dump", r"database_backup",
    # File extensions đáng ngờ
    r"\.doc", r"\.docx", r"\.md", r"\.markdown", r"\.rtf",
    r"\.pdf", r"\.xls", r"\.xlsx", r"\.ppt", r"\.pptx", r"\.odt",
    r"\.zip", r"\.rar", r"\.7z", r"\.tar", r"\.gz", r"\.bz2",
    r"\.exe", r"\.bat", r"\.cmd", r"\.sh", r"\.ps1", r"\.vbs",
    r"\.ini", r"\.cfg", r"\.conf", r"\.config", r"\.properties",
    r"\.log", r"\.tmp", r"\.temp", r"\.bak", r"\.old", r"\.orig",
    r"\.key", r"\.pem", r"\.crt", r"\.cer", r"\.p12", r"\.pfx",
    r"\.py", r"\.pl", r"\.rb", r"\.go", r"\.java", r"\.cpp", r"\.c",
    r"\.asp", r"\.aspx", r"\.jsp", r"\.cfm", r"\.cgi", r"\.fcgi",
]

ALLOWED_STATIC_PATTERNS: list[str] = [
    r"/static/", r"/media/", r"\.css", r"\.js", r"\.png", r"\.jpg",
    r"\.jpeg", r"\.gif", r"\.svg", r"\.ico", r"\.woff", r"\.woff2",
    r"\.ttf", r"\.eot", r"\.map", r"robots\.txt", r"sitemap\.xml",
]

DOMAIN_APPS: tuple[str, ...] = (
    "App_Core",
    "App_Account",
    "App_Product",
    "App_Post",
    "App_Quanly",
)

RUNTIME_SCAN_ROOTS: tuple[str, ...] = (
    "App_Core",
    "App_Account",
    "App_Product",
    "App_Post",
    "App_Quanly",
    "Project",
    "templates",
    "scripts",
)

RUNTIME_TEXT_SUFFIXES: set[str] = {
    ".py",
    ".html",
    ".txt",
    ".js",
    ".css",
    ".json",
    ".yml",
    ".yaml",
}

LEGACY_RUNTIME_MARKERS: tuple[str, ...] = (
    "from App_ecom",
    "import App_ecom",
    "App_ecom.",
    "App_ecom:",
    "legacy_ecom",
    "App_Accounts",
)


def _is_suspicious(path_or_line: str) -> bool:
    lower = path_or_line.lower()
    if any(re.search(p, lower) for p in ALLOWED_STATIC_PATTERNS):
        return False
    return any(re.search(p, lower) for p in SUSPICIOUS_PATTERNS)


def _iter_runtime_text_files(base_dir: Path):
    skip_dirs = {
        ".git",
        ".hg",
        ".svn",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "venv",
        ".venv",
        "env",
        "ENV",
        "node_modules",
        "staticfiles",
        "media",
        "logs",
        "backup",
    }
    self_path = Path(__file__).resolve()
    for root_name in RUNTIME_SCAN_ROOTS:
        root = base_dir / root_name
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.resolve() == self_path:
                continue
            if set(path.relative_to(base_dir).parts) & skip_dirs:
                continue
            if path.suffix.lower() not in RUNTIME_TEXT_SUFFIXES:
                continue
            yield path


# ══════════════════════════════════════════════
# SUBCOMMAND: debug  (từ 2_manage_production.py)
# ══════════════════════════════════════════════

def cmd_debug(args: argparse.Namespace) -> int:
    """
    Kiểm tra toàn diện môi trường production.
    Tùy chọn: --check-only | --fix-common | --verbose
    """
    _setup_django()

    from django.conf import settings
    from django.contrib.auth import get_user_model
    from django.core.management import call_command
    from django.db import connection

    BASE_DIR = getattr(settings, "BASE_DIR", Path(__file__).resolve().parent.parent)

    log_path = os.path.join(BASE_DIR, "logs", "debug_production.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_path), logging.StreamHandler()],
    )
    logger = logging.getLogger("ops.debug")

    issues: list[str] = []
    fixes: list[str] = []

    def log(message: str, level: str = "INFO") -> None:
        if level == "ERROR":
            logger.error(message)
            issues.append(message)
        elif level == "WARNING":
            logger.warning(message)
        elif level == "SUCCESS":
            logger.info("✅ %s", message)
            fixes.append(message)
        else:
            logger.info(message)

    def check_environment() -> None:
        log("🔧 Checking environment settings...")
        log(f"   - DEBUG: {getattr(settings, 'DEBUG', True)}")
        log(f"   - ENVIRONMENT: {getattr(settings, 'ENVIRONMENT', 'unknown')}")
        log(f"   - ALLOWED_HOSTS: {getattr(settings, 'ALLOWED_HOSTS', [])}")
        if getattr(settings, "DEBUG", True) and getattr(settings, "ENVIRONMENT", "") == "production":
            log("WARNING: DEBUG=True in production environment!", "WARNING")
        if not getattr(settings, "ALLOWED_HOSTS", []):
            log("WARNING: ALLOWED_HOSTS is empty!", "WARNING")

    def check_database_connection() -> None:
        log("🗄️  Checking database connection...")
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            log("Database connection: OK", "SUCCESS")
        except Exception as exc:
            log(f"Database connection failed: {exc}", "ERROR")

    def check_models_data() -> None:
        log("📊 Checking models data...")
        try:
            from App_Post.models import Post, Subject
            from App_Product.models import Category, Product

            for model, name in [
                (Category, "Categories"),
                (Product, "Products"),
                (Subject, "Subjects"),
                (Post, "Posts"),
            ]:
                try:
                    count = model.objects.count()
                    log(f"   - {name}: {count} records")
                    if count == 0 and name in ("Categories", "Products"):
                        log(f"WARNING: No {name.lower()} found", "WARNING")
                except Exception as exc:
                    log(f"Failed to count {name}: {exc}", "ERROR")
        except ImportError as exc:
            log(f"Cannot import catalog models: {exc}", "WARNING")

    def check_static_media_files() -> None:
        log("📁 Checking static and media files...")
        for attr in ("STATIC_ROOT", "MEDIA_ROOT"):
            root = getattr(settings, attr, None)
            if root and os.path.exists(root):
                file_count = sum(len(fs) for _, _, fs in os.walk(root))
                log(f"   - {attr}: {root} ({file_count} files)")
            elif root:
                log(f"{attr} directory doesn't exist: {root}", "WARNING")
            else:
                log(f"{attr} not configured", "WARNING")
        log(f"   - STATIC_URL: {getattr(settings, 'STATIC_URL', None)}")
        log(f"   - MEDIA_URL: {getattr(settings, 'MEDIA_URL', None)}")

    def check_logs_directory() -> None:
        log("📝 Checking logs directory...")
        logs_dir = os.path.join(BASE_DIR, "logs")
        if not os.path.exists(logs_dir):
            log("Logs directory doesn't exist, creating...", "WARNING")
            os.makedirs(logs_dir, exist_ok=True)
            log("Created logs directory", "SUCCESS")
        else:
            log_files = [f for f in os.listdir(logs_dir) if f.endswith(".log")]
            log(f"   - Logs directory: {len(log_files)} log files")
            if args.verbose:
                for lf in log_files:
                    size = os.path.getsize(os.path.join(logs_dir, lf))
                    log(f"     - {lf}: {size} bytes")

    def check_user_models() -> None:
        log("👤 Checking user models...")
        User = get_user_model()
        try:
            log(f"   - Total users: {User.objects.count()}")
            log(f"   - Admin users: {User.objects.filter(is_superuser=True).count()}")
            log(f"   - Active users: {User.objects.filter(is_active=True).count()}")
            if not User.objects.filter(is_superuser=True).exists():
                log("WARNING: No admin users found", "WARNING")
        except Exception as exc:
            log(f"Failed to check users: {exc}", "ERROR")

    def check_context_processors() -> None:
        log("🔄 Checking context processors...")
        try:
            from django.contrib.auth.models import AnonymousUser
            from django.http import HttpRequest

            from App_Core.context_processors import cart

            req = HttpRequest()
            req.user = AnonymousUser()
            ctx = cart(req)
            log("   - Context processor test (anonymous): OK")
            log(f"     - Categories: {len(ctx.get('categories', []))}")
            log(f"     - Subjects: {len(ctx.get('subjects', []))}")
        except Exception as exc:
            log(f"Context processor test failed: {exc}", "ERROR")

    def run_django_checks() -> None:
        log("🔍 Running Django system checks...")
        try:
            call_command("check", verbosity=0)
            log("Django system check: OK", "SUCCESS")
        except Exception as exc:
            log(f"Django system check failed: {exc}", "ERROR")
        try:
            call_command("check", "--deploy", verbosity=0)
            log("Django deployment check: OK", "SUCCESS")
        except Exception as exc:
            log(f"Django deployment check warning: {exc}", "WARNING")

    def fix_common_issues() -> None:
        log("🔧 Attempting to fix common issues...")
        for dir_name in ("logs", "staticfiles", "media"):
            dir_path = os.path.join(BASE_DIR, dir_name)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                log(f"Created directory: {dir_name}", "SUCCESS")
        try:
            call_command("migrate", verbosity=0)
            log("Migrations applied successfully", "SUCCESS")
        except Exception as exc:
            log(f"Migration failed: {exc}", "ERROR")
        try:
            call_command("collectstatic", "--noinput", verbosity=0)
            log("Static files collected successfully", "SUCCESS")
        except Exception as exc:
            log(f"Collect static failed: {exc}", "ERROR")

    print("🚀 Django Production Debugger")
    print("=" * 50)

    for fn in (
        check_environment,
        check_database_connection,
        check_logs_directory,
        check_static_media_files,
        check_models_data,
        check_user_models,
        check_context_processors,
        run_django_checks,
    ):
        try:
            fn()
        except Exception as exc:
            log(f"Check failed ({fn.__name__}): {exc}", "ERROR")
        print()

    if args.fix_common and not args.check_only:
        fix_common_issues()
        print()

    print("=" * 60)
    print("📋 PRODUCTION DEBUG REPORT")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if issues:
        print(f"\n❌ Issues found ({len(issues)}):")
        for i, iss in enumerate(issues, 1):
            print(f"  {i}. {iss}")
    else:
        print("\n✅ No critical issues found!")
    if fixes:
        print(f"\n🔧 Fixes applied ({len(fixes)}):")
        for i, fix in enumerate(fixes, 1):
            print(f"  {i}. {fix}")

    return 1 if issues else 0


# ══════════════════════════════════════════════
# SUBCOMMAND: server  (từ 2_manage_production.py)
# ══════════════════════════════════════════════

def cmd_server(_args: argparse.Namespace) -> int:
    """Debug lỗi 500 server errors."""
    _setup_django()

    import traceback as _traceback

    from django.conf import settings
    from django.contrib.auth import get_user_model
    from django.test import Client

    errors: list[str] = []
    successes: list[str] = []

    def err(msg: str) -> None:
        errors.append(msg)
        print(f"❌ {msg}")

    def ok(msg: str) -> None:
        successes.append(msg)
        print(f"✅ {msg}")

    def info(msg: str) -> None:
        print(f"ℹ️  {msg}")

    def test_home_page() -> None:
        info("Testing home page for 500 errors...")
        client = Client()
        try:
            resp = client.get("/")
            info(f"Anonymous user response: {resp.status_code}")
            if resp.status_code == 500:
                err("Home page returns 500 for anonymous users")
            elif resp.status_code == 200:
                ok("Home page works for anonymous users")

            User = get_user_model()
            if User.objects.filter(is_active=True).exists():
                user = User.objects.filter(is_active=True).first()
                if user:
                    client.force_login(user)
                    resp = client.get("/")
                    info(f"Authenticated user response: {resp.status_code}")
                    if resp.status_code == 500:
                        err("Home page returns 500 for authenticated users")
                    elif resp.status_code == 200:
                        ok("Home page works for authenticated users")
        except Exception as exc:
            err(f"Exception testing home page: {exc}")

    def test_context_processor_direct() -> None:
        info("Testing context processor directly...")
        try:
            from django.contrib.auth.models import AnonymousUser
            from django.http import HttpRequest

            from App_Core.context_processors import cart

            req = HttpRequest()
            req.user = AnonymousUser()
            ctx = cart(req)
            for key in ("cart", "categories", "subjects", "form_contact"):
                if key not in ctx:
                    err(f"Context processor missing key: {key}")
                    return
            ok("Context processor working correctly")
            info(
                "Context: cart=%s, categories=%s, subjects=%s"
                % (type(ctx.get("cart")), len(ctx.get("categories", [])), len(ctx.get("subjects", [])))
            )
        except Exception as exc:
            err(f"Context processor error: {exc}")
            _traceback.print_exc()

    def test_static_files_access() -> None:
        info("Testing static files access...")
        client = Client()
        for url in ("/static/website/css/main.css", "/static/canhan/css/style.css"):
            try:
                resp = client.get(url)
                if resp.status_code == 404:
                    err(f"Static file 404: {url}")
                elif resp.status_code == 200:
                    ok(f"Static file OK: {url}")
                else:
                    info(f"Static file status {resp.status_code}: {url}")
            except Exception as exc:
                err(f"Error accessing {url}: {exc}")

    def test_template_rendering() -> None:
        info("Testing template rendering...")
        try:
            from django.template.loader import render_to_string

            render_to_string(
                "base.html",
                {"categories": [], "subjects": [], "form_contact": None, "cart": None},
            )
            ok("Base template renders correctly")
            render_to_string(
                "home.html",
                {
                    "categories": [],
                    "products": [],
                    "products_featured": [],
                    "subjects": [],
                    "posts": [],
                    "posts_featured": [],
                },
            )
            ok("Home template renders correctly")
        except Exception as exc:
            err(f"Template rendering error: {exc}")
            _traceback.print_exc()

    def check_recent_error_logs() -> None:
        info("Checking recent error logs...")
        for log_name, label in (("error.log", "error"), ("debug.log", "debug")):
            path = os.path.join(settings.BASE_DIR, "logs", log_name)
            if os.path.exists(path) and os.path.getsize(path) > 0:
                with open(path, "r", errors="ignore") as f:
                    content = f.read()
                if "ERROR" in content or "500" in content:
                    err(f"Found errors in {label} log")
                    for line in [l for l in content.splitlines() if "ERROR" in l or "500" in l][-3:]:
                        print(f"   {line}")
                else:
                    ok(f"No critical errors in {label} log")
            else:
                info(f"{label}.log is empty or doesn't exist")

    def check_database_data() -> None:
        info("Checking database data...")
        try:
            from App_Post.models import Post, Subject
            from App_Product.models import Category, Product

            for model, name in [
                (Category, "Categories"),
                (Product, "Products"),
                (Subject, "Subjects"),
                (Post, "Posts"),
            ]:
                try:
                    count = model.objects.count()
                    if count == 0:
                        err(f"No {name.lower()} found in database")
                    else:
                        ok(f"{name}: {count} records")
                except Exception as exc:
                    err(f"Error querying {name}: {exc}")
        except Exception as exc:
            err(f"Database check error: {exc}")

    print("🔍 Django 500 Server Error Debugger")
    print("=" * 50)

    for fn in (
        check_database_data,
        test_context_processor_direct,
        test_template_rendering,
        test_home_page,
        test_static_files_access,
        check_recent_error_logs,
    ):
        try:
            fn()
            print()
        except Exception as exc:
            err(f"Test {fn.__name__} failed: {exc}")
            print()

    print("\n📊 SUMMARY:")
    print("=" * 30)
    print(f"✅ Successes: {len(successes)}")
    print(f"❌ Errors: {len(errors)}")

    if errors:
        print("\n❌ ERRORS FOUND:")
        for i, e in enumerate(errors, 1):
            print(f"  {i}. {e}")

    print("\n🔧 RECOMMENDED FIXES:")
    print("=" * 50)
    if "Context processor" in str(errors):
        print("📋 1. Fix Context Processor:")
        print("   - Check App_Core/context_processors.py")
    if "Static file 404" in str(errors):
        print("📋 2. Fix Static Files:")
        print("   - python manage.py collectstatic --noinput")
    if "template" in str(errors).lower():
        print("📋 3. Fix Templates:")
        print("   - Verify all context variables are provided")
    if "database" in str(errors).lower():
        print("📋 4. Fix Database:")
        print("   - python manage.py migrate")

    print("\n🚀 Quick Fix Commands:")
    print("   python manage.py collectstatic --noinput")
    print("   python manage.py migrate")
    print("   python scripts/3_security_tools.py debug --fix-common")

    return 0 if not errors else 1


# ══════════════════════════════════════════════
# SUBCOMMAND: deploy  (từ 2_manage_production.py)
# ══════════════════════════════════════════════

def cmd_deploy(args: argparse.Namespace) -> int:
    """
    Chạy toàn bộ quy trình setup production:
      1. Kiểm tra requirements
      2. Thiết lập môi trường
      3. Tạo thư mục cần thiết
      4. Backup database (trừ khi --skip-backup / --quick)
      5. Chạy migrations
      6. Collect static files
      7. Django system + deployment checks
      8. Kiểm tra superuser
      9. Chạy debug check (trừ khi --skip-debug / --quick)
    """
    if getattr(args, "quick", False):
        args.skip_backup = True
        args.skip_debug = True

    base_dir = Path(__file__).resolve().parent.parent

    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    NC = "\033[0m"

    def info(msg: str) -> None:
        print(f"{BLUE}ℹ️  {msg}{NC}")

    def success(msg: str) -> None:
        print(f"{GREEN}✅ {msg}{NC}")

    def warning(msg: str) -> None:
        print(f"{YELLOW}⚠️  {msg}{NC}")

    def error(msg: str) -> None:
        print(f"{RED}❌ {msg}{NC}")

    print(f"{GREEN}🚀 Django Production Setup{NC}")
    print("=" * 40)

    info("Checking requirements...")
    import shutil as _shutil

    if not _shutil.which("python") and not _shutil.which("python3"):
        error("Python is not installed")
        return 1
    if not (base_dir / "manage.py").exists():
        error(f"manage.py not found in {base_dir}")
        return 1
    success("Requirements check passed")

    info("Setting up environment...")
    if not os.environ.get("ENVIRONMENT"):
        os.environ["ENVIRONMENT"] = "production"
        warning("ENVIRONMENT not set, defaulting to production")
    info(f"Environment: {os.environ['ENVIRONMENT']}")

    info("Creating necessary directories...")
    for dir_name in ("staticfiles", "media", "logs", "backup"):
        dir_path = base_dir / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            success(f"Created directory: {dir_name}")
        else:
            info(f"Directory already exists: {dir_name}")

    if not getattr(args, "skip_backup", False):
        info("Creating database backup...")
        db_file = base_dir / "db.sqlite3"
        if db_file.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = base_dir / "backup" / f"db_backup_{timestamp}.sqlite3"
            import shutil as _sh

            _sh.copy2(db_file, backup_path)
            success(f"Database backed up: backup/db_backup_{timestamp}.sqlite3")
        else:
            warning("No db.sqlite3 found to backup")
    else:
        info("Skipping database backup")

    _setup_django()
    from django.core.management import call_command
    from django.contrib.auth import get_user_model

    info("Running database migrations...")
    try:
        call_command("migrate", no_input=True, verbosity=1)
        success("Migrations completed successfully")
    except Exception as exc:
        error(f"Migrations failed: {exc}")
        return 1

    info("Collecting static files...")
    try:
        call_command("collectstatic", no_input=True, verbosity=0)
        success("Static files collected successfully")
    except Exception as exc:
        error(f"Collect static failed: {exc}")
        return 1

    info("Running Django system checks...")
    try:
        call_command("check", verbosity=0)
        success("Basic system checks passed")
    except Exception as exc:
        error(f"System checks failed: {exc}")
        return 1

    info("Running deployment security checks...")
    try:
        call_command("check", "--deploy", verbosity=0)
        success("Deployment security checks passed")
    except Exception as exc:
        warning(f"Deployment warnings: {exc}")

    info("Checking superuser setup...")
    User = get_user_model()
    if User.objects.filter(is_superuser=True).exists():
        success("Superuser already exists")
    else:
        warning("No superuser found — hãy tạo bằng: python manage.py createsuperuser")

    if not getattr(args, "skip_debug", False):
        info("Running production debug check...")
        import types

        fake_args = types.SimpleNamespace(check_only=True, fix_common=False, verbose=False)
        rc = cmd_debug(fake_args)
        if rc != 0:
            warning("Debug check found issues. Chạy: python scripts/3_security_tools.py debug --fix-common")
    else:
        info("Skipping debug check")

    print()
    success("Production setup completed! 🎉")
    print()
    print("🎯 Next steps:")
    print("   1. 🔐 Set a secure SECRET_KEY in .env")
    print("   2. 👤 Create/update superuser: python manage.py createsuperuser")
    print("   3. 🌐 Configure web server (nginx/gunicorn)")
    print("   4. 🔒 Set up SSL certificate")
    print()
    print("🚀 Start server:")
    print("   gunicorn Project.wsgi:application --bind 0.0.0.0:8000")
    print()
    print("🐛 Debug tools:")
    print("   python scripts/3_security_tools.py debug --verbose")
    print("   python scripts/3_security_tools.py server")
    print("   python scripts/3_security_tools.py all")
    return 0


# ══════════════════════════════════════════════
# SUBCOMMAND: monitor  (từ security_monitor.py)
# ══════════════════════════════════════════════

def cmd_monitor(_args: argparse.Namespace) -> int:
    """Phân tích các truy cập đáng ngờ từ bảng PageView trong database."""
    _setup_django()

    from App_Core.models import PageView  # type: ignore[import]

    print("=" * 60)
    print("BÁO CÁO BẢO MẬT - PHÂN TÍCH TRUY CẬP ĐÁNG NGỜ")
    print("=" * 60)
    print(f"Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    all_views = list(PageView.objects.all().order_by("-view_count"))
    suspicious_views = [v for v in all_views if _is_suspicious(v.path)]
    normal_views = [v for v in all_views if not _is_suspicious(v.path)]

    print("📊 TỔNG QUAN:")
    print(f"   - Tổng số đường dẫn được truy cập: {len(all_views)}")
    print(f"   - Đường dẫn bình thường: {len(normal_views)}")
    print(f"   - Đường dẫn đáng ngờ: {len(suspicious_views)}")
    print()

    if suspicious_views:
        print("🚨 CÁC TRUY CẬP ĐÁNG NGỜ:")
        print("-" * 40)
        for view in suspicious_views[:20]:
            print(f"   {view.path}: {view.view_count} lượt truy cập")
        print()

        # Phân loại tấn công
        attack_types: dict[str, list] = {
            "PHP Files": [v for v in suspicious_views if ".php" in v.path.lower()],
            "Config Files": [v for v in suspicious_views if any(x in v.path.lower() for x in (".env", "config.php", "wp-config"))],
            "Admin Panels": [v for v in suspicious_views if any(x in v.path.lower() for x in ("admin", "wp-admin", "phpmyadmin"))],
            "API Endpoints": [v for v in suspicious_views if any(x in v.path.lower() for x in ("api", "swagger", "openapi"))],
            "Backup Files": [v for v in suspicious_views if any(x in v.path.lower() for x in ("backup", "dump", ".sql"))],
            "Log Files": [v for v in suspicious_views if any(x in v.path.lower() for x in ("log", "error", "access"))],
            "Docker/Dev Files": [v for v in suspicious_views if any(x in v.path.lower() for x in ("docker", ".git", ".svn"))],
            "Git/IDE Files": [v for v in suspicious_views if any(x in v.path.lower() for x in (".gitignore", ".cursorignore", ".vscode", ".idea"))],
            "SQL Files": [v for v in suspicious_views if any(x in v.path.lower() for x in (".sql", ".db", ".sqlite", "database.sql"))],
            "Credentials": [v for v in suspicious_views if any(x in v.path.lower() for x in ("credentials", "secrets", "aws", "ssh"))],
        }

        print("📈 PHÂN TÍCH THEO LOẠI TẤN CÔNG:")
        print("-" * 40)
        for attack_type, views in attack_types.items():
            if views:
                total = sum(v.view_count for v in views)
                print(f"   {attack_type}: {len(views)} đường dẫn, {total} lượt truy cập")
        print()

    print("🔥 TOP 10 ĐƯỜNG DẪN ĐƯỢC TRUY CẬP NHIỀU NHẤT:")
    print("-" * 40)
    for i, view in enumerate(all_views[:10], 1):
        status = "🚨" if view in suspicious_views else "✅"
        print(f"   {i:2d}. {status} {view.path}: {view.view_count} lượt")
    print()

    print("💡 KHUYẾN NGHỊ:")
    print("-" * 40)
    if suspicious_views:
        print("   ⚠️  Phát hiện truy cập đáng ngờ!")
        print("   🔒 Kiểm tra web server logs để xác định nguồn tấn công")
        print("   🛡️  Cân nhắc chặn IP địa chỉ đáng ngờ")
        print("   📊 Thiết lập monitoring real-time")
        print("   🔍 Kiểm tra file .htaccess hoặc nginx config")
    else:
        print("   ✅ Không phát hiện truy cập đáng ngờ")
        print("   🔒 Hệ thống đang được bảo vệ tốt")
        print("   📊 Tiếp tục monitoring định kỳ")
    print()
    print("=" * 60)
    return 0


# ══════════════════════════════════════════════
# SUBCOMMAND: logs  (từ check_logs.py)
# ══════════════════════════════════════════════

def cmd_logs(_args: argparse.Namespace) -> int:
    """Quét file log trên disk để tìm các dòng đáng ngờ."""
    print("🔒 SECURITY LOG ANALYZER")
    print("=" * 60)

    _check_django_logs()
    _check_web_server_logs()
    _generate_security_report()
    return 0


def _check_django_logs() -> None:
    print("🔍 KIỂM TRA DJANGO LOGS")
    print("-" * 40)

    log_dir = "logs"
    if not os.path.exists(log_dir):
        print("❌ Không tìm thấy thư mục logs")
        return

    log_files = glob.glob(os.path.join(log_dir, "*.log"))
    for log_file in log_files:
        print(f"\n📄 Kiểm tra file: {log_file}")
        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            suspicious_lines = [
                (i, line.strip())
                for i, line in enumerate(lines, 1)
                if _is_suspicious(line)
            ]

            if suspicious_lines:
                print(f"   🚨 Tìm thấy {len(suspicious_lines)} dòng đáng ngờ:")
                for line_num, content in suspicious_lines[:10]:
                    print(f"      Dòng {line_num}: {content[:100]}...")
            else:
                print("   ✅ Không tìm thấy dòng đáng ngờ")
        except Exception as exc:
            print(f"   ❌ Lỗi khi đọc file: {exc}")


def _check_web_server_logs() -> None:
    print("\n🌐 KIỂM TRA WEB SERVER LOGS")
    print("-" * 40)

    possible_locations = [
        "/var/log/apache2/access.log",
        "/var/log/apache2/error.log",
        "/var/log/nginx/access.log",
        "/var/log/nginx/error.log",
        "/var/log/httpd/access_log",
        "/var/log/httpd/error_log",
    ]

    found_logs = [loc for loc in possible_locations if os.path.exists(loc)]
    if not found_logs:
        print("❌ Không tìm thấy web server logs")
        print("💡 Có thể logs được lưu ở vị trí khác hoặc không có quyền truy cập")
        return

    for log_file in found_logs:
        print(f"\n📄 Kiểm tra file: {log_file}")
        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            recent = lines[-1000:] if len(lines) > 1000 else lines
            count = sum(1 for line in recent if _is_suspicious(line))
            print(f"   📊 Trong 1000 dòng gần nhất: {count} dòng đáng ngờ")
        except Exception as exc:
            print(f"   ❌ Lỗi khi đọc file: {exc}")


def _generate_security_report() -> None:
    print("\n" + "=" * 60)
    print("BÁO CÁO BẢO MẬT TỔNG HỢP")
    print("=" * 60)
    print(f"Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    print("📋 TÓM TẮT:")
    print("   - Đã kiểm tra Django logs")
    print("   - Đã kiểm tra web server logs (nếu có)")
    print("   - Đã phân tích các pattern đáng ngờ")
    print()

    print("🛡️  CÁC BIỆN PHÁP BẢO VỆ ĐÃ TRIỂN KHAI:")
    print("   ✅ SecurityMiddleware - chặn truy cập đáng ngờ")
    print("   ✅ PageViewMiddleware - theo dõi và log truy cập")
    print("   ✅ Django Security Settings - HTTPS, CSRF, XSS protection")
    print("   ✅ CORS Protection - chỉ cho phép domain tin cậy")
    print()

    print("🔍 KHUYẾN NGHỊ TIẾP THEO:")
    print("   1. Thiết lập fail2ban để tự động chặn IP đáng ngờ")
    print("   2. Cấu hình Cloudflare hoặc CDN để lọc traffic")
    print("   3. Thiết lập monitoring real-time với tools như Sentry")
    print("   4. Thường xuyên cập nhật Django và dependencies")
    print("   5. Backup dữ liệu định kỳ và test restore")


# ══════════════════════════════════════════════
# SUBCOMMAND: all
# ══════════════════════════════════════════════

def cmd_all(args: argparse.Namespace) -> int:
    """Chạy cả monitor lẫn logs rồi in báo cáo tổng hợp."""
    rc1 = cmd_logs(args)
    print()
    rc2 = cmd_monitor(args)
    return max(rc1, rc2)


# ══════════════════════════════════════════════
# SUBCOMMAND: refactor-audit
# ══════════════════════════════════════════════

def cmd_refactor_audit(args: argparse.Namespace) -> int:
    """Audit nhanh trạng thái sau khi tách legacy ecommerce app thành domain apps."""
    base_dir = Path(__file__).resolve().parent.parent
    issues: list[str] = []

    def ok(message: str) -> None:
        print(f"✅ {message}")

    def fail(message: str) -> None:
        issues.append(message)
        print(f"❌ {message}")

    def info(message: str) -> None:
        print(f"ℹ️  {message}")

    print("🔎 DOMAIN APP REFACTOR AUDIT")
    print("=" * 60)

    legacy_dir = base_dir / "App_ecom"
    if legacy_dir.exists():
        fail("Legacy directory still exists: App_ecom")
    else:
        ok("Legacy directory App_ecom is absent")

    backup_file = base_dir / "db.sqlite3.before_app_ecom_reset"
    if backup_file.exists():
        fail("Old reset backup still exists: db.sqlite3.before_app_ecom_reset")
    else:
        ok("Old reset DB backup is absent")

    runtime_hits: list[str] = []
    for path in _iter_runtime_text_files(base_dir):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            fail(f"Cannot read {path.relative_to(base_dir)}: {exc}")
            continue
        for marker in LEGACY_RUNTIME_MARKERS:
            if marker in text:
                runtime_hits.append(f"{path.relative_to(base_dir)} -> {marker}")

    if runtime_hits:
        fail("Legacy runtime references found:")
        for hit in runtime_hits[:30]:
            print(f"   - {hit}")
        if len(runtime_hits) > 30:
            print(f"   - ... and {len(runtime_hits) - 30} more")
    else:
        ok("No legacy runtime references found")

    for app_name in DOMAIN_APPS:
        app_dir = base_dir / app_name
        if app_dir.is_dir():
            ok(f"{app_name} directory exists")
        else:
            fail(f"{app_name} directory is missing")

        migration = app_dir / "migrations" / "0001_initial.py"
        if migration.exists():
            ok(f"{app_name} initial migration exists")
        else:
            fail(f"{app_name} initial migration is missing")

    if not getattr(args, "skip_django_check", False):
        try:
            _setup_django()
            from django.apps import apps
            from django.conf import settings
            from django.core.management import call_command

            installed_apps = set(getattr(settings, "INSTALLED_APPS", []))
            if "App_ecom" in installed_apps:
                fail("App_ecom is still present in INSTALLED_APPS")
            else:
                ok("App_ecom is absent from INSTALLED_APPS")

            missing_installed = [app for app in DOMAIN_APPS if app not in installed_apps]
            if missing_installed:
                fail(f"Domain apps missing from INSTALLED_APPS: {', '.join(missing_installed)}")
            else:
                ok("All domain apps are present in INSTALLED_APPS")

            missing_registry = [app for app in DOMAIN_APPS if not apps.is_installed(app)]
            if missing_registry:
                fail(f"Domain apps missing from Django app registry: {', '.join(missing_registry)}")
            else:
                ok("All domain apps are loaded in Django app registry")

            call_command("check", verbosity=0)
            ok("Django system check passed")
        except Exception as exc:
            fail(f"Django audit failed: {exc}")
    else:
        info("Skipped Django check")

    print("=" * 60)
    if issues:
        print(f"❌ Audit failed: {len(issues)} issue(s)")
        return 1
    print("✅ Audit passed")
    return 0


# ══════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="3_security_tools.py",
        description="Công cụ vận hành (production + security) Django tích hợp.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # production
    p_deploy = sub.add_parser("deploy", help="Chạy toàn bộ quy trình setup production")
    p_deploy.add_argument("--skip-backup", action="store_true", dest="skip_backup", help="Bỏ qua bước backup database")
    p_deploy.add_argument("--skip-debug", action="store_true", dest="skip_debug", help="Bỏ qua bước chạy debug check")
    p_deploy.add_argument("--quick", action="store_true", help="Quick mode: bỏ qua backup và debug")

    p_debug = sub.add_parser("debug", help="Kiểm tra toàn diện môi trường production")
    p_debug.add_argument("--check-only", action="store_true", dest="check_only", help="Chỉ kiểm tra, không sửa")
    p_debug.add_argument("--fix-common", action="store_true", dest="fix_common", help="Tự động sửa các lỗi phổ biến")
    p_debug.add_argument("--verbose", action="store_true", help="Hiển thị thông tin chi tiết")

    sub.add_parser("server", help="Debug lỗi 500 server errors")

    # security
    sub.add_parser("monitor", help="Phân tích PageView records từ database")
    sub.add_parser("logs", help="Quét file log trên disk")
    sub.add_parser("all", help="Chạy monitor + logs")

    p_refactor = sub.add_parser("refactor-audit", help="Audit trạng thái sau khi tách domain app")
    p_refactor.add_argument("--skip-django-check", action="store_true", help="Chỉ scan file, không setup Django")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    dispatch = {
        "deploy": cmd_deploy,
        "debug": cmd_debug,
        "server": cmd_server,
        "monitor": cmd_monitor,
        "logs": cmd_logs,
        "all": cmd_all,
        "refactor-audit": cmd_refactor_audit,
    }
    sys.exit(dispatch[args.command](args))


if __name__ == "__main__":
    main()
