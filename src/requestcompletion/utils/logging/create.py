import logging

from .config import rc_logger_name, ColorfulFormatter


def get_rc_logger(name: str | None):
    """
    A method used to get a logger of the provided name.

    The method is essentially a wrapper of the `logging` method to collect the logger, but it will add a reference to
    the RC root logger.

    If the name is not provided it returns the root RC logger.
    """
    if name is None:
        logger = logging.getLogger(rc_logger_name)
    else:
        logger = logging.getLogger(f"{rc_logger_name}.{name}")

    # Ensure the logger has the ColorfulFormatter applied
    if not logger.handlers:  # Avoid adding duplicate handlers
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)  # Adjust the level as needed
        formatter = ColorfulFormatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
