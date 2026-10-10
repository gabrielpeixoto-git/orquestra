"""OpenTelemetry configuration for Orquestra."""

import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def configure_opentelemetry() -> None:
    """Configure OpenTelemetry for distributed tracing."""
    # Create resource with service information
    debug = os.environ.get("DEBUG", "False").lower() in ("true", "1", "t")
    resource = Resource.create(
        {
            "service.name": "orquestra",
            "service.version": "0.1.0",
            "deployment.environment": "development" if debug else "production",
        }
    )

    # Configure tracer provider
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    # Configure OTLP exporter
    otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(processor)

    # Instrument Django
    DjangoInstrumentor().instrument()

    # Instrument Celery
    CeleryInstrumentor().instrument()

    # Instrument psycopg
    PsycopgInstrumentor().instrument()

    # Instrument Redis
    RedisInstrumentor().instrument()
