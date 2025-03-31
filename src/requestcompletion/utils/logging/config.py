import logging
import warnings
from typing import Literal, Optional

allowable_log_levels = Literal["VERBOSE", "REGULAR", "QUIET"]
# the temporary name for the logger that RC will use.
rc_logger_name = "RC"


def setup_verbose_logger_config():
    console_handler = logging.StreamHandler()
    # in the verbose case we would like to use the debug level.
    console_handler.setLevel(logging.DEBUG)

    logger = logging.getLogger(rc_logger_name)
    logger.addHandler(console_handler)

    verbose_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(threadName)s %(message)s",
        datefmt="%y/%m/%d %H:%M:%S.%f",
    )


def setup_regular_logger_config():
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    logger = logging.getLogger(rc_logger_name)
    logger.addHandler(console_handler)

    # TODO finish adding all the other configurations


def setup_quiet_logger_config():
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)

    logger = logging.getLogger(rc_logger_name)
    logger.addHandler(console_handler)

    # TODO finish adding all the other configurations


def setup_file_handler(
    file_name: str,
    file_logging_config: dict | None,
    file_logging_level: logging.DEBUG | logging.INFO | logging.WARNING | logging.ERROR | logging.CRITICAL | None,
):
    file_handler = logging.FileHandler(file_name)
    logging_level = logging.DEBUG if file_logging_level else file_logging_level
    file_handler.setLevel(logging.DEBUG if file_logging_level else file_logging_level)

    # date format include milliseconds for better resolution
    if file_logging_config is not None:
        user_provided_format = logging.Formatter(**file_logging_config)
        file_handler.setFormatter(user_provided_format)
    else:
        default_formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(threadName)s %(message)s",
            datefmt="%y/%m/%d %H:%M:%S.%f",
        )

        file_handler.setFormatter(default_formatter)

    # we want to add this file handler to the root logger is it is propagated
    logger = logging.getLogger(rc_logger_name)
    logger.addHandler(file_handler)


def prepare_logger(
    setting: allowable_log_levels,
    *,
    no_stream: bool,
    file_name: str | None,
    file_logging_config: dict | None,
    file_logging_level: logging.DEBUG | logging.INFO | logging.WARNING | logging.ERROR | logging.CRITICAL | None,
):
    # the file injection will happen no matter what.
    if file_name is not None:
        setup_file_handler(file_name, file_logging_config, file_logging_level)
    # We should raise a warning if the file logging config was provided
    else:
        if file_logging_config is not None:
            warnings.warn(
                "File logging config provided but no file was provided. The file logging config will be ignored"
            )

    # now for each of our predefined settings we will set up the logger.
    if setting == "VERBOSE":
        setup_verbose_logger_config()
    elif setting == "REGULAR":
        setup_regular_logger_config()
    elif setting == "QUIET":
        setup_quiet_logger_config()
    else:
        raise ValueError("Invalid log level setting")
