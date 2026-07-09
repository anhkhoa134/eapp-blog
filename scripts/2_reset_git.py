"""
Các lệnh sử dụng nhanh:

1. Chỉ xoá .git cũ, tạo repo Git mới, commit lại code hiện tại, không push:
   python3 scripts/2_reset_git.py --skip-push

2. Reset Git và push ghi đè lịch sử remote GitHub cũ:
   python3 scripts/2_reset_git.py --remote-url https://github.com/anhkhoa134/eApp.git --remote-name origin --branch main

3. Reset Git, không hỏi tương tác, không push nếu thiếu --remote-url:
   python3 scripts/2_reset_git.py --skip-push --non-interactive

4. Nếu thật sự cần fetch remote trước khi push:
   python3 scripts/2_reset_git.py --remote-url https://github.com/anhkhoa134/eApp.git --fetch-before-push

5. Chỉ dọn .git hiện tại, không xoá lịch sử/không init lại:
   python3 scripts/2_reset_git.py --cleanup-only

Ghi chú:
- Mặc định script KHÔNG fetch remote để tránh kéo lịch sử Git cũ về .git.
- Mặc định push dùng --force để ghi đè lịch sử remote bằng commit mới.
- Script sẽ xoá cache công cụ trong .git/cursor nếu có, vì đây không phải dữ liệu Git chuẩn
  và thường chiếm nhiều dung lượng cục bộ.
- Muốn giảm mạnh dung lượng .git, hãy đảm bảo .gitignore đã loại runtime artifacts
  không cần commit, ví dụ: staticfiles/, media/, logs/, backup/, db.sqlite3, db.sqlite3.*.
"""

import shutil
import subprocess
from pathlib import Path
import argparse
from typing import Optional
import fnmatch

