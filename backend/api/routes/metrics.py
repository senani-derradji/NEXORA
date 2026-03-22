from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
from security.jwt import get_current_user
from config import init
from time_series_readers.influx_reader import InfluxReader, get_influx_reader
from utils.logger import setup_logger

# Setup logger
logger = setup_logger('backend.metrics', level=20)

init(url_env="DATABASE_URL")
router = APIRouter()

# Duration mappings
DURATION_MAP = {
    '5m': '5m',
    '15m': '15m',
    '30m': '30m',
    '1h': '1h',
    '6h': '6h',
    '24h': '24h',
    '7d': '7d'
}

# Aggregation intervals based on duration
AGGREGATION_MAP = {
    '5m': '10s',
    '15m': '30s',
    '30m': '1m',
    '1h': '1m',
    '6h': '5m',
    '24h': '15m',
    '7d': '1h'
}


def _require_admin_or_viewer():
    """Allow both admin and viewer roles"""
    def role_checker(user: dict = Depends(get_current_user)):
        if user["role"] not in ["admin", "viewer"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return role_checker


# Helper to get reader instance
def _get_reader() -> InfluxReader:
    """Get InfluxReader instance"""
    return get_influx_reader()


def _get_aggregation_window(duration: str) -> str:
    """Get aggregation window based on duration"""
    return AGGREGATION_MAP.get(duration, '1m')


def _build_flux_query(
    field: str,
    duration: str = '1h',
    device_filter: Optional[str] = None
) -> str:
    """Build a Flux query for a specific metric field using InfluxReader"""
    reader = _get_reader()
    devices = [device_filter] if device_filter else None
    window = _get_aggregation_window(duration)

    return reader.build_query(
        field=field,
        duration=duration,
        devices=devices,
        aggregation='mean',
        window=window
    )


# ============================================
# FLUX QUERIES FOR EACH METRIC
# ============================================

# Field name mapping - core writes: cpu_usage, ram_usage, disk_usage, in_bytes, out_bytes, latency, packet_loss_percent

def get_cpu_query(duration: str = '1h', device: Optional[str] = None) -> str:
    """Flux query for CPU usage - field name is 'cpu_usage'"""
    return _build_flux_query('cpu_usage', duration, device)


def get_ram_query(duration: str = '1h', device: Optional[str] = None) -> str:
    """Flux query for RAM usage - field name is 'ram_usage'"""
    return _build_flux_query('ram_usage', duration, device)


def get_disk_query(duration: str = '1h', device: Optional[str] = None) -> str:
    """Flux query for disk usage - field name is 'disk_usage'"""
    return _build_flux_query('disk_usage', duration, device)


def get_network_in_query(duration: str = '1h', device: Optional[str] = None) -> str:
    """Flux query for network inbound bytes"""
    return _build_flux_query('in_bytes', duration, device)


def get_network_out_query(duration: str = '1h', device: Optional[str] = None) -> str:
    """Flux query for network outbound bytes"""
    return _build_flux_query('out_bytes', duration, device)


def get_latency_query(duration: str = '1h', device: Optional[str] = None) -> str:
    """Flux query for latency"""
    return _build_flux_query('latency', duration, device)


def get_packet_loss_query(duration: str = '1h', device: Optional[str] = None) -> str:
    """Flux query for packet loss - field name is 'packet_loss_percent'"""
    return _build_flux_query('packet_loss_percent', duration, device)


# ============================================
# HELPER FUNCTIONS
# ============================================

def _organize_by_device(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Organize flat data into device-structured format"""
    device_map: Dict[str, List[Dict[str, Any]]] = {}

    for item in data:
        # InfluxReader returns 'device' key for device_name
        device_name = item.get('device') or item.get('device_name', 'unknown')
        if device_name not in device_map:
            device_map[device_name] = []

        device_map[device_name].append({
            "timestamp": item.get('time'),
            "value": item.get('value')
        })

    # Convert to list format
    result = []
    for device_name, points in device_map.items():
        result.append({
            "device": device_name,
            "data": points
        })

    return result


def _merge_network_data(
    in_data: List[Dict[str, Any]],
    out_data: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Merge inbound and outbound network data by timestamp"""
    merged: Dict[str, Dict[str, Any]] = {}

    for point in in_data:
        ts = str(point.get('timestamp'))
        if ts:
            if ts not in merged:
                merged[ts] = {"timestamp": point.get('timestamp')}
            merged[ts]["value_in"] = point.get('value') or 0

    for point in out_data:
        ts = str(point.get('timestamp'))
        if ts:
            if ts not in merged:
                merged[ts] = {"timestamp": point.get('timestamp')}
            merged[ts]["value_out"] = point.get('value') or 0

    # Ensure all points have both value_in and value_out (default to 0 if missing)
    for ts, merged_point in merged.items():
        if "value_in" not in merged_point:
            merged_point["value_in"] = 0
        if "value_out" not in merged_point:
            merged_point["value_out"] = 0
        print(f"[NETWORK MERGE] {merged_point}", flush=True)

    return list(merged.values())


def _combine_network_data(
    in_by_device: Dict[str, List],
    out_by_device: Dict[str, List]
) -> List[Dict[str, Any]]:
    """Combine network data for all devices"""
    all_devices = set(in_by_device.keys()) | set(out_by_device.keys())
    result = []

    for device in all_devices:
        result.append({
            "device": device,
            "data": _merge_network_data(
                in_by_device.get(device, []),
                out_by_device.get(device, [])
            )
        })

    return result


# ============================================
# API ENDPOINTS
# ============================================

@router.get("/cpu")
def get_cpu_metrics(
    duration: str = Query('1h', regex='^(5m|15m|30m|1h|6h|24h|7d)$'),
    device: Optional[str] = None,
    user: dict = Depends(_require_admin_or_viewer())
):
    """Get CPU usage metrics for all devices"""
    reader = _get_reader()
    query = get_cpu_query(duration, device)
    data = reader.query(query)

    print(f"[API] CPU metrics result: {data[:5] if data else 'No data'}", flush=True)

    devices_data = _organize_by_device(data)

    return {
        "metric": "cpu",
        "duration": duration,
        "devices": devices_data
    }


@router.get("/ram")
def get_ram_metrics(
    duration: str = Query('1h', regex='^(5m|15m|30m|1h|6h|24h|7d)$'),
    device: Optional[str] = None,
    user: dict = Depends(_require_admin_or_viewer())
):
    """Get RAM usage metrics for all devices"""
    reader = _get_reader()
    query = get_ram_query(duration, device)
    data = reader.query(query)

    print(f"[API] RAM metrics result: {data[:5] if data else 'No data'}", flush=True)

    devices_data = _organize_by_device(data)

    return {
        "metric": "ram",
        "duration": duration,
        "devices": devices_data
    }


@router.get("/disk")
def get_disk_metrics(
    duration: str = Query('1h', regex='^(5m|15m|30m|1h|6h|24h|7d)$'),
    device: Optional[str] = None,
    user: dict = Depends(_require_admin_or_viewer())
):
    """Get disk usage metrics for all devices"""
    reader = _get_reader()
    query = get_disk_query(duration, device)
    data = reader.query(query)

    print(f"[API] Disk metrics result: {data[:5] if data else 'No data'}", flush=True)

    devices_data = _organize_by_device(data)

    return {
        "metric": "disk",
        "duration": duration,
        "devices": devices_data
    }


@router.get("/network")
def get_network_metrics(
    duration: str = Query('1h', regex='^(5m|15m|30m|1h|6h|24h|7d)$'),
    device: Optional[str] = None,
    user: dict = Depends(_require_admin_or_viewer())
):
    """Get network metrics (in/out bytes) for all devices"""
    reader = _get_reader()

    # Query both inbound and outbound
    in_query = get_network_in_query(duration, device)
    out_query = get_network_out_query(duration, device)

    in_data = reader.query(in_query)
    out_data = reader.query(out_query)

    print(f"[API] Network in result: {len(in_data)} rows", flush=True)
    print(f"[API] Network out result: {len(out_data)} rows", flush=True)

    # Organize by device
    in_by_device_list = _organize_by_device(in_data)
    out_by_device_list = _organize_by_device(out_data)

    # Convert list to dict for easier access
    in_by_device = {item['device']: item['data'] for item in in_by_device_list}
    out_by_device = {item['device']: item['data'] for item in out_by_device_list}

    # Combine into network structure
    all_devices = set(in_by_device.keys()) | set(out_by_device.keys())
    devices_list = []

    for dev in all_devices:
        devices_list.append({
            "device": dev,
            "data": _merge_network_data(
                in_by_device.get(dev, []),
                out_by_device.get(dev, [])
            )
        })

    return {
        "metric": "network",
        "duration": duration,
        "devices": devices_list
    }


@router.get("/latency")
def get_latency_metrics(
    duration: str = Query('1h', regex='^(5m|15m|30m|1h|6h|24h|7d)$'),
    device: Optional[str] = None,
    user: dict = Depends(_require_admin_or_viewer())
):
    """Get latency metrics for all devices"""
    reader = _get_reader()
    query = get_latency_query(duration, device)
    data = reader.query(query)

    print(f"[API] Latency metrics result: {data[:5] if data else 'No data'}", flush=True)

    devices_data = _organize_by_device(data)

    return {
        "metric": "latency",
        "duration": duration,
        "devices": devices_data
    }


@router.get("/packet-loss")
def get_packet_loss_metrics(
    duration: str = Query('1h', regex='^(5m|15m|30m|1h|6h|24h|7d)$'),
    device: Optional[str] = None,
    user: dict = Depends(_require_admin_or_viewer())
):
    """Get packet loss metrics for all devices"""
    reader = _get_reader()
    query = get_packet_loss_query(duration, device)
    data = reader.query(query)

    print(f"[API] Packet loss metrics result: {data[:5] if data else 'No data'}", flush=True)

    devices_data = _organize_by_device(data)

    return {
        "metric": "packet_loss",
        "duration": duration,
        "devices": devices_data
    }


@router.get("/all")
def get_all_metrics(
    duration: str = Query('1h', regex='^(5m|15m|30m|1h|6h|24h|7d)$'),
    user: dict = Depends(_require_admin_or_viewer())
):
    """Get all metrics at once for dashboard overview"""
    reader = _get_reader()

    # Query all metrics
    cpu_query = get_cpu_query(duration)
    ram_query = get_ram_query(duration)
    disk_query = get_disk_query(duration)
    latency_query = get_latency_query(duration)
    packet_loss_query = get_packet_loss_query(duration)
    network_in_query = get_network_in_query(duration)
    network_out_query = get_network_out_query(duration)

    # Execute queries sequentially
    cpu_data = reader.query(cpu_query)
    ram_data = reader.query(ram_query)
    disk_data = reader.query(disk_query)
    latency_data = reader.query(latency_query)
    packet_loss_data = reader.query(packet_loss_query)
    network_in_data = reader.query(network_in_query)
    network_out_data = reader.query(network_out_query)

    print(f"[API] All metrics - CPU: {len(cpu_data)}, RAM: {len(ram_data)}, Disk: {len(disk_data)}", flush=True)

    return {
        "metric": "all",
        "duration": duration,
        "cpu": {"metric": "cpu", "devices": _organize_by_device(cpu_data)},
        "ram": {"metric": "ram", "devices": _organize_by_device(ram_data)},
        "disk": {"metric": "disk", "devices": _organize_by_device(disk_data)},
        "latency": {"metric": "latency", "devices": _organize_by_device(latency_data)},
        "packet_loss": {"metric": "packet_loss", "devices": _organize_by_device(packet_loss_data)},
        "network": {
            "metric": "network",
            "devices": _combine_network_data(
                {item['device']: item['data'] for item in _organize_by_device(network_in_data)},
                {item['device']: item['data'] for item in _organize_by_device(network_out_data)}
            )
        }
    }
