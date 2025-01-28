import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    """
      1) debug_info.log — пишет уровни ниже WARNING (DEBUG и INFO).
      2) error_critical.log — пишет уровни ERROR и CRITICAL.
      3) admin_actions.log — отдельный лог для действий админов (WARNING).
    """
    log_dir = "C:/Project/api/logs"

    # Проверяем существование диска
    drive = os.path.splitdrive(log_dir)[0]
    if drive and not os.path.exists(drive):
        raise FileNotFoundError(f"Drive not found: {drive}")

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')

    # 1) Логер: debug_info (DEBUG + INFO) -----
    debug_info_handler = RotatingFileHandler(
        os.path.join(log_dir, 'debug_info.log'),
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding='utf-8'
    )
    debug_info_handler.setLevel(logging.DEBUG)

    # Фильтр, чтобы отсечь WARNING и выше
    def debug_info_filter(record: logging.LogRecord):
        return record.levelno < logging.WARNING

    debug_info_handler.addFilter(debug_info_filter)
    debug_info_handler.setFormatter(formatter)
    logger.addHandler(debug_info_handler)

    # 2) Логер: error_critical (ERROR, CRITICAL) -----
    error_critical_handler = RotatingFileHandler(
        os.path.join(log_dir, 'error_critical.log'),
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding='utf-8'
    )
    error_critical_handler.setLevel(logging.ERROR)
    error_critical_handler.setFormatter(formatter)
    logger.addHandler(error_critical_handler)


    # 3) Логгер для админских действий (admin_actions)
    admin_logger = logging.getLogger("admin_actions")
    admin_logger.setLevel(logging.WARNING)
    admin_logger.propagate = False

    admin_actions_handler = RotatingFileHandler(
        os.path.join(log_dir, 'admin_actions.log'),
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding='utf-8'
    )
    admin_actions_handler.setLevel(logging.WARNING)
    admin_actions_handler.setFormatter(formatter)

    admin_logger.addHandler(admin_actions_handler)

    return logger
