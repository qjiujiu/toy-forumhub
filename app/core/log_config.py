import os
import time
import logging
import colorlog

_LOG_FORMAT = "[%(asctime)s] %(levelname)s - %(pathname)s[line:%(lineno)d]: %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def config_logging(log_level=logging.INFO, is_console=True, is_file=True, is_colorful=True):
    """全局日志样式配置。在应用启动时调用一次，所有模块的 logging.getLogger(__name__) 自动继承此配置。"""
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 每次调用先清除已有 handler，防止重复
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)
    colorful_formatter = colorlog.ColoredFormatter(
        "%(log_color)s" + _LOG_FORMAT,
        datefmt=_DATE_FORMAT,
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    )

    if is_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(colorful_formatter if is_colorful else formatter)
        console_handler.setLevel(log_level)
        root_logger.addHandler(console_handler)

    if is_file:
        log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(
            os.path.join(log_dir, f"{time.strftime('%Y%m%d')}.log")
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
