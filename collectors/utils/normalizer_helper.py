def explode_metrics(normalized):
    metrics = []

    base = {
        "device_hostname": normalized["device"]["hostname"],
        "device_type": normalized["device"]["type"],
        "device_ip": normalized["device"]["ip"],
        "timestamp": normalized["timestamp"],
    }

    for k, v in normalized["sys"].items():
        if v is not None:
            metrics.append({**base, "value": float(v), "name": f"sys.{k}"})

    for k, v in normalized["net"].items():
        if v is not None:
            metrics.append({**base, "value": float(v), "name": f"net.{k}"})

    return metrics
