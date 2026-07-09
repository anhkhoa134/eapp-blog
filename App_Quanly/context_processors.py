import logging

from App_Quanly.models import QuanlyMenuConfig

logger = logging.getLogger(__name__)


def quanly_menu(request):
    # Chỉ nạp cấu hình menu cho các trang quản lý, tránh query thừa ở trang public.
    if not (request.path.startswith('/quan-ly') or request.path.startswith('/quanly')):
        return {}
    try:
        config = QuanlyMenuConfig.load()
    except Exception:
        logger.exception("Quanly menu config error")
        config = QuanlyMenuConfig()
    return {'menu_config': config}
