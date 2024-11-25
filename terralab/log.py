# log.py

import colorlog
import logging
from tabulate import tabulate


def configure_logging(debug: bool):
    log_level = logging.DEBUG if debug else logging.INFO

    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s%(message)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "white",
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
    column_width = max(column_width, len(first_string) + 1)
    return first_string.ljust(column_width)


def add_blankline_after(string: str):
    return f"{string}\n"


def format_table_with_status(
    rows_list: list[list[str]], status_key: str = "Status"
) -> str:
    """Provided a list of list of strings representing rows to be formatted into a table,
    with the headers as the first list of strings, color-format a Status column's values
    and return the formatted (via tabulate package) string to be logged as a table.

    Raises a ValueError if the status_key is not found in the first row (headers) of the table.
    """
    all_table_rows = []
    headers = rows_list[0]
    # find status column index; this raises a ValueError if the status_key is not found
    status_column_index = headers.index(status_key)
    for single_table_row in rows_list:
        all_table_rows.append(
            format_status_in_table_row(single_table_row, status_column_index)
        )

    return tabulate(all_table_rows, headers="firstrow", numalign="left")


COLORFUL_STATUS = {
    "FAILED": "\033[1;37;41mFailed\033[0m",
    "SUCCEEDED": "\033[1;37;42mSucceeded\033[0m",
    "RUNNING": "\033[0;30;46mRunning\033[0m",
    "PREPARING": "\033[0;30;43mPreparing\033[0m",
}


def format_status_in_table_row(
    table_row: list[str], status_column_index: int
) -> list[str]:
    """Look for a value in the status_column_index index of table_row that matches the keys in COLORFUL_STATUS.
    If present, replace with the colored value and return the row.
    Otherwise (or if index is None), return the row unchanged."""
    if (
        status_column_index is not None
        and table_row[status_column_index].upper() in COLORFUL_STATUS
    ):
        table_row[status_column_index] = COLORFUL_STATUS[
            table_row[status_column_index].upper()
        ]

    return table_row


def format_status(status_str: str) -> str:
    return COLORFUL_STATUS[status_str]
