import logging
import warnings
from typing import Literal, Optional

allowable_log_levels = Literal["VERBOSE", "REGULAR", "QUIET", "NONE"]
# the temporary name for the logger that RC will use.
rc_logger_name = "RC"
rc_logger = logging.getLogger(rc_logger_name)


_default_format_string = "[+%(relative_seconds)-7ss] %(name)-12s: %(levelname)-8s - %(message)s"


class RelativeTimeFormatter(logging.Formatter):
    def format(self, record):
        record.relative_seconds = f"{record.relativeCreated / 1000:.3f}"
        return super().format(record)


def setup_verbose_logger_config():
    console_handler = logging.StreamHandler()
    # in the verbose case we would like to use the debug level.
    console_handler.setLevel(logging.DEBUG)

    verbose_formatter = RelativeTimeFormatter(
        fmt=_default_format_string,
    )

    console_handler.setFormatter(verbose_formatter)

    logger = logging.getLogger(rc_logger_name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)


def setup_regular_logger_config():
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    regular_formatter = RelativeTimeFormatter(
        fmt=_default_format_string,
    )

    console_handler.setFormatter(regular_formatter)

    logger = logging.getLogger(rc_logger_name)
    logger.addHandler(console_handler)
    logger.setLevel(logging.INFO)


def setup_quiet_logger_config():
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)

    quiet_formatter = RelativeTimeFormatter(fmt=_default_format_string)

    console_handler.setFormatter(quiet_formatter)

    logger = logging.getLogger(rc_logger_name)
    logger.addHandler(console_handler)
    logger.setLevel(logging.WARNING)


def setup_none_logger_config():
    """
    Set up the logger to do nothing.
    """
    # set up a logger which does not do anything.
    logger = logging.getLogger(rc_logger_name)
    logger.setLevel(logging.CRITICAL)
    logger.addHandler(logging.NullHandler())


# TODO Complete the file integration.
def setup_file_handler(
    file_name: str,
    file_logging_config: dict | None,
    file_logging_level: logging.DEBUG | logging.INFO | logging.WARNING | logging.ERROR | logging.CRITICAL,
):
    file_handler = logging.FileHandler(file_name)
    logging_level = logging.DEBUG if file_logging_level else file_logging_level
    file_handler.setLevel(logging_level)

    # date format include milliseconds for better resolution
    if file_logging_config is not None:
        user_provided_format = logging.Formatter(**file_logging_config)
        file_handler.setFormatter(user_provided_format)
    else:
        default_formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(threadName)s %(message)s",
        )

        file_handler.setFormatter(default_formatter)

    # we want to add this file handler to the root logger is it is propagated
    logger = logging.getLogger(rc_logger_name)
    logger.addHandler(file_handler)


# TODO fill out the rest of the logic
def prepare_logger(
    setting: allowable_log_levels,
    # file_name: str | None = None,
    # file_logging_config: dict | None = None,
    # file_logging_level: (
    #     logging.DEBUG | logging.INFO | logging.WARNING | logging.ERROR | logging.CRITICAL
    # ) = logging.DEBUG,
):
    # # the file injection will happen no matter what.
    # if file_name is not None:
    #     setup_file_handler(file_name, file_logging_config, file_logging_level)
    # # We should raise a warning if the file logging config was provided
    # else:
    #     if file_logging_config is not None:
    #         warnings.warn(
    #             "File logging config provided but no file was provided. The file logging config will be ignored"
    #

    # now for each of our predefined settings we will set up the logger.
    if setting == "VERBOSE":
        setup_verbose_logger_config()
    elif setting == "REGULAR":
        setup_regular_logger_config()
    elif setting == "QUIET":
        setup_quiet_logger_config()
    elif setting == "NONE":
        setup_none_logger_config()
    else:
        raise ValueError("Invalid log level setting")
