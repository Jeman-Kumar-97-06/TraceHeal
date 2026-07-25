import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME

from openinference.instrumentation.openai import OpenAIInstrumentor
from opentelemetry.instrumentation.chromadb import ChromaInstrumentor

_provider: TracerProvider = None

def init_telemetry(service_name: str = "LocalAgent1") -> trace.Tracer:
    """Initializes OpenTelemetry tracing directed at SigNoz's OTLP HTTP receiver."""
    global _provider

    # Set service metadata
    resource = Resource.create(attributes={
        SERVICE_NAME: service_name,
        "deployment.environment": "development"
    })

    _provider = TracerProvider(resource=resource)

    # SigNoz HTTP OTLP endpoint (Default: http://localhost:4318/v1/traces)
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces")
    
    otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)

    # Use SimpleSpanProcessor for instant trace delivery during CLI/agent execution
    processor = SimpleSpanProcessor(otlp_exporter)
    _provider.add_span_processor(processor)
    
    trace.set_tracer_provider(_provider)

    # Enable auto-instrumentation for OpenAI/Ollama client & ChromaDB
    OpenAIInstrumentor().instrument()
    ChromaInstrumentor().instrument()

    print(f"✅ [OTel]: Telemetry initialized for '{service_name}' -> {otlp_endpoint}")
    return trace.get_tracer(service_name)

def flush_telemetry():
    """Forces immediate delivery of all pending spans to SigNoz."""
    if _provider:
        _provider.force_flush()