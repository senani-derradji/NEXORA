
class Normalizer:

    @staticmethod
    def normalize(host: str, raw_metrics: dict, tags: dict, timestamp):
        __net_devices = ["router", "switch", "firewall"]
        __os_devices = ["server", "access_point", "printer"]

        if tags is None or timestamp is None or raw_metrics is None or host is None:
            return False

        tag = {
                "hostname" : host,
                "ip_address" : tags.get("ip"),
                "mac_address" : tags.get("mac"),
                "status" : tags.get("status"),
                "device_type" : tags.get("device_type"),
                }



        if tags.get("device_type") in __net_devices:
            data = {
                    "cpu" : raw_metrics.get("cpu"),
                    "ram" : raw_metrics.get("ram"),
                    "in_bytes" : raw_metrics.get("in_bytes"),
                    "out_bytes" : raw_metrics.get("out_bytes"),
                    "in_packets" : raw_metrics.get("in_packets"),
                    "out_packets" : raw_metrics.get("out_packets"),
                    "in_errors" : raw_metrics.get("in_errors"),
                    "out_errors" : raw_metrics.get("out_errors"),
                    "latency" : raw_metrics.get("latency"),
                    "packet_loss" : raw_metrics.get("packet_loss"),
                }

        elif tags.get("device_type") in __os_devices:
            data = {
                    "cpu" : raw_metrics.get("cpu"),
                    "ram" : raw_metrics.get("ram"),
                    "disk" : raw_metrics.get("disk"),
                    "latency" : raw_metrics.get("latency"),
                    "packet_loss" : raw_metrics.get("packet_loss")
                    }

        else:
            return False

        return {**tag, **data, "timestamp" : timestamp}
