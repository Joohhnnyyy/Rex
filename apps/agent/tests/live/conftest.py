"""Live workflow tests are skipped unless REX_LIVE_TESTS=1 (they need network + real API keys).

REX_LIVE_TESTS=1 uv run --env-file .env pytest apps/agent/tests/live -v
"""

import os

import pytest


def pytest_collection_modifyitems(config, items):
    if os.environ.get("REX_LIVE_TESTS") == "1":
        return
    skip = pytest.mark.skip(reason="live test: set REX_LIVE_TESTS=1")
    for item in items:
        if "/tests/live/" in str(item.fspath):
            item.add_marker(skip)
