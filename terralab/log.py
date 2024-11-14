# log.py

import logging


def configure_logging(debug: bool):
    log_level = logging.DEBUG if debug else logging.INFO

    # create a handler, modify the terminator to add an extra newline after each logged message
    handler = logging.StreamHandler()
    handler.terminator = "\n\n"

    logging.basicConfig(level=log_level, format="%(message)s", handlers=[handler])
