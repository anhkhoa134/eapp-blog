#!/usr/bin/env python3
"""
Reset dev DB/artifacts và seed dữ liệu domain apps.

Các lệnh hay dùng, chạy từ thư mục gốc repo:

  # Xem trước mọi thao tác, không xoá/sửa file
  python scripts/1_reset_fresh.py --dry-run

  # Reset sạch local, migrate, hỏi trước khi tạo superadmin/quanly, rồi seed data
  python scripts/1_reset_fresh.py

  # Reset nhưng giữ media/logs upload hiện có
  python scripts/1_reset_fresh.py --keep-media --keep-logs

  # Reset/migrate nhưng không seed data và không hỏi tạo account seed
  python scripts/1_reset_fresh.py --skip-seed

  # Không reset/migrate, chỉ chạy seed data
  python scripts/1_reset_fresh.py --seed-only

  # Giữ DB hiện tại, chỉ dọn migration/cache/staticfiles rồi chạy migrate/seed
  python scripts/1_reset_fresh.py --keep-db

Script sẽ xoá: migrations (trừ __init__.py), __pycache__, db.sqlite3,
db.sqlite3.*, db.sqlite3-*, staticfiles collected, media/ và logs/ (mặc định).

Sau migrate, nếu không dùng --skip-seed:
  1. Hỏi xác nhận trước khi tạo/cập nhật account seed superadmin.
  2. Hỏi xác nhận trước khi tạo/cập nhật account seed quanly.
  3. Chạy seed_posts.

Account seed có password mặc định 123456 khi bạn xác nhận tạo/cập nhật.
Cuối script in SECRET_KEY mới để copy vào .env.
"""
from __future__ import annotations

import argparse
import os
import secrets
import shutil
import string
import subprocess
import sys
from pathlib import Path


# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────

SKIP_DIR_NAMES = frozenset({
    ".git", ".hg", ".svn", "venv", ".venv", "node_modules",
    "site-packages", ".tox", "__pypackages__",
})


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def django_style_secret_key() -> str:
    """Giống django.core.management.utils.get_random_secret_key (50 ký tự)."""
    alphabet = string.ascii_lowercase + string.digits + "!@#$%^&*(-_=+)"
    return "".join(secrets.choice(alphabet) for _ in range(50))


def should_skip_tree(path: Path) -> bool:
    return bool(set(path.parts) & SKIP_DIR_NAMES)


def iter_migrations_dirs(root: Path) -> list[Path]:
    found: list[Path] = []
    for dirpath, dirnames, _ in os.walk(root, topdown=True):
        p = Path(dirpath)
        if should_skip_tree(p):
            dirnames[:] = []
            continue
        if p.name == "migrations" and (p.parent / "__init__.py").exists():
            found.append(p)
    return found


def rm_tree(path: Path, dry_run: bool) -> None:
    if not path.exists():
        return
    if dry_run:
        print(f"  [dry-run] would remove: {path}")
        return
    shutil.rmtree(path) if path.is_dir() else path.unlink()


def clear_migrations(migrations_dir: Path, dry_run: bool) -> int:
    removed = 0
    for f in sorted(migrations_dir.glob("*.py")):
        if f.name == "__init__.py":
            continue
        if dry_run:
            print(f"  [dry-run] would remove: {f}")
        else:
            f.unlink()
        removed += 1
    init_py = migrations_dir / "__init__.py"
    if not dry_run and not init_py.exists():
        init_py.write_text("")
        print(f"  created empty: {init_py}")
    return removed


def remove_pycache(root: Path, dry_run: bool) -> int:
    count = 0
    for dirpath, dirnames, _ in os.walk(root, topdown=True):
        p = Path(dirpath)
        if should_skip_tree(p):
            dirnames[:] = []
            continue
        if p.name == "__pycache__":
            rm_tree(p, dry_run)
            dirnames[:] = []
            count += 1
    return count


def prompt_yes_no(question: str, default: bool = False) -> bool:
    """Prompt xác nhận. Non-interactive thì luôn dùng default."""
    suffix = " [Y/n] " if default else " [y/N] "
    if not sys.stdin.isatty():
        print(f"{question}{suffix}{'yes' if default else 'no'} (non-interactive)")
        return default
    answer = input(question + suffix).strip().lower()
    if not answer:
        return default
    return answer in {"y", "yes"}


