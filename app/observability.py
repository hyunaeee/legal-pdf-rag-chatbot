from __future__ import annotations

import logging
from typing import Any

from app.settings import Settings

logger = logging.getLogger(__name__)


def configure_observability(app: Any, settings: Settings) -> bool:
    """Configure OTLP tracing and log correlation when explicitly enabled."""
    if not settings.otel_enabled:
        logger.info("OpenTelemetry instrumentation is disabled.")
        return False

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.logging import LoggingInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError as exc:
        raise RuntimeError(
            "Install observability dependencies with "
            "`pip install -e '.[observability]'`."
        ) from exc

    resource = Resource.create(
        {
            "service.name": settings.otel_service_name,
            "deployment.environment": settings.environment,
        }
    )
    provider = TracerProvider(resource=resource)
    exporter_kwargs: dict[str, object] = {}
    if settings.otel_exporter_otlp_endpoint:
        exporter_kwargs["endpoint"] = settings.otel_exporter_otlp_endpoint
    exporter = OTLPSpanExporter(**exporter_kwargs)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    LoggingInstrumentor().instrument(
        set_logging_format=True,
        tracer_provider=provider,
    )
    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
    logger.info(
        "OpenTelemetry instrumentation enabled for %s.",
        settings.otel_service_name,
    )
    return True
