import ctypes
import datetime as dt
import logging
import os
import sys
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

LOG_DIR = Path("log")
LOG_FILE = LOG_DIR / "bot_log.log"

RESET = "\033[0m"
DIM = "\033[2m"
COLORS = {
    "DEBUG": "\033[36m",
    "INFO": "\033[32m",
    "WARNING": "\033[33m",
    "ERROR": "\033[31m",
    "CRITICAL": "\033[1;31m",
}


def resolve_timezone():
    for zone_name in ("Europe/Kyiv", "Europe/Kiev"):
        try:
            return ZoneInfo(zone_name)
        except ZoneInfoNotFoundError:
            continue

    try:
        import pytz

        for zone_name in ("Europe/Kyiv", "Europe/Kiev"):
            try:
                return pytz.timezone(zone_name)
            except Exception:
                continue
    except Exception:
        pass

    return dt.datetime.now().astimezone().tzinfo or dt.timezone.utc


KYIV_TZ = resolve_timezone()


def enable_windows_ansi_support() -> None:
    if os.name != "nt":
        return

    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass


class KyivFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        local_time = dt.datetime.fromtimestamp(record.created, tz=KYIV_TZ)
        if datefmt:
            return local_time.strftime(datefmt)
        return local_time.strftime("%Y-%m-%d %H:%M:%S")


class ColorFormatter(KyivFormatter):
    def format(self, record):
        color = COLORS.get(record.levelname, "")
        record.levelname_colored = f"{color}{record.levelname:<8}{RESET}"
        record.name_colored = f"{DIM}{record.name}{RESET}"
        return super().format(record)


def setup_logging(level: int = logging.INFO) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    enable_windows_ansi_support()

    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()
    root_logger.setLevel(level)

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(
        KyivFormatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
    )

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(level)
    if sys.stdout.isatty():
        stream_handler.setFormatter(
            ColorFormatter("%(asctime)s | %(levelname_colored)s | %(name_colored)s | %(message)s")
        )
    else:
        stream_handler.setFormatter(
            KyivFormatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
        )

    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("aiogram.event").setLevel(logging.INFO)


setup_logging()
