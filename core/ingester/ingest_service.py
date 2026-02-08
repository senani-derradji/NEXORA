import os, sys ; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from transport import core_ingest_pb2 as core_ingest_pb2
from transport import core_ingest_pb2_grpc as core_ingest_pb2_grpc
from concurrent import futures
import time, grpc
from core.processer.normalizer import Normalizer
from core.buffer.ingest_queue import CoreBuffer
from core.writer.data_writer import CoreWriter



class CoreIngestService(core_ingest_pb2_grpc.CoreIngestServicer):
    def __init__(self):
        self.buffer = CoreBuffer()
        self.normalizer = Normalizer()
        self.coredbwriter = CoreWriter()



    def SendMetric(self, request, context):

        print(f"[CORE] Got metric: {request.device_hostname} , {request.timestamp}")
        metric__ = self.normalizer.normalize(request.device_hostname, request.metric_values, request.tags, request.timestamp)

        if self.buffer.add_metric(metric=metric__):
            get = self.buffer.get_metric()
            print(f"METRIC {get.get('hostname')} {get.get('type')} WRITED IN DB SUCCESSFULLY")
            self.coredbwriter.write_in_db(get)

        return core_ingest_pb2.Ack(success=True, message="Metric received")


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=20))
    core_ingest_pb2_grpc.add_CoreIngestServicer_to_server(CoreIngestService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    print("[CORE] Starting server...")
    serve()