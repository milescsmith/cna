import datetime
from pathlib import Path
from sys import stderr, stdout
from typing import TextIO

from loguru import logger

# parent_module = modules[".".join(__name__.split(".")[:-1]) or "__main__"]

def init_logger(verbose: int = 0) -> None:
    timezone = datetime.datetime.now(datetime.UTC).astimezone().tzinfo

    logger.remove()  # Remove the default handler.

    match verbose:
        case 3:
            log_level = "DEBUG"
            backtrace = True
            diagnose = True
        case 2:
            log_level = "INFO"
            backtrace = False
            diagnose = False
        case 1:
            log_level = "WARNING"
            backtrace = False
            diagnose = False
        case _:
            log_level = "ERROR"
            backtrace = False
            diagnose = False

    msg_save_format = "{name}:{function}:{line} - {message}"
    msg_display_format = "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    output_file_sink: Path | TextIO = Path(f"{__package__}_{datetime.datetime.now(tz=timezone).strftime('%d-%m-%Y--%H-%M-%S')}.log")

    logger.add(
        sink=output_file_sink,
        format=msg_save_format,
        level="DEBUG",
        backtrace=True,
        diagnose=True,
        filter=__package__,
        rotation="500 MB",
    )

    logger.add(
        sink=stderr,
        format=msg_display_format,
        level=log_level,
        backtrace=backtrace,
        diagnose=diagnose,
        filter=__package__,
    )