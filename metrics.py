import time
import psutil

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

# Replace with your OTel Collector endpoint (default if running locally)
OTEL_COLLECTOR_URL = "http://localhost:4318/v1/metrics"

# Set up the OTLP exporter
exporter = OTLPMetricExporter(endpoint=OTEL_COLLECTOR_URL)

# Create a metric reader to export periodically
reader = PeriodicExportingMetricReader(exporter, export_interval_millis=10000)

# Create a MeterProvider with basic resource attributes
provider = MeterProvider(
    resource=Resource.create({"service.name": "macbook-metrics"}),
    metric_readers=[reader],
)

metrics.set_meter_provider(provider)
meter = metrics.get_meter("macbook.meter")

# Create Observable Gauges
def cpu_usage_callback(options):
    return [metrics.Observation(psutil.cpu_percent(), {})]

def memory_usage_callback(options):
    
    mem = psutil.virtual_memory()
    return [metrics.Observation(mem.used, {"state": "used"}),
            metrics.Observation(mem.total, {"state": "total"})]

meter.create_observable_gauge(
    name="system.cpu.usage",
    callbacks=[cpu_usage_callback],
    unit="percent",
    description="CPU usage percentage",
)

meter.create_observable_gauge(
    name="system.memory.usage",
    callbacks=[memory_usage_callback],
    unit="bytes",
    description="Memory usage",
)

print("Sending MacBook metrics to OpenTelemetry Collector every 10 seconds. Press Ctrl+C to stop.")
try:
    while True:
        time.sleep(1)  # Just keep the process alive
except KeyboardInterrupt:
    print("Stopped.")

