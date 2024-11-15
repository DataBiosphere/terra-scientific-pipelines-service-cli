# tests/utils_for_tests.py

import logging
import pytest

# Helper functions for unit tests


@pytest.fixture()
def capture_logs(caplog):
    # caplog default level is INFO; set to DEBUG instead
    caplog.set_level(logging.DEBUG)
    yield caplog
