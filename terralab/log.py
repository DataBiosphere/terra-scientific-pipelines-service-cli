# log.py

import colorlog
import logging


def configure_logging(debug: bool):
    log_level = logging.DEBUG if debug else logging.INFO

    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s%(message)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        )
    )

    logging.basicConfig(level=log_level, format="%(message)s", handlers=[handler])


def indented(string_to_indent: str, n_spaces: int = 2):
    return f"{' ' * n_spaces}{string_to_indent}"


def join_lines(list_of_strings: list[str]):
    return "\n".join(list_of_strings)


def pad_column(first_string: str, column_width: int = 20):
    return first_string.ljust(column_width)


def add_blankline_after(string: str):
    return f"{string}\n"
