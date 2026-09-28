from pathlib import Path

import pytest

from app import config

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLES = FIXTURES / "samples"


def pytest_runtest_setup(item):
    if "live" in item.keywords and not (config.GEMINI_API_KEY and config.GEMINI_MODEL):
        pytest.skip("GEMINI_API_KEY / GEMINI_MODEL not set")


def sample_bytes(name: str) -> bytes:
    path = SAMPLES / name
    if not path.exists():  # the public repo ships without RegenMed's sample forms
        pytest.skip(f"sample fixture not included: {name}")
    return path.read_bytes()
