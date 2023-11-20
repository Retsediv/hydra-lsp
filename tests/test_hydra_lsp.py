from __future__ import annotations

import logging
import sys

import pytest


@pytest.fixture(autouse=True, scope="session")
def setup_logging():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    logging.getLogger("pygls").setLevel(logging.DEBUG)


def test_foo():
    assert True
