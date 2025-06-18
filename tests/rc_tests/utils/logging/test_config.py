import logging

import pytest

from requestcompletion.utils.logging.config import prepare_logger, rc_logger, detach_logging_handlers


@pytest.fixture
def detach_logger():
    """
    Fixture to prepare the logger before each test.
    """

    yield
    detach_logging_handlers()

@pytest.mark.parametrize(
    "log_level",
    [logging.DEBUG, logging.INFO, logging.ERROR, logging.WARNING, logging.CRITICAL],
    ids="debug, info, error, warning, critical".split(", "),
)
def test_simple_logger_setting_none(caplog, log_level, detach_logger):
    prepare_logger(setting="NONE")
    with caplog.at_level(log_level):
        rc_logger.debug("Hello world")
        rc_logger.info("Hello world")
        rc_logger.warning("Hello world")
        rc_logger.error("Hello world")
        rc_logger.critical("Hello world")
        rc_logger.exception("Hello world")

    assert len(caplog.records) == 0


expected_answers = {
    "VERBOSE": {
        logging.DEBUG: 5,
        logging.INFO: 4,
        logging.WARNING: 3,
        logging.ERROR: 2,
        logging.CRITICAL: 1,
    },
    "REGULAR": {
        logging.DEBUG: 4,
        logging.INFO: 4,
        logging.WARNING: 3,
        logging.ERROR: 2,
        logging.CRITICAL: 1,
    },
    "QUIET": {
        logging.DEBUG: 3,
        logging.INFO: 3,
        logging.WARNING: 3,
        logging.ERROR: 2,
        logging.CRITICAL: 1,
    },
    "NONE": {
        logging.DEBUG: 0,
        logging.INFO: 0,
        logging.WARNING: 0,
        logging.ERROR: 0,
        logging.CRITICAL: 0,
    },
}
@pytest.mark.parametrize(
    "log_setting",
    [
        "VERBOSE",
        "REGULAR",
        "QUIET",
        "NONE",
    ],
    ids="verbose, regular, quiet, none".split(", "),
)
@pytest.mark.parametrize(
    "log_level",
    [
        logging.DEBUG,
        logging.INFO,
        logging.WARNING,
        logging.ERROR,
        logging.CRITICAL,
    ],
    ids="debug, info, warning, error, critical".split(", "),
)
def test_verbose_logger(caplog, log_level, log_setting, detach_logger):
    prepare_logger(setting=log_setting)

    with caplog.at_level(log_level):
        rc_logger.debug("Hello world")
        rc_logger.info("Hello world")
        rc_logger.warning("Hello world")
        rc_logger.error("Hello world")
        rc_logger.critical("Hello world")

    print(f"Log setting: {log_setting}, Log level: {log_level}, expected {expected_answers[log_setting][log_level]} records")
    assert len(caplog.records) == expected_answers[log_setting][log_level]

    for record in caplog.records:
        assert record.message == "Hello world"












