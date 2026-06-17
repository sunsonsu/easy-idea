"""OpenTelemetry setup — traces + metrics exported via OTLP to the Collector.
Fail-soft: if the Collector is down, the app still runs."""
import os
import logging
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

logger = logging.getLogger(__name__)


def setup_observability(app, service_name: str = "easy-idea-api") -> None:
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317")
    resource = Resource.create({"service.name": service_name})

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=True))
    )
    trace.set_tracer_provider(tracer_provider)

    reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=endpoint, insecure=True),
        export_interval_millis=10000,
    )
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[reader]))

    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()
    logger.info(f"OpenTelemetry wired → {endpoint} (service={service_name})")
