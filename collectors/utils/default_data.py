def down_metric(device):
    import time

    down_metric = {
    "device_host": device["hostname"], "device_type": device["device_type"], "device_ip": device["ip_address"], "device_mac": device["mac_address"],
    "cpu": 0.0, "ram": 0.0,"disk": 0.0 if device["device_type"] == " server" else "",
    "in_net_bytes": 0.0, "out_net_bytes": 0.0,
    "in_net_packets": 0.0, "out_net_packets": 0.0,
    "in_net_errors": 0.0, "out_net_errors": 0.0,
    "latency": 0.0, "packet_loss": 0.0,
    "status": "DOWN",
    "timestamp": int(time.time()),
            }
    return down_metric