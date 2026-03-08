import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from concurrent import futures
import grpc
from core.grpc_api import core_ingest_pb2 as core_ingest_pb2
from core.grpc_api import core_ingest_pb2_grpc as core_ingest_pb2_grpc
from grpc_health.v1 import health_pb2, health_pb2_grpc
from core.processer.normalizer import Normalizer
from core.buffer.ingest_queue import CoreBuffer
from core.writer.data_writer import CoreWriter



class CoreIngestService(core_ingest_pb2_grpc.CoreIngestServicer):
    def __init__(self):
        self.buffer = CoreBuffer(max_size=1000)
        self.normalizer = Normalizer()
        self.coredbwriter = CoreWriter()

    def SendMetric(self, request, context):
        print(f"[CORE] Got metric: {request.metric_values} {request.tags}")

        metric__ = self.normalizer.normalize(
            request.device_hostname, request.metric_values, request.tags, request.timestamp
        )

        if self.buffer.add_metric(metric=metric__):
            get = self.buffer.get_metric()

            self.coredbwriter.write_in_db(get)

        return core_ingest_pb2.Ack(success=True, message="Metric received")


class HealthServicer(health_pb2_grpc.HealthServicer):
    def Check(self, request, context):
        return health_pb2.HealthCheckResponse(status=health_pb2.HealthCheckResponse.SERVING)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    core_ingest_pb2_grpc.add_CoreIngestServicer_to_server(CoreIngestService(), server)

    health_pb2_grpc.add_HealthServicer_to_server(HealthServicer(), server)

    server.add_insecure_port("[::]:50051")
    server.start()
    print("[CORE] gRPC server running on port 50051...")
    server.wait_for_termination()


if __name__ == "__main__":
    print("[CORE] Starting server...")
    serve()