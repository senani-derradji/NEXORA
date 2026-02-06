import random

class DeviceHeartbeat:
    @staticmethod
    def is_alive(device_name):
        "VIRTUAL / SEMULATES DEVICE HEARTBEAT"
        return True if random.randint(0, 100) > 20 else False
