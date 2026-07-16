from fastapi import FastAPI

from app.observability import configure_observability
from app.settings import Settings


def test_observability_is_disabled_by_default() -> None:
    enabled = configure_observability(FastAPI(), Settings())
    assert enabled is False