def run_seed_data(base_dir: Path, manage_py: Path, dry_run: bool) -> None:
    if dry_run:
        print("(dry-run) would ask: create/update seed account superadmin?")
        print("(dry-run) would ask: create/update seed account quanly?")
        print(f"(dry-run) would run: {sys.executable} manage.py shell -c <create confirmed seed accounts>")
        for command in ("seed_posts",):
            print(f"(dry-run) would run: {sys.executable} manage.py {command}")
        print()
        return

    print("\n🌱 Seeding domain app data...")
    create_superadmin = prompt_yes_no(
        "Tạo/cập nhật tài khoản seed superadmin (password 123456)?",
        default=False,
    )
    create_quanly = prompt_yes_no(
        "Tạo/cập nhật tài khoản seed quanly (password 123456)?",
        default=False,
    )

    if create_superadmin or create_quanly:
        # (username, email, is_staff, is_superuser). Trang /quan-ly/ chỉ kiểm tra
        # username qua decorator quanly_required nên account quanly không được
        # cấp quyền vào Django admin.
        accounts: list[tuple[str, str, bool, bool]] = []
        if create_superadmin:
            accounts.append(("superadmin", "superadmin@example.com", True, True))
        if create_quanly:
            accounts.append(("quanly", "quanly@example.com", False, False))

        account_lines = [
            "from django.contrib.auth import get_user_model",
            "User=get_user_model()",
            f"accounts={accounts!r}",
            "for username,email,is_staff,is_superuser in accounts:",
            "    user,created=User.objects.get_or_create(username=username, defaults={'email': email})",
            "    user.email=email",
            "    user.is_staff=is_staff",
            "    user.is_superuser=is_superuser",
            "    user.set_password('123456')",
            "    user.save()",
            "    print(('Created' if created else 'Updated') + f' seed account: {username}')",
        ]
        subprocess.run(
            [sys.executable, str(manage_py), "shell", "-c", "\n".join(account_lines)],
            cwd=base_dir,
            check=True,
        )
    else:
        print("Skipped creating seed accounts.")

    seed_commands = (
        ("seed_posts",),
    )
    try:
        for command_args in seed_commands:
            subprocess.run([sys.executable, str(manage_py), *command_args], cwd=base_dir, check=True)
        print("✅ Seed data completed.")
        if create_superadmin:
            print("   Seed account: username=superadmin, password=123456")
        if create_quanly:
            print("   Seed account: username=quanly, password=123456")
    except subprocess.CalledProcessError as exc:
        print(f"❌ Lỗi khi chạy seed data: {exc}")
        raise SystemExit(1)


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reset local Django dev artifacts + print SECRET_KEY mới."
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Chỉ in việc sẽ làm, không xoá.")
    parser.add_argument("--keep-db", action="store_true",
                        help="Giữ file db.sqlite3.")
    parser.add_argument("--keep-media", action="store_true",
                        help="Giữ thư mục media/.")
    parser.add_argument("--keep-logs", action="store_true",
                        help="Giữ thư mục logs/.")
    parser.add_argument("--skip-seed", action="store_true",
                        help="Không tạo admin seed và không chạy seed data sau migrate.")
    parser.add_argument("--seed-only", action="store_true",
                        help="Không reset/migrate; chỉ chạy seed data.")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent.parent
    manage_py = base_dir / "manage.py"
    if not manage_py.exists():
        print(f"❌ Không tìm thấy manage.py tại: {manage_py}")
        raise SystemExit(1)

    print(f"BASE_DIR: {base_dir}")
    if args.dry_run:
        print("(dry-run — không thay đổi file)\n")
    if args.seed_only and args.skip_seed:
        print("❌ Không thể dùng đồng thời --seed-only và --skip-seed.")
        raise SystemExit(1)

    if args.seed_only:
        if not args.dry_run:
            (base_dir / "logs").mkdir(parents=True, exist_ok=True)
        run_seed_data(base_dir, manage_py, args.dry_run)
        return

    # ── Migrations ──
    total_mig = 0
    for mig in iter_migrations_dirs(base_dir):
        n = clear_migrations(mig, args.dry_run)
        if n:
            print(f"Migrations cleared ({n} files): {mig}")
        total_mig += n
    if total_mig == 0:
        print("Không tìm thấy file migration .py nào để xoá (ngoài __init__.py).")

    # ── __pycache__ ──
    n_cache = remove_pycache(base_dir, args.dry_run)
    print(f"__pycache__ folders removed: {n_cache}")

    # ── Extra caches ──
    for name in (".pytest_cache", ".mypy_cache", ".ruff_cache", ".hypothesis"):
        d = base_dir / name
        if d.is_dir():
            rm_tree(d, args.dry_run)
            if not args.dry_run:
                print(f"Removed cache dir: {d}")

    # ── SQLite ──
    db_related = {base_dir / "db.sqlite3"}
    db_related.update(base_dir.glob("db.sqlite3.*"))
    db_related.update(base_dir.glob("db.sqlite3-*"))
    for db_path in sorted(db_related):
        if not db_path.exists():
            continue
        if args.keep_db:
            print(f"Kept (--keep-db): {db_path}")
            continue
        rm_tree(db_path, args.dry_run)
        if not args.dry_run:
            print(f"Removed: {db_path}")

    # ── Staticfiles collected ──
    static_root = base_dir / "staticfiles"
    if static_root.is_dir():
        rm_tree(static_root, args.dry_run)
        if not args.dry_run:
            print(f"Removed collected static: {static_root}")

    # ── Media (mặc định xoá) ──
    if not args.keep_media:
        media = base_dir / "media"
        if media.is_dir():
            rm_tree(media, args.dry_run)
            if not args.dry_run:
                print(f"Removed media: {media}")
    else:
        print("Kept (--keep-media): media/")

    # ── Logs (mặc định xoá) ──
    if not args.keep_logs:
        logs = base_dir / "logs"
        if logs.is_dir():
            rm_tree(logs, args.dry_run)
            if not args.dry_run:
                print(f"Removed logs: {logs}")
    else:
        print("Kept (--keep-logs): logs/")

    # Django LOGGING trong settings đang dùng FileHandler tới BASE_DIR/logs/*.log
    # nên cần đảm bảo thư mục logs/ tồn tại trước khi chạy manage.py.
    if not args.dry_run:
        logs_dir = base_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

    # ── Re-run migrations (mặc định) ──
    if args.dry_run:
        print(f"\n(dry-run) would run: {sys.executable} manage.py makemigrations")
        print(f"(dry-run) would run: {sys.executable} manage.py migrate")
        print(f"(dry-run) would run: {sys.executable} manage.py collectstatic --noinput\n")
        if not args.skip_seed:
            run_seed_data(base_dir, manage_py, args.dry_run)
    else:
        print("\n🔄 Re-running migrations...")
        try:
            subprocess.run([sys.executable, str(manage_py), "makemigrations"], cwd=base_dir, check=True)
            subprocess.run([sys.executable, str(manage_py), "migrate"], cwd=base_dir, check=True)
            print("✅ Migrations completed.")
        except subprocess.CalledProcessError as exc:
            print(f"❌ Lỗi khi chạy migrations: {exc}")
            raise SystemExit(1)

        print("\n📦 Collecting static files...")
        try:
            subprocess.run([sys.executable, str(manage_py), "collectstatic", "--noinput"], cwd=base_dir, check=True)
            print("✅ Static manifest rebuilt.")
        except subprocess.CalledProcessError as exc:
            print(f"❌ Lỗi khi chạy collectstatic: {exc}")
            raise SystemExit(1)

        if not args.skip_seed:
            run_seed_data(base_dir, manage_py, args.dry_run)
        else:
            print("\nSkipped seed data (--skip-seed).")

    # ── SECRET_KEY mới (in cuối cùng) ──
    key = django_style_secret_key()
    print()
    print("--- SECRET_KEY mới (copy vào .env) ---")
    print(f"SECRET_KEY={key}")
    print("---")


if __name__ == "__main__":
    main()
