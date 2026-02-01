import time




class Normalizer:
    _network_devices_types = ["router", "switch", "server", "firewall"]


    @staticmethod
    def normalize(raw_metric):
        return {
            "device":
                {
                    "hostname": raw_metric.get("device_host", "unknown"),
                    "type": raw_metric.get("device_type", "unknown"),
                    "ip": raw_metric.get("device_ip", "unknown"),
                    "mac": raw_metric.get("device_mac", "unknown")
                },

            "sys": {
                "cpu": raw_metric.get("cpu", 0),
                "ram": raw_metric.get("ram", 0),
                "disk": raw_metric.get("disk", 0) if raw_metric.get("device_type") not in Normalizer._network_devices_types else None,
            },

            "net": {
                "in_bytes": raw_metric.get("in_bytes", 0) if raw_metric.get("device_type") in Normalizer._network_devices_types else None,
                "out_bytes": raw_metric.get("out_bytes", 0) if raw_metric.get("device_type") in Normalizer._network_devices_types else None,

                "in_packets": raw_metric.get("in_packets", 0) if raw_metric.get("device_type") in Normalizer._network_devices_types else None,
                "out_packets": raw_metric.get("out_packets", 0) if raw_metric.get("device_type") in Normalizer._network_devices_types else None,

                "in_errors": raw_metric.get("in_errors", 0) if raw_metric.get("device_type") in Normalizer._network_devices_types else None,
                "out_errors": raw_metric.get("out_errors", 0) if raw_metric.get("device_type") in Normalizer._network_devices_types else None,

                "latency": raw_metric.get("latency", 0),
                "packet_loss": raw_metric.get("packet_loss", 0),

            },

            "status": raw_metric.get("status", "unknown"),
            "timestamp": raw_metric.get("timestamp", int(time.time()))
        }
