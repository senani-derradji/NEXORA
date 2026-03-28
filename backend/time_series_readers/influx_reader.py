from influxdb_client import InfluxDBClient
import os
from typing import List, Dict, Any, Optional


class InfluxReader:
    """
    Centralized InfluxDB reader for querying time-series data.
    Uses influxdb-client library instead of raw HTTP requests.
    """

    def __init__(self):
        self.url = os.getenv("INFLUXDB_URL", "http://influxdb:8086")
        self.token = os.getenv("INFLUXDB_INIT_ADMIN_TOKEN")
        self.org = os.getenv("INFLUXDB_ORG", "myorg")
        self.bucket = os.getenv("INFLUXDB_BUCKET", "dr_test")

        # Measurement name from core/time_series/models/main_model.py
        self.measurement = "DEVICE_STATS_V1"

        print(f"[InfluxReader] Init → {self.url}, bucket={self.bucket}, org={self.org}", flush=True)

        self.client = InfluxDBClient(
            url=self.url,
            token=self.token,
            org=self.org
        )

        self.query_api = self.client.query_api()

    def query(self, flux: str) -> List[Dict[str, Any]]:
        """Execute a Flux query and return structured results"""
        print("[InfluxReader] Executing query:", flush=True)
        print(flux, flush=True)

        try:
            tables = self.query_api.query(flux)
            results = []

            for table in tables:
                for record in table.records:
                    results.append({
                        "time": record.get_time(),
                        "value": record.get_value(),
                        "field": record.get_field(),
                        "device": record.values.get("device_name"),
                        "device_ip": record.values.get("device_ip"),
                        "device_type": record.values.get("device_type"),
                    })

            print(f"[InfluxReader] Retrieved {len(results)} rows", flush=True)
            return results

        except Exception as e:
            print(f"[InfluxReader][ERROR] {e}", flush=True)
            return []

    def build_query(
        self,
        field: str,
        duration: str = "1h",
        devices: Optional[List[str]] = None,
        aggregation: str = "mean",
        window: str = "1m"
    ) -> str:
        device_filter = ""
        if devices and len(devices) > 0:
            conditions = " or ".join([f'r["device_name"] == "{d}"' for d in devices])
            device_filter = f'|> filter(fn: (r) => {conditions})'

        query = f"""
from(bucket: "{self.bucket}")
  |> range(start: -{duration})
  |> filter(fn: (r) => r["_measurement"] == "{self.measurement}")
  |> filter(fn: (r) => r["_field"] == "{field}")
  {device_filter}
  |> aggregateWindow(every: {window}, fn: {aggregation}, createEmpty: false)
  |> yield(name: "{aggregation}")
"""
        print(f"[QUERY BUILDER] Field: {field}, Duration: {duration}, Devices: {devices}", flush=True)
        print("[QUERY BUILDER] Generated query:", flush=True)
        print(query, flush=True)
        return query

    def build_summary_query(
        self,
        fields: List[str],
        duration: str = "1h",
        devices: Optional[List[str]] = None
    ) -> str:
        """
        Build a query to get summary statistics (average) for multiple fields.
        Used for dashboard summary.
        """
        # Device filter
        device_filter = ""
        if devices and len(devices) > 0:
            conditions = " or ".join([f'r["device_name"] == "{d}"' for d in devices])
            device_filter = f'|> filter(fn: (r) => {conditions})'

        # Filter for specific fields
        field_conditions = " or ".join([f'r["_field"] == "{f}"' for f in fields])

        query = f"""
from(bucket: "{self.bucket}")
  |> range(start: -{duration})
  |> filter(fn: (r) => r["_measurement"] == "{self.measurement}")
  |> filter(fn: (r) => {field_conditions})
  {device_filter}
  |> group(columns: ["_field"])
  |> mean()
"""
        print(f"[SUMMARY QUERY BUILDER] Fields: {fields}, Duration: {duration}", flush=True)
        print("[SUMMARY QUERY BUILDER] Generated query:", flush=True)
        print(query, flush=True)
        return query

    def get_all_devices(self, duration: str = "24h") -> List[str]:
        """
        Get list of all unique device names from InfluxDB.
        """
        query = f"""
from(bucket: "{self.bucket}")
  |> range(start: -{duration})
  |> filter(fn: (r) => r["_measurement"] == "{self.measurement}")
  |> keep(columns: ["device_name"])
  |> distinct(column: "device_name")
"""
        try:
            tables = self.query_api.query(query)
            devices = []
            for table in tables:
                for record in table.records:
                    device = record.values.get("device_name")
                    if device and device not in devices:
                        devices.append(device)
            print(f"[InfluxReader] Found {len(devices)} devices: {devices}", flush=True)
            return devices
        except Exception as e:
            print(f"[InfluxReader][ERROR] Failed to get devices: {e}", flush=True)
            return []

    def get_latest_values(self, fields: List[str], devices: Optional[List[str]] = None) -> List[Dict[str, Any]]:

        device_filter = ""
        if devices and len(devices) > 0:
            conditions = " or ".join([f'r["device_name"] == "{d}"' for d in devices])
            device_filter = f'|> filter(fn: (r) => {conditions})'

        # Field filter
        field_conditions = " or ".join([f'r["_field"] == "{f}"' for f in fields])

        # Use a larger time range to ensure we capture latest data
        # Also use sort + limit to get most recent points per device/field
        # NOTE: Using -24h without comment to avoid # being interpreted as comment in Flux
        query = f"""
from(bucket: "{self.bucket}")
  |> range(start: -24h)
  |> filter(fn: (r) => r["_measurement"] == "{self.measurement}")
  |> filter(fn: (r) => {field_conditions})
  {device_filter}
  |> group(columns: ["device_name", "_field"])
  |> sort(columns: ["_time"], desc: true)
  |> limit(n: 1)
"""
        print("[InfluxReader] Getting latest values (sort + limit)...", flush=True)
        print(query, flush=True)

        try:
            tables = self.query_api.query(query)
            results = []

            for table in tables:
                for record in table.records:
                    results.append({
                        "time": record.get_time(),
                        "value": record.get_value(),
                        "field": record.get_field(),
                        "device": record.values.get("device_name"),
                    })

            print(f"[InfluxReader] Retrieved {len(results)} latest values", flush=True)
            return results
        except Exception as e:
            print(f"[InfluxReader][ERROR] {e}", flush=True)
            return []

    def close(self):
        """Close the InfluxDB client connection"""
        if self.client:
            self.client.close()
            print("[InfluxReader] Connection closed", flush=True)

_reader_instance = None

def get_influx_reader() -> InfluxReader:
    global _reader_instance
    if _reader_instance is None:
        _reader_instance = InfluxReader()
    return _reader_instance