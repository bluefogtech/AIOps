import json
import os
import time
import chromadb
from chromadb.config import Settings

# Initialize ChromaDB
client = chromadb.Client(Settings(persist_directory="./chroma-metrics"))
collection = client.get_or_create_collection("system_metrics")

# Simple vectorizer for CPU/memory metrics
def metric_to_vector(name, value, ts):
    return [hash(name) % 1000 / 1000, float(value) / 100.0, (ts % 1e6) / 1e6]

# Read and process file
def process_metrics_file(path):
    if not os.path.exists(path):
        print("No metrics file found.")
        return

    with open(path, "r") as f:
        for line in f:
            try:
                data = json.loads(line)
                for rm in data.get("resourceMetrics", []):
                    for sm in rm.get("scopeMetrics", []):
                        for metric in sm.get("metrics", []):
                            name = metric.get("name", "")
                            points = metric.get("dataPoints", [])
                            for point in points:
                                value = point.get("asDouble", point.get("asInt", 0))
                                timestamp = int(point.get("timeUnixNano", time.time_ns())) // 1_000_000_000
                                vector = metric_to_vector(name, value, timestamp)
                                doc_id = f"{name}_{timestamp}"

                                collection.add(
                                    documents=[f"{name}: {value}"],
                                    metadatas=[{"timestamp": timestamp}],
                                    ids=[doc_id],
                                    embeddings=[vector]
                                )
                                print(f"Stored: {name} = {value} at {timestamp}")
            except json.JSONDecodeError:
                continue

# Run once or schedule as a loop
process_metrics_file("otel_metrics.json")
