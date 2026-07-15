from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any


@contextmanager
def traced_span(
    name: str,
    attributes: dict[str, str | int | float | bool] | None = None,
) -> Iterator[Any]:
    """Create an OpenTelemetry span when the API package is installed."""
    try:
        from opentelemetry import trace
    except ImportError:
        yield None
        return

    tracer = trace.get_tracer("enterprise-policy-agent")
    with tracer.start_as_current_span(name) as span:
        for key, value in (attributes or {}).items():
            span.set_attribute(key, value)
        yield span
