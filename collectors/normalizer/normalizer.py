import time

class Normalizer:

    @staticmethod
    def normalize(raw_metric):
        # Check if device is DOWN - if so, send None for metrics to preserve old values
        is_device_down = raw_metric.get("status") in ("down", "DOWN")

        return {
            "device":
                {
                    "hostname": raw_metric.get("hostname", "unknown"),
                    "device_type": raw_metric.get("device_type", "unknown"),
                    "ip": raw_metric.get("device_ip", "unknown"),
                    "mac": raw_metric.get("device_mac", "unknown")
                },

            "sys": {
                # For DOWN devices, send None to preserve old metrics in InfluxDB
                "cpu": None if is_device_down else raw_metric.get("cpu"),
                "ram": None if is_device_down else raw_metric.get("ram"),
                "disk": None if is_device_down else raw_metric.get("disk"),
            },

            "net": {
                # For DOWN devices, send None to preserve old metrics in InfluxDB
                "in_bytes": None if is_device_down else raw_metric.get("in_bytes"),
                "out_bytes": None if is_device_down else raw_metric.get("out_bytes"),

                "in_packets": None if is_device_down else raw_metric.get("in_packets"),
                "out_packets": None if is_device_down else raw_metric.get("out_packets"),

                "in_errors": None if is_device_down else raw_metric.get("in_errors"),
                "out_errors": None if is_device_down else raw_metric.get("out_errors"),

                "latency": None if is_device_down else raw_metric.get("latency"),
                "packet_loss": raw_metric.get("packet_loss", 0.0),

            },

            "status": raw_metric.get("status", "unknown"),
            "timestamp": raw_metric.get("timestamp", int(time.time()))
        }
