# tests/test_log.py

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
    assert log.pad_column("foo", 1) == "foo"  # doesn't truncate string
    assert log.pad_column("", 2) == "  "


def test_add_blankline_after():
    assert log.add_blankline_after("foo") == "foo\n"
    assert log.add_blankline_after("") == "\n"
