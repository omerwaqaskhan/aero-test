"""OpenTelemetry distributed tracing setup."""

import os
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

# Initialize tracer provider
resource = Resource.create({
    "service.name": os.getenv("SERVICE_NAME", "aero-hotels-backend"),
    "service.version": os.getenv("SERVICE_VERSION", "1.0.0"),
    "deployment.environment": os.getenv("ENVIRONMENT", "development"),
})

tracer_provider = TracerProvider(resource=resource)

# Configure OTLP exporter (for Jaeger, Tempo, etc.)
otlp_endpoint = os.getenv("OTLP_ENDPOINT", "http://localhost:4317")
if otlp_endpoint:
    otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

trace.set_tracer_provider(tracer_provider)

tracer = trace.get_tracer(__name__)


def setup_tracing(app):
    """Setup OpenTelemetry tracing for FastAPI app."""
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
    
    # Instrument SQLAlchemy
    SQLAlchemyInstrumentor().instrument()
    
    # Instrument requests library
    RequestsInstrumentor().instrument()


def get_tracer(name: str = __name__):
    """Get a tracer instance."""
    return trace.get_tracer(name)

