import grpc
import time
import api.core_ingest_pb2 as core_ingest_pb2
import api.core_ingest_pb2_grpc as core_ingest_pb2_grpc
from collectors.utils.normalizer_helper import safe_float


class CoreClient:
    def __init__(self, host="localhost", port=50051):
        self.channel = grpc.insecure_channel(f"{host}:{port}")
        self.stub = core_ingest_pb2_grpc.CoreIngestStub(self.channel)

    def send_metric(self, metric):
        if not metric:
            print("No metric to send (None). Skipping...")
            return False

        proto = core_ingest_pb2.Metric(
            device_hostname=metric.get("device", {}).get("hostname", "unknown"),

            metric_values={
                "cpu": safe_float(metric.get("sys", {}).get("cpu")),
                "ram": safe_float(metric.get("sys", {}).get("ram")),
                "disk": safe_float(metric.get("sys", {}).get("disk")),

                "in_bytes": safe_float(metric.get("net", {}).get("in_bytes")),
                "out_bytes": safe_float(metric.get("net", {}).get("out_bytes")),
                "in_packets": safe_float(metric.get("net", {}).get("in_packets")),
                "out_packets": safe_float(metric.get("net", {}).get("out_packets")),
                "in_errors": safe_float(metric.get("net", {}).get("in_errors")),
                "out_errors": safe_float(metric.get("net", {}).get("out_errors")),

                "packet_loss": safe_float(metric.get("net", {}).get("packet_loss")),
                "latency": safe_float(metric.get("net", {}).get("latency")),

                "timestamp": metric.get("timestamp", int(time.time()))
            },

            tags={
                "type": metric.get("device", {}).get("type", "unknown"),
                "ip": metric.get("device", {}).get("ip", "unknown"),
                "mac": metric.get("device", {}).get("mac", "unknown"),
                "status": metric.get("status", "unknown")
            },

            timestamp=int(time.time())
        )

        try:
            response = self.stub.SendMetric(proto, timeout=0.5)
            print(f"[Collector] Metric sent successfully")
            return response.success
        except grpc.RpcError as e:
            print("[Collector] gRPC Error:", e)
            return False
        except Exception as e:
            print("[Collector] Error:", e)
            return False
