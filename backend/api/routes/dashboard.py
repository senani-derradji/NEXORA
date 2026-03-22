from fastapi import APIRouter, Depends, HTTPException
from nexora_db.operations.devices_ops import DeviceOperations
from nexora_db.operations.alerts_ops import AlertOperations
from security.jwt import get_current_user
from config import init
from datetime import datetime, timedelta, timezone
from utils.logger import setup_logger
import os
import json
from time_series_readers.influx_reader import InfluxReader, get_influx_reader

# Setup logger
logger = setup_logger('backend.dashboard', level=20)

init(url_env="DATABASE_URL")

device_ops = DeviceOperations()
alert_ops = AlertOperations()
router = APIRouter()

def _require_admin_or_viewer():
    """Allow both admin and viewer roles"""
    def role_checker(user: dict = Depends(get_current_user)):
        if user["role"] not in ["admin", "viewer"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return role_checker

def _is_device_online(device):
    """Check if device is online based on status and last_seen"""
    now = datetime.now(timezone.utc)

    # Check the status field (up, down)
    device_status = str(device.status).upper() if device.status else ""

    # Device is DOWN if status explicitly says so
    if device_status == "DOWN":
        return False

    # Device is UP if status says so
    if device_status == "UP":
        # Also verify last_seen is recent (within 30 seconds)
        if device.last_seen:
            # Handle timezone-aware vs naive datetime comparison
            last_seen = device.last_seen
            if last_seen.tzinfo is None:
                # Naive datetime from DB - assume UTC
                last_seen = last_seen.replace(tzinfo=timezone.utc)

            if (now - last_seen).total_seconds() < 30:
                return True
        # If no recent last_seen but status is UP, still consider online
        return True

    # Fallback: check last_seen
    if device.last_seen:
        last_seen = device.last_seen
        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        return (now - last_seen).total_seconds() < 30
    return False


def _get_influx_metrics():
    """Try to get metrics from InfluxDB using InfluxReader, return default values if unavailable"""
    try:
        reader = get_influx_reader()

        # Use InfluxReader's get_latest_values method to get all metrics
        fields = ['cpu_usage', 'ram_usage', 'disk_usage', 'latency']
        data = reader.get_latest_values(fields)

        print(f"[DASHBOARD] InfluxDB latest values: {len(data)} rows", flush=True)

        # Organize data by device - SKIP zero values as they're likely placeholders
        devices_data = {}
        for item in data:
            device_name = item.get('device')
            if not device_name:
                continue

            if device_name not in devices_data:
                devices_data[device_name] = {}

            field = item.get('field')
            value = item.get('value')

            # Skip zero values - they're placeholder data
            if field and value is not None and value != 0.0:
                try:
                    devices_data[device_name][field] = float(value)
                except (ValueError, TypeError):
                    pass

        print(f"[DASHBOARD] Devices data (non-zero): {devices_data}", flush=True)

        # Calculate averages - if no non-zero data, try using whatever we have
        count = len(devices_data)
        if count > 0:
            total_cpu = sum(d.get('cpu_usage', 0) or 0 for d in devices_data.values())
            total_ram = sum(d.get('ram_usage', 0) or 0 for d in devices_data.values())
            total_disk = sum(d.get('disk_usage', 0) or 0 for d in devices_data.values())
            total_latency = sum(d.get('latency', 0) or 0 for d in devices_data.values())

            print(f"[DASHBOARD] Avg CPU: {total_cpu / count}, Avg RAM: {total_ram / count}", flush=True)

            return {
                'avg_cpu': total_cpu / count,
                'avg_ram': total_ram / count,
                'avg_disk': total_disk / count,
                'avg_latency': total_latency / count,
                'has_influx': True
            }
        else:
            # If all zero, try with original data (including zeros)
            for item in data:
                device_name = item.get('device')
                if not device_name:
                    continue
                if device_name not in devices_data:
                    devices_data[device_name] = {}
                field = item.get('field')
                value = item.get('value')
                if field and value is not None:
                    try:
                        devices_data[device_name][field] = float(value)
                    except (ValueError, TypeError):
                        pass

            count = len(devices_data)
            if count > 0:
                total_cpu = sum(d.get('cpu_usage', 0) for d in devices_data.values())
                total_ram = sum(d.get('ram_usage', 0) for d in devices_data.values())
                total_disk = sum(d.get('disk_usage', 0) for d in devices_data.values())
                total_latency = sum(d.get('latency', 0) for d in devices_data.values())
                print(f"[DASHBOARD] Fallback - Avg CPU: {total_cpu / count}", flush=True)
                return {
                    'avg_cpu': total_cpu / count,
                    'avg_ram': total_ram / count,
                    'avg_disk': total_disk / count,
                    'avg_latency': total_latency / count,
                    'has_influx': True
                }

            print("[DASHBOARD] No device data found in InfluxDB", flush=True)

    except Exception as e:
        print(f"[DASHBOARD] InfluxDB error: {e}", flush=True)

    # Return default values if InfluxDB is not available
    return {
        'avg_cpu': 0,
        'avg_ram': 0,
        'avg_disk': 0,
        'avg_latency': 0,
        'has_influx': False
    }


@router.get("/summary")
def get_dashboard_summary(user: dict = Depends(_require_admin_or_viewer())):
    """Get dashboard summary with device counts, alerts, and metrics"""

    # Get device counts from PostgreSQL
    devices = device_ops.get_all_devices()
    total_devices = len(devices)
    online_devices = sum(1 for d in devices if _is_device_online(d))

    # Get alerts count
    alerts = alert_ops.get_all_alerts()
    active_alerts = len(alerts) if alerts else 0

    # Calculate critical and warning counts
    critical_alerts = 0
    warning_alerts = 0
    if alerts:
        for alert in alerts:
            level = str(alert.alert_level).upper() if alert.alert_level else ''
            if level in ['CRITICAL', 'HIGH']:
                critical_alerts += 1
            elif level in ['WARNING', 'MID']:
                warning_alerts += 1

    # Get metrics from InfluxDB (or return defaults)
    metrics = _get_influx_metrics()

    # Calculate system health (percentage of online devices)
    system_health = (online_devices / total_devices * 100) if total_devices > 0 else 100

    return {
        "total_devices": total_devices,
        "online_devices": online_devices,
        "offline_devices": total_devices - online_devices,
        "active_alerts": active_alerts,
        "critical_alerts": critical_alerts,
        "warning_alerts": warning_alerts,
        "system_health": round(system_health, 1),
        "avg_cpu": round(metrics['avg_cpu'], 1),
        "avg_ram": round(metrics['avg_ram'], 1),
        "avg_disk": round(metrics['avg_disk'], 1),
        "avg_latency": round(metrics['avg_latency'], 2)
    }


@router.get("/device-metrics")
def get_device_metrics(user: dict = Depends(_require_admin_or_viewer())):
    """Get metrics for all devices with their latest readings"""

    # Get devices from PostgreSQL
    devices = device_ops.get_all_devices()

    # Initialize device_metrics as empty dict (default when InfluxDB unavailable)
    device_metrics = {}

    # Try to get metrics from InfluxDB using InfluxReader
    try:
        reader = get_influx_reader()

        # Get latest values for all devices
        fields = ['cpu_usage', 'ram_usage', 'disk_usage', 'latency', 'status']
        data = reader.get_latest_values(fields)

        print(f"[DASHBOARD] Device metrics from InfluxDB: {len(data)} rows", flush=True)

        # Organize data by device
        for item in data:
            device_name = item.get('device')
            if not device_name:
                continue

            if device_name not in device_metrics:
                device_metrics[device_name] = {
                    'cpu_usage': None,
                    'ram_usage': None,
                    'disk_usage': None,
                    'latency': None,
                    'status': 'unknown'
                }

            field = item.get('field')
            value = item.get('value')

            if field and value is not None:
                try:
                    float_val = float(value)
                    if field == 'cpu_usage':
                        device_metrics[device_name]['cpu_usage'] = float_val
                    elif field == 'ram_usage':
                        device_metrics[device_name]['ram_usage'] = float_val
                    elif field == 'disk_usage':
                        device_metrics[device_name]['disk_usage'] = float_val
                    elif field == 'latency':
                        device_metrics[device_name]['latency'] = float_val
                    elif field == 'status':
                        device_metrics[device_name]['status'] = 'UP' if float_val == 1 else 'DOWN'
                except (ValueError, TypeError):
                    pass

        print(f"[DASHBOARD] Parsed device metrics: {device_metrics}", flush=True)

    except Exception as e:
        print(f"[DASHBOARD] Error querying InfluxDB: {e}", flush=True)

    # Build response
    device_list = []
    for device in devices:
        device_name = device.hostname
        metrics = device_metrics.get(device_name, {
            'cpu_usage': None,
            'ram_usage': None,
            'disk_usage': None,
            'latency': None,
            'status': 'unknown'
        })

        # Override with PostgreSQL status if available
        db_status = 'UP' if _is_device_online(device) else 'DOWN'

        device_list.append({
            'id': device.id,
            'hostname': device.hostname,
            'ip_address': device.ip_address,
            'mac_address': device.mac_address,
            'device_type': device.device_type,
            'status': db_status,
            'status_value': 1 if db_status == 'UP' else 0,
            'status_text': device.status,
            'last_seen': device.last_seen.isoformat() if device.last_seen else None,
            'cpu_usage': metrics.get('cpu_usage'),
            'ram_usage': metrics.get('ram_usage'),
            'disk_usage': metrics.get('disk_usage'),
            'latency': metrics.get('latency'),
        })

    return {"devices": device_list}


@router.get("/topology")
def get_topology(user: dict = Depends(_require_admin_or_viewer())):
    """Get network topology with devices"""

    # Get devices from PostgreSQL
    devices = device_ops.get_all_devices()

    # Build device nodes from database
    device_nodes = []
    for device in devices:
        is_online = _is_device_online(device)
        device_nodes.append({
            'id': str(device.id),
            'name': device.hostname,
            'type': 'device',
            'status': 'online' if is_online else 'offline',
            'ip': device.ip_address,
            'mac': device.mac_address,
            'device_type': device.device_type
        })

    # Return topology structure
    return {
        'core': {
            'id': 'core',
            'name': 'Core',
            'type': 'core',
            'status': 'online',
            'ip': '172.18.0.30'
        },
        'collector': {
            'id': 'collector',
            'name': 'Collector',
            'type': 'collector',
            'status': 'online',
            'ip': '172.18.0.40'
        },
        'databases': [
            {
                'id': 'postgres',
                'name': 'PostgreSQL',
                'type': 'postgres',
                'status': 'online',
                'ip': '172.18.0.20'
            },
            {
                'id': 'influxdb',
                'name': 'InfluxDB',
                'type': 'influxdb',
                'status': 'online',
                'ip': '172.18.0.10'
            }
        ],
        'devices': device_nodes
    }


@router.get("/metrics/history")
def get_metrics_history(
    device: str = None,
    metric: str = "cpu_usage",
    duration: str = "1h",
    user: dict = Depends(_require_admin_or_viewer())
):
    """Get time-series metrics history from InfluxDB"""
    try:
        import os
        import requests
        from datetime import datetime, timedelta

        influx_url = os.getenv('INFLUXDB_URL', 'http://influxdb:8086')
        influx_bucket = os.getenv('INFLUXDB_BUCKET', 'dr_test')
        influx_token = os.getenv('INFLUXDB_ADMIN_TOKEN', os.getenv('INFLUXDB_INIT_ADMIN_TOKEN', ''))

        # Parse duration
        duration_map = {
            '5m': '5m',
            '15m': '15m',
            '1h': '1h',
            '6h': '6h',
            '24h': '24h',
            '7d': '7d'
        }
        duration_str = duration_map.get(duration, '1h')

        # Build Flux query
        device_filter = f'r.device_name == "{device}"' if device else ''

        query = f'''
from(bucket: "{influx_bucket}")
  |> range(start: -{duration_str})
  |> filter(fn: (r) => r._measurement == "DEVICE_STATS_V1")
  '''

        if device_filter:
            query += f'  |> filter(fn: (r) => r._name == "{metric}" and {device_filter})'
        else:
            query += f'  |> filter(fn: (r) => r._name == "{metric}")'

        query += '''
  |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
  |> yield(name: "mean")
        '''

        # Use v2 API with token auth
        query_url = f"{influx_url}/api/v2/query"
        params = {
            'org': 'myorg',
            'bucket': influx_bucket,
        }
        headers = {
            'Authorization': f'Token {influx_token}',
            'Content-Type': 'application/vnd.flux'
        }

        response = requests.post(query_url, params=params, headers=headers, data=query, timeout=10)

        if response.status_code == 200:
            result = response.json()
            # Parse InfluxDB v2 response
            data = []
            if 'results' in result:
                for table in result.get('results', []):
                    for row in table.get('data', []):
                        data.append({
                            'time': row.get('_time'),
                            'value': row.get('_value')
                        })
            return {
                'metric': metric,
                'device': device,
                'duration': duration,
                'data': data
            }
        else:
            return {
                'error': f'InfluxDB query failed: {response.status_code}',
                'data': []
            }
    except Exception as e:
        return {
            'error': str(e),
            'data': []
        }


@router.get("/metrics/current")
def get_current_metrics(
    user: dict = Depends(_require_admin_or_viewer())
):
    """Get current metrics for all devices from InfluxDB"""
    try:
        import os
        import requests

        influx_url = os.getenv('INFLUXDB_URL', 'http://influxdb:8086')
        influx_bucket = os.getenv('INFLUXDB_BUCKET', 'dr_test')
        influx_token = os.getenv('INFLUXDB_ADMIN_TOKEN', os.getenv('INFLUXDB_INIT_ADMIN_TOKEN', ''))

        # Query for last value of each metric
        query = f'''
from(bucket: "{influx_bucket}")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "DEVICE_STATS_V1")
  |> last()
  |> group(columns: ["_name", "device_name"])
  |> yield(name: "last")
        '''

        query_url = f"{influx_url}/api/v2/query"
        params = {
            'org': 'myorg',
            'bucket': influx_bucket,
        }
        headers = {
            'Authorization': f'Token {influx_token}',
            'Content-Type': 'application/vnd.flux'
        }

        response = requests.post(query_url, params=params, headers=headers, data=query, timeout=10)

        if response.status_code == 200:
            result = response.json()
            # Parse response into device metrics
            devices = {}

            if 'results' in result:
                for table in result.get('results', []):
                    for row in table.get('data', []):
                        device_name = row.get('device_name', 'unknown')
                        metric_name = row.get('_name', '')
                        value = row.get('_value')

                        if device_name not in devices:
                            devices[device_name] = {
                                'device_name': device_name,
                                'cpu_usage': None,
                                'ram_usage': None,
                                'disk_usage': None,
                                'latency': None,
                                'packet_loss': None,
                                'in_bytes': None,
                                'out_bytes': None,
                            }

                        if metric_name == 'cpu_usage':
                            devices[device_name]['cpu_usage'] = value
                        elif metric_name == 'ram_usage':
                            devices[device_name]['ram_usage'] = value
                        elif metric_name == 'disk_usage':
                            devices[device_name]['disk_usage'] = value
                        elif metric_name == 'latency':
                            devices[device_name]['latency'] = value
                        elif metric_name == 'packet_loss_percent':
                            devices[device_name]['packet_loss'] = value
                        elif metric_name == 'in_bytes':
                            devices[device_name]['in_bytes'] = value
                        elif metric_name == 'out_bytes':
                            devices[device_name]['out_bytes'] = value

            return {
                'devices': list(devices.values())
            }
        else:
            return {
                'error': f'InfluxDB query failed: {response.status_code}',
                'devices': []
            }
    except Exception as e:
        return {
            'error': str(e),
            'devices': []
        }
