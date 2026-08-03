from config.logging import setup_logging


def test_setup_logging_configures_console_and_file_handlers():
    logger = setup_logging()

    assert logger is not None
    assert logger._core.handlers
