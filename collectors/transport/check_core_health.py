from grpc_health.v1 import health_pb2, health_pb2_grpc ; import grpc


class CoreHealth:

    @staticmethod
    def check(host="localhost", port=50051, timeout=5) -> bool:

        channel = None

        try:
            channel = grpc.insecure_channel(f"{host}:{port}")

            health_stub = health_pb2_grpc.HealthStub(channel)

            response = health_stub.Check(
                health_pb2.HealthCheckRequest(service=""),
                timeout=timeout
            )
            is_healthy = response.status == health_pb2.HealthCheckResponse.SERVING

            return is_healthy

        except Exception:
            try:
                if channel:
                    future = grpc.channel_ready_future(channel)
                    future.result(timeout=timeout)
                    return True
            except:
                return False
            finally:
                if channel:
                    channel.close()

        return False