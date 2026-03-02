from grpc_health.v1 import health_pb2, health_pb2_grpc
import grpc

class CoreHealth:
    @staticmethod
    def check(host, port, timeout=8) -> bool:
        channel = None
        print(f"[HealthCheck] Checking Core at {host}:{port}")

        try:
            channel = grpc.insecure_channel(f"{host}:{port}")
            grpc.channel_ready_future(channel).result(timeout=timeout)

            stub = health_pb2_grpc.HealthStub(channel)
            response = stub.Check(health_pb2.HealthCheckRequest(service=""), timeout=timeout)

            healthy = response.status == health_pb2.HealthCheckResponse.SERVING
            print(f"[HealthCheck] Core health: {healthy}")
            return healthy

        except grpc.RpcError as e:
            print(f"[HealthCheck] gRPC error: {e}")
            return False

        finally:
            if channel:
                channel.close()