# tests/test_log.py

import pytest

import logging
from terralab.log import RetryMessageFilter
from terralab import log


def test_indented():
    # default n_spaces is 2
    assert log.indented("foo") == "  foo"
    assert log.indented("foo", 3) == "   foo"


def test_join_lines():
    assert log.join_lines(["one", "two"]) == "one\ntwo"
    assert log.join_lines(["one"]) == "one"
    assert log.join_lines([""]) == ""


def test_pad_column():
    # default column_width is 20
    assert log.pad_column("foo") == "foo                 "  # 17 spaces
    assert log.pad_column("foo", 5) == "foo  "
    assert (
        log.pad_column("foo", 1) == "foo "
    )  # if padding is less than len(str), adds a space after
    assert log.pad_column("", 2) == "  "


def test_add_blankline_before():
    assert log.add_blankline_before("foo") == "\nfoo"
    assert log.add_blankline_before("") == "\n"


format_table_with_status_testdata = [
    # rows, status_key, expected_substrings or None if error
    (  # no status in headers
        [["Name", "Age"], ["Alice", "25"]],
        "Status",
        None,
    ),
    (  # status in header
        [["Name", "Status", "Age"], ["Alice", "SUCCEEDED", "25"]],
        "Status",
        ["Name", "\033[1;37;42mSucceeded\033[0m", "25"],
    ),
    (  # multiple rows
        [
            ["Job", "Status", "Time"],
            ["job1", "FAILED", "10:00"],
            ["job2", "RUNNING", "10:01"],
            ["job3", "PREPARING", "10:02"],
        ],
        "Status",
        [
            "Job",
            "\033[1;37;41mFailed\033[0m",
            "\033[0;30;46mRunning\033[0m",
            "\033[0;30;43mPreparing\033[0m",
            "10:00",
        ],
    ),
    (  # non-default status key
        [["Name", "State", "Age"], ["Alice", "SUCCEEDED", "25"]],
        "State",
        ["Name", "\033[1;37;42mSucceeded\033[0m", "25"],
    ),
]


@pytest.mark.parametrize(
    "rows,status_key,expected_substrings", format_table_with_status_testdata
)
def test_format_table_with_status(rows, status_key, expected_substrings):
    if expected_substrings:
        formatted = log.format_table_with_status(rows, status_key=status_key)
        for expected in expected_substrings:
            assert expected in formatted
    else:
        with pytest.raises(ValueError):
            log.format_table_with_status(rows, status_key=status_key)


def test_format_table_with_status_line_wrapping():
    long_field_value = "this is a field that we expect to get wrapped"
    max_col_size = len(long_field_value) - 5
    rows = [["Name", "Status", "Long field"], ["Alice", "SUCCEEDED", long_field_value]]
    formatted = log.format_table_with_status(rows, max_col_size=max_col_size)

    # the long field should have been wrapped into two rows, so expect 4 (header + ---- + 2 data lines)
    formatted_rows = formatted.split("\n")
    assert len(formatted_rows) == 4


def test_retry_message_filter_match():
    filter_instance = RetryMessageFilter()

    record = logging.LogRecord(
        name="urllib3.connectionpool",
        level=logging.WARNING,
        pathname="test_path",
        lineno=10,
        msg="Retrying (Retry(total=2, connect=None, read=None, redirect=None, status=None)) "
        "after connection broken by 'NewConnectionError': /api/test",
        args=(),
        exc_info=None,
    )

    result = filter_instance.filter(record)

    assert result is False
    assert record.levelno == logging.DEBUG
    assert (
        record.msg
        == "terralab encountered a problem connecting to the server. Retrying your request..."
    )
    assert record.args == ()


# Tests that we don't clobber other non-retry log messages
def test_retry_message_filter_non_match():
    filter_instance = RetryMessageFilter()

    non_matching_record = logging.LogRecord(
        name="urllib3.connectionpool",
        level=logging.WARNING,
        pathname="test_path",
        lineno=10,
        msg="Some other log message",
        args=(),
        exc_info=None,
    )

    result = filter_instance.filter(non_matching_record)

    assert result is True
    assert non_matching_record.levelno == logging.WARNING
    assert non_matching_record.msg == "Some other log message"


format_status_in_table_row_testdata = [
    # input row list input, status index input, expected output list
    (  # status column at expected index
        ["job1", "FAILED", "10:00"],
        1,
        ["job1", "\033[1;37;41mFailed\033[0m", "10:00"],
    ),
    (  # status column at different indices
        ["job1", "FAILED", "10:00"],
        0,
        ["job1", "FAILED", "10:00"],
    ),
    (  # status not in COLORFUL_STATUS
        ["job1", "UNKNOWN", "10:00"],
        1,
        ["job1", "UNKNOWN", "10:00"],
    ),
    (  # status at beginning
        ["SUCCEEDED", "job1", "10:00"],
        0,
        ["\033[1;37;42mSucceeded\033[0m", "job1", "10:00"],
    ),
    (  # status at end
        ["job1", "10:00", "RUNNING"],
        2,
        ["job1", "10:00", "\033[0;30;46mRunning\033[0m"],
    ),
    (  # invalid status index (None) returns row untouched
        ["job1", "FAILED", "10:00"],
        None,
        ["job1", "FAILED", "10:00"],
    ),
]


@pytest.mark.parametrize(
    "row, status_index, expected", format_status_in_table_row_testdata
)
def test_format_status_in_table_row(row, status_index, expected):
    formatted = log.format_status_in_table_row(row, status_index)
    assert formatted == expected


format_status_testdata = [
    # input status string, expected formatted output
    ("FAILED", "\033[1;37;41mFailed\033[0m"),
    ("SUCCEEDED", "\033[1;37;42mSucceeded\033[0m"),
    ("RUNNING", "\033[0;30;46mRunning\033[0m"),
    ("PREPARING", "\033[0;30;43mPreparing\033[0m"),
]


@pytest.mark.parametrize("status,expected", format_status_testdata)
def test_format_status(status, expected):
    formatted = log.format_status(status)
    assert formatted == expected
