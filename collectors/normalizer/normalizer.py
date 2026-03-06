import time

class Normalizer:

    @staticmethod
    def normalize(raw_metric):
        print("INSIDE -- NORMALIZER : ", raw_metric)
        return {
            "device":
                {
                    "hostname": raw_metric.get("device_host", "unknown"),
                    "device_type": raw_metric.get("device_type", "unknown"),
                    "ip": raw_metric.get("device_ip", "unknown"),
                    "mac": raw_metric.get("device_mac", "unknown")
                },

            "sys": {
                "cpu": raw_metric.get("cpu", 0.0),
                "ram": raw_metric.get("ram", 0.0),
                "disk": raw_metric.get("disk", 0.0),
            },

            "net": {
                "in_bytes": raw_metric.get("in_bytes", 0.0),
                "out_bytes": raw_metric.get("out_bytes", 0.0),

                "in_packets": raw_metric.get("in_packets", 0.0),
                "out_packets": raw_metric.get("out_packets", 0.0),

                "in_errors": raw_metric.get("in_errors", 0.0),
                "out_errors": raw_metric.get("out_errors", 0.0),

                "latency": raw_metric.get("latency", 0.0),
                "packet_loss": raw_metric.get("packet_loss", 0.0),

            },

            "status": raw_metric.get("status", "unknown"),
            "timestamp": raw_metric.get("timestamp", int(time.time()))
        }