def _human_size(num_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    for u in units:
        if size < 1024 or u == units[-1]:
            if u == "B":
                return f"{int(size)} {u}"
            return f"{size:.2f} {u}"
        size /= 1024
    return f"{num_bytes} B"


def _dir_size_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        try:
            return path.stat().st_size
        except OSError:
            return 0
    total = 0
    for p in path.rglob("*"):
        if p.is_file():
            try:
                total += p.stat().st_size
            except OSError:
                continue
    return total


def _print_sizes(project_root: Path) -> None:
    git_dir = project_root / ".git"
    project_size = _dir_size_bytes(project_root)
    git_size = _dir_size_bytes(git_dir)
    git_objects_size = _dir_size_bytes(git_dir / "objects")
    git_pack_size = _dir_size_bytes(git_dir / "objects" / "pack")
    git_cursor_size = _dir_size_bytes(git_dir / "cursor")
    print("📦 Dung lượng hiện tại:")
    print(f"   - Project: {_human_size(project_size)}")
    print(f"   - .git/:  {_human_size(git_size)}")
    if git_dir.exists():
        print(f"     - .git/objects/:      {_human_size(git_objects_size)}")
        print(f"     - .git/objects/pack/: {_human_size(git_pack_size)}")
        print(f"     - .git/cursor/:       {_human_size(git_cursor_size)}")


def _remove_git_temp_pack_files(project_root: Path) -> None:
    """
    Dọn các file pack tạm còn sót lại nếu git fetch/push/gc bị ngắt giữa chừng.
    Chỉ xoá file tạm trong .git/objects/pack, không xoá pack hợp lệ.
    """
    pack_dir = project_root / ".git" / "objects" / "pack"
    if not pack_dir.exists():
        return

    removed = 0
    removed_bytes = 0
    for path in pack_dir.iterdir():
        if not path.is_file():
            continue
        if not fnmatch.fnmatch(path.name, "tmp_pack_*"):
            continue
        try:
            size = path.stat().st_size
            path.unlink()
            removed += 1
            removed_bytes += size
        except OSError as exc:
            print(f"    -> Không xoá được file pack tạm {path.name}: {exc}")

    if removed:
        print(f"    -> Đã xoá {removed} file pack tạm ({_human_size(removed_bytes)}).")


def _remove_git_tool_caches(project_root: Path) -> None:
    """
    Xoá cache/index của công cụ nằm trong .git nhưng không phải dữ liệu Git chuẩn.
    Cursor có thể tạo lại .git/cursor sau đó; xoá thư mục này không làm mất lịch sử Git.
    """
    git_dir = project_root / ".git"
    cache_dirs = [
        git_dir / "cursor",
    ]

    for cache_dir in cache_dirs:
        if not cache_dir.exists():
            continue

        size = _dir_size_bytes(cache_dir)
        try:
            shutil.rmtree(cache_dir)
            print(f"    -> Đã xoá cache công cụ {cache_dir.relative_to(project_root)} ({_human_size(size)}).")
        except OSError as exc:
            print(f"    -> Không xoá được cache công cụ {cache_dir.relative_to(project_root)}: {exc}")


def _run_git_cleanup(project_root: Path) -> None:
    """
    Gom pack, expire reflog và prune object không còn được tham chiếu sau khi reset/push.
    """
    _remove_git_temp_pack_files(project_root)
    _remove_git_tool_caches(project_root)

    cleanup_commands = [
        ["git", "reflog", "expire", "--expire=now", "--expire-unreachable=now", "--all"],
        ["git", "repack", "-Ad"],
        ["git", "prune", "--expire=now"],
        ["git", "gc", "--prune=now", "--aggressive"],
    ]

    try:
        for cmd in cleanup_commands:
            subprocess.run(cmd, cwd=project_root, check=True)
        _remove_git_temp_pack_files(project_root)
        _remove_git_tool_caches(project_root)
    except subprocess.CalledProcessError as exc:
        print(f"    -> CẢNH BÁO: git cleanup không hoàn tất: {exc}")


def _warn_if_git_still_large(project_root: Path, threshold_mb: int = 30) -> None:
    git_dir = project_root / ".git"
    git_size = _dir_size_bytes(git_dir)
    threshold_bytes = threshold_mb * 1024 * 1024
    if git_size <= threshold_bytes:
        return

    print(
        f"    -> CẢNH BÁO: .git vẫn còn lớn ({_human_size(git_size)}). "
        "Có thể file lớn vẫn đang được commit hoặc Cursor vừa tạo lại cache."
    )
    for child in sorted(git_dir.iterdir(), key=_dir_size_bytes, reverse=True)[:5]:
        print(f"       - {child.relative_to(project_root)}: {_human_size(_dir_size_bytes(child))}")


def cleanup_current_git(project_root: Path) -> int:
    """
    Dọn .git hiện tại mà không xoá repo, không init lại và không thay đổi commit history.
    """
    git_dir = project_root / ".git"
    if not git_dir.exists():
        print("[cleanup] Không tìm thấy .git, không có gì để dọn.")
        return 0

    print(f"[*] Bắt đầu dọn .git hiện tại tại: {project_root}")
    _print_sizes(project_root)
    print("[cleanup] Đang dọn cache công cụ, reflog, pack và object không dùng...")
    _run_git_cleanup(project_root)
    _print_sizes(project_root)
    _warn_if_git_still_large(project_root)
    return 0



def _get_existing_remotes(project_root: Path) -> dict[str, str]:
    """
    Lấy danh sách remote hiện có (tên -> url) từ repo *trước khi* reset.
    Trả về rỗng nếu không phải repo git hoặc không đọc được.
    """
    def parse_remote_v(output: str) -> dict[str, str]:
        remotes: dict[str, str] = {}
        for raw in (output or "").splitlines():
            # Format: origin  https://... (fetch)
            parts = raw.split()
            if len(parts) < 3:
                continue
            name, url, kind = parts[0], parts[1], parts[2]
            if kind != "(fetch)":
                continue
            remotes[name] = url
        return remotes

    # 1) Ưu tiên: git remote -v (dễ hiểu, đúng định dạng)
    try:
        proc = subprocess.run(
            ["git", "remote", "-v"],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
        )
        remotes = parse_remote_v(proc.stdout or "")
        if remotes:
            return remotes
    except subprocess.CalledProcessError:
        pass

    # 2) Fallback: đọc trực tiếp từ git config (ổn định hơn nếu remote -v bị lỗi/khác format)
    try:
        cfg = subprocess.run(
            ["git", "config", "--local", "--get-regexp", r"^remote\..*\.url$"],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        return {}

    remotes: dict[str, str] = {}
    for raw in (cfg.stdout or "").splitlines():
        # Format: remote.origin.url https://...
        key, *rest = raw.split()
        if not rest:
            continue
        url = rest[0]
        if not key.startswith("remote.") or not key.endswith(".url"):
            continue
        name = key[len("remote.") : -len(".url")]
        if name:
            remotes[name] = url
    return remotes


def _prompt_yes_no(question: str, default_yes: bool = True) -> bool:
    suffix = " [Y/n] " if default_yes else " [y/N] "
    ans = input(question + suffix).strip().lower()
    if not ans:
        return default_yes
    return ans in ("y", "yes")


def _choose_remote_interactive(existing_remotes: dict[str, str]) -> tuple[Optional[str], Optional[str]]:
    """
    Trả về (remote_name, remote_url) hoặc (None, None) nếu không chọn push.
    """
    if existing_remotes:
        default_name = next(iter(existing_remotes.keys()))
        default_url = existing_remotes.get(default_name, "")
        if _prompt_yes_no(
            f"[5] Push và ghi đè lịch sử remote đang có ({default_name} -> {default_url}) không?",
            default_yes=False,
        ):
            if len(existing_remotes) == 1:
                return default_name, existing_remotes[default_name]

            print("    Danh sách remote đang có:")
            for i, (name, url) in enumerate(existing_remotes.items(), start=1):
                print(f"    {i}. {name} -> {url}")
            chosen = input(f"    Chọn remote name (Enter để dùng '{default_name}'): ").strip()
            chosen_name = chosen or default_name
            if chosen_name in existing_remotes:
                return chosen_name, existing_remotes[chosen_name]
            print("    -> Remote name không hợp lệ, bỏ qua chọn remote cũ.")

    url = input("[5] Nhập remote URL để push (Enter để không push): ").strip()
    if not url:
        return None, None
    name = input("[5] Nhập remote name (mặc định: origin): ").strip() or "origin"
    return name, url


def reset_git_repository(
    remote_url: Optional[str],
    remote_name: Optional[str],
    branch: str,
    force_mode: str,
    skip_push: bool,
    fetch_before_push: bool,
    interactive: bool = True,
) -> int:
    """
    1. Xóa thư mục .git đi.
    2. Chạy git init lại từ đầu.
    3. Áp dụng .gitignore.
    4. Commit lại toàn bộ code hiện tại.
    5. Dọn pack tạm/gc.
    6. (Tuỳ chọn) Thêm remote và push lại, mặc định không fetch lịch sử cũ.
    """
    project_root = Path(__file__).resolve().parent.parent
    git_dir = project_root / '.git'
    gitignore_file = project_root / '.gitignore'

    print(f"[*] Bắt đầu reset git repository tại: {project_root}")
    _print_sizes(project_root)

    existing_remotes = _get_existing_remotes(project_root)
    if existing_remotes:
        print("[*] Remote phát hiện (trước khi reset):")
        for name, url in existing_remotes.items():
            print(f"    - {name} -> {url}")
    else:
        print("[*] Không phát hiện remote nào (trước khi reset).")

    # 1. Xóa thư mục .git
    if git_dir.exists() and git_dir.is_dir():
        print("[1] Đang xóa thư mục .git cũ...")
        try:
            shutil.rmtree(git_dir)
            print("    -> Đã xóa thành công.")
            _print_sizes(project_root)
        except Exception as e:
            print(f"    -> Lỗi khi xóa thư mục .git: {e}")
            return 1
    else:
        print("[1] Thư mục .git không tồn tại, bỏ qua bước xóa.")

    # 2. Chạy git init
    print("[2] Đang khởi tạo lại git (git init)...")
    try:
        subprocess.run(['git', 'init'], cwd=project_root, check=True)
        print("    -> Đã khởi tạo xong.")
    except subprocess.CalledProcessError as e:
        print(f"    -> Lỗi khi khởi tạo git: {e}")
        return 1

    # 3. Đảm bảo .gitignore
    print("[3] Kiểm tra .gitignore...")
    if gitignore_file.exists():
        print("    -> Tệp .gitignore đã tồn tại.")
    else:
        print("    -> CẢNH BÁO: Tệp .gitignore không tồn tại trong thư mục gốc.")

    # 4. Add và commit toàn bộ code
    print("[4] Thêm file và commit toàn bộ code hiện tại...")
    try:
        subprocess.run(['git', 'add', '.'], cwd=project_root, check=True)
        commit_msg = "Initial commit (repository reset)"
        subprocess.run(['git', 'commit', '-m', commit_msg], cwd=project_root, check=True)
        print(f"    -> Đã commit thành công với message: '{commit_msg}'")
        print("    -> Đang dọn pack tạm và object không dùng...")
        _run_git_cleanup(project_root)

        if skip_push:
            print("[5] Bỏ qua bước push theo tuỳ chọn --skip-push.")
            _print_sizes(project_root)
            _warn_if_git_still_large(project_root)
            return 0

        chosen_remote_name: Optional[str] = remote_name
        chosen_remote_url: Optional[str] = remote_url

        # Nếu user không truyền remote_url, mặc định hỏi theo flow:
        # 1) push lên remote đang có (trước khi reset)
        # 2) nếu không thì nhập URL mới
        # 3) nếu vẫn trống thì không push
        if not chosen_remote_url and interactive:
            chosen_remote_name, chosen_remote_url = _choose_remote_interactive(existing_remotes)

        if not chosen_remote_url:
            print("[5] Không có remote URL, bỏ qua bước push.")
            return 0

        if not chosen_remote_name:
            chosen_remote_name = "origin"

        print(f"[5] Thiết lập branch '{branch}', thêm remote và push lên server...")
        subprocess.run(['git', 'branch', '-M', branch], cwd=project_root, check=True)

        # Thêm remote (xoá nếu tồn tại để tránh lỗi)
        subprocess.run(
            ['git', 'remote', 'remove', chosen_remote_name],
            cwd=project_root,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        subprocess.run(['git', 'remote', 'add', chosen_remote_name, chosen_remote_url], cwd=project_root, check=True)

        if fetch_before_push:
            print("    -> Đang fetch remote trước khi push (--fetch-before-push).")
            subprocess.run(['git', 'fetch', '--prune', chosen_remote_name], cwd=project_root, check=False)
        elif force_mode == "with-lease":
            print("    -> CẢNH BÁO: --force-with-lease có thể fail nếu chưa có thông tin remote.")
            print("       Script sẽ KHÔNG fetch mặc định để tránh kéo lịch sử cũ về .git.")

        push_cmd = ['git', 'push', '-u', chosen_remote_name, branch]
        if force_mode == "force":
            push_cmd.append('--force')
        elif force_mode == "with-lease":
            push_cmd.append('--force-with-lease')

        subprocess.run(push_cmd, cwd=project_root, check=True)
        print(f"    -> Đã push thành công lên remote '{chosen_remote_name}' branch '{branch}'!")
        print("    -> Đang dọn pack tạm và object không dùng sau push...")
        _run_git_cleanup(project_root)
        _print_sizes(project_root)
        _warn_if_git_still_large(project_root)

    except subprocess.CalledProcessError as e:
        print(f"    -> Lỗi khi commit/push code: {e}")
        return 1
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reset git repo (xoá .git), init lại, commit và push lại.")
    parser.add_argument(
        "--remote-url",
        default=None,
        help="Remote URL để push lại. Nếu bỏ trống và không dùng --skip-push, script sẽ hỏi interactive.",
    )
    parser.add_argument("--remote-name", default=None, help="Tên remote (mặc định: origin nếu có push).")
    parser.add_argument("--branch", default="main", help="Tên branch để push (mặc định: main).")
    parser.add_argument(
        "--force",
        choices=["none", "with-lease", "force"],
        default="force",
        help="Chế độ force push: none | with-lease | force (mặc định: force để ghi đè lịch sử remote cũ).",
    )
    parser.add_argument("--skip-push", action="store_true", help="Chỉ reset/init/commit, không push.")
    parser.add_argument(
        "--cleanup-only",
        action="store_true",
        help="Chỉ dọn .git hiện tại, không xoá .git, không init lại, không commit/push.",
    )
    parser.add_argument(
        "--fetch-before-push",
        action="store_true",
        help="Fetch remote trước khi push. Mặc định tắt để không kéo lịch sử cũ về .git.",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Không hỏi interactive. Nếu thiếu --remote-url thì sẽ không push.",
    )

    args = parser.parse_args()
    project_root = Path(__file__).resolve().parent.parent
    if args.cleanup_only:
        raise SystemExit(cleanup_current_git(project_root))

    raise SystemExit(
        reset_git_repository(
            remote_url=args.remote_url,
            remote_name=args.remote_name,
            branch=args.branch,
            force_mode=args.force,
            skip_push=args.skip_push,
            fetch_before_push=args.fetch_before_push,
            interactive=not args.non_interactive,
        )
    )
