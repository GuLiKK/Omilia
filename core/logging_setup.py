import logging
import os

def setup_logging():
    """
    Настраивает логирование: создаёт папку logs/, файлы для debug и warning
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
    debug_info_handler = logging.FileHandler(os.path.join(log_dir, 'debug_info.log'))
    debug_info_handler.setLevel(logging.DEBUG)
    # Фильтр: если уровень >= WARNING, пусть летит в другой файл
    def debug_filter(record: logging.LogRecord):
        return record.levelno < logging.WARNING
    debug_info_handler.addFilter(debug_filter)
    debug_info_handler.setFormatter(formatter)

    # warning_error_critical
    warn_err_handler = logging.FileHandler(os.path.join(log_dir, 'warning_error_critical.log'))
    warn_err_handler.setLevel(logging.WARNING)
    warn_err_handler.setFormatter(formatter)

    logger.addHandler(debug_info_handler)
    logger.addHandler(warn_err_handler)

    return logger
