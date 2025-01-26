import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    """
    Настраивает логирование: создаёт папку logs/, файлы для debug и warning
    с ротацией при достижении размера, в данном случае 5 мб.
    """
    # Ставим путь к логам, меняем если нужно
    log_dir = "C:/Project/api/logs"

    # Проверяем доступность (что диск существует)
    drive = os.path.splitdrive(log_dir)[0]
    if drive and not os.path.exists(drive):
        raise FileNotFoundError(f"Drive not found: {drive}")

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

    # debug_info: пишем только DEBUG и INFO (максимум INFO)
    debug_info_handler = RotatingFileHandler(
        os.path.join(log_dir, 'debug_info.log'),
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,            # Храним до 3 старых файлов
        encoding='utf-8'
    )
    debug_info_handler.setLevel(logging.DEBUG)
    # Фильтр: если уровень >= WARNING, пусть летит в другой файл
    def debug_filter(record: logging.LogRecord):
        return record.levelno < logging.WARNING
    debug_info_handler.addFilter(debug_filter)
    debug_info_handler.setFormatter(formatter)

    # warning_error_critical
    warn_err_handler = RotatingFileHandler(
        os.path.join(log_dir, 'warning_error_critical.log'),
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding='utf-8'
    )
    warn_err_handler.setLevel(logging.WARNING)
    warn_err_handler.setFormatter(formatter)

    logger.addHandler(debug_info_handler)
    logger.addHandler(warn_err_handler)

    return logger
