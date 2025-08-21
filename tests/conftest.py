# tests/utils_for_tests.py

import logging

import pytest
from mockito import unstub

# Helper functions for unit tests


@pytest.fixture()
def capture_logs(caplog):
    # caplog default level is INFO; set to DEBUG instead
    caplog.set_level(logging.DEBUG)
    yield caplog


@pytest.fixture
def unstub_fixture():
    """
    A pytest fixture to ensure mocks are unstubbed after each test.
    """
    yield  # allows the test to run
    unstub()
