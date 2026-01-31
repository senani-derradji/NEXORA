import random, time

class VirtualEngine:
    def collect(self, device_hostname, device_type, device_ip_address, device_mac_address):
        return {
            "device_host": device_hostname,
            "device_type": device_type,
            "device_ip"  : device_ip_address,
            "device_mac" : device_mac_address,

            "cpu": float(round(random.uniform(10, 90), 2)),
            "ram": float(round(random.uniform(20, 95), 2)),
            "disk": float(round(random.uniform(10, 90), 2)),

            "in_bytes": float(round(random.uniform(1, 1000), 2)),
            "out_bytes": float(round(random.uniform(1, 1000), 2)),

            "in_packets": float(round(random.uniform(1, 256), 2)),
            "out_packets": float(round(random.uniform(1, 256), 2)),

            "in_errors": float(round(random.uniform(1, 10), 2)),
            "out_errors": float(round(random.uniform(1, 10), 2)),

            "latency": float(round(random.uniform(1, 10), 2)),
            "packet_loss": float(round(random.uniform(1, 10), 2)),

            "status": True,
            "timestamp": int(time.time())
        }
