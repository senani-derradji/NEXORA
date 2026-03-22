from pysnmp.hlapi import *
import subprocess
import re
import time
from typing import Dict, Tuple, Optional, Any
from dataclasses import dataclass
import logging


@dataclass
class SNMPConfig:
    community: str = "public"
    port: int = 161
    timeout: int = 2
    retries: int = 1
    mp_model: int = 1


@dataclass
class DeviceMetrics:
    device_host: str
    device_type: str
    device_ip: str
    device_mac: str
    cpu: Optional[float]
    ram: Optional[float]
    disk: Optional[float]
    in_bytes: float
    out_bytes: float
    in_packets: float
    out_packets: float
    in_errors: float
    out_errors: float
    latency: Optional[float]
    packet_loss: float
    status: bool
    timestamp: int


class SNMPMonitor:

    OID_CPU_IDLE = "1.3.6.1.4.1.2021.11.11.0"
    OID_MEM_TOTAL = "1.3.6.1.4.1.2021.4.5.0"
    OID_MEM_AVAIL = "1.3.6.1.4.1.2021.4.6.0"
    OID_DISK_SIZE = "1.3.6.1.2.1.25.2.3.1.5"
    OID_DISK_USED = "1.3.6.1.2.1.25.2.3.1.6"

    OID_IF_OPER = "1.3.6.1.2.1.2.2.1.8"
    OID_IF_IN_OCTETS = "1.3.6.1.2.1.2.2.1.10"
    OID_IF_OUT_OCTETS = "1.3.6.1.2.1.2.2.1.16"
    OID_IF_IN_PACKETS = "1.3.6.1.2.1.2.2.1.11"
    OID_IF_OUT_PACKETS = "1.3.6.1.2.1.2.2.1.17"
    OID_IF_IN_ERRORS = "1.3.6.1.2.1.2.2.1.14"
    OID_IF_OUT_ERRORS = "1.3.6.1.2.1.2.2.1.20"
    OID_IF_MAC = "1.3.6.1.2.1.2.2.1.6"

    OID_SYS_DESCR = "1.3.6.1.2.1.1.1.0"
    OID_SYS_OBJECT_ID = "1.3.6.1.2.1.1.2.0"

    IF_STATUS_UP = 1
    LOOPBACK_INTERFACE_INDEX = "1"

    def __init__(self, config: Optional["SNMPConfig"] = None):
        self.config = config or SNMPConfig()
        # Suppress verbose SNMP transport logs
        self.logger = logging.getLogger('nexora.collector.snmp')
        self.logger.setLevel(logging.WARNING)  # Only log warnings and errors


    def snmp_get(self, ip: str, oid: str) -> Tuple[Any, bool]:

        try:
            iterator = getCmd(
                SnmpEngine(),
                CommunityData(self.config.community, mpModel=self.config.mp_model),
                UdpTransportTarget(
                    (ip, self.config.port),
                    timeout=self.config.timeout,
                    retries=self.config.retries
                ),
                ContextData(),
                ObjectType(ObjectIdentity(oid)),
            )

            error_indication, error_status, error_index, var_binds = next(iterator)

            if error_indication or error_status:
                self.logger.warning(
                    f"SNMP GET failed for {ip} OID {oid}: "
                    f"{error_indication or error_status}"
                )
                return None, False

            return var_binds[0][1], True

        except Exception as e:
            self.logger.debug(f"SNMP GET exception for {ip}: {e}")
            return None, False


    def snmp_walk(self, ip: str, oid: str) -> Dict[str, Any]:

        results = {}

        try:
            for (error_indication, error_status, error_index, var_binds) in nextCmd(
                SnmpEngine(),
                CommunityData(self.config.community, mpModel=self.config.mp_model),
                UdpTransportTarget(
                    (ip, self.config.port),
                    timeout=self.config.timeout,
                    retries=self.config.retries
                ),
                ContextData(),
                ObjectType(ObjectIdentity(oid)),
                lexicographicMode=False,
            ):
                if error_indication or error_status:
                    self.logger.warning(
                        f"SNMP WALK failed for {ip} OID {oid}: "
                        f"{error_indication or error_status}"
                    )
                    break

                for var_bind in var_binds:
                    results[str(var_bind[0])] = var_bind[1]

        except Exception as e:
            self.logger.error(f"SNMP WALK exception for {ip}: {e}")

        return results

    def ping_device(self, ip: str, count: int = 3) -> Tuple[Optional[float], float]:

        try:
            output = subprocess.check_output(
                ["ping", "-c", str(count), ip],
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                timeout=10
            )

            loss_match = re.search(r"(\d+)% packet loss", output)
            packet_loss = float(loss_match.group(1)) if loss_match else 100.0

            rtt_match = re.search(r"rtt .* = .*?/([\d.]+)/", output)
            latency = float(rtt_match.group(1)) if rtt_match else None

            return latency, packet_loss

        except subprocess.TimeoutExpired:
            self.logger.warning(f"Ping timeout for {ip}")
            return None, 100.0
        except Exception as e:
            self.logger.error(f"Ping failed for {ip}: {e}")
            return None, 100.0

    def _get_cpu_usage(self, ip: str) -> Optional[float]:

        cpu_idle, sec = self.snmp_get(ip, self.OID_CPU_IDLE)
        print(f'''

              CPU IDLE : {cpu_idle}
              Type : {type(cpu_idle)}

              ''')

        # Check if we got valid data
        if not sec or cpu_idle is None:
            self.logger.warning(f"CPU idle query failed for {ip}")
            return None

        # Handle different SNMP response types
        try:
            # Handle bytes or string values from SNMP
            if isinstance(cpu_idle, (bytes, str)):
                # Empty bytes/string means no data
                if cpu_idle in (b'', ''):
                    return None
                cpu_idle = float(cpu_idle)

            # Handle SNMP Integer types (including Boolean-like integers)
            elif isinstance(cpu_idle, int):
                cpu_idle = float(cpu_idle)

            # Handle other types (like SNMP Integer32)
            else:
                cpu_idle = float(cpu_idle)

            # Validate the value is in reasonable range (0-100)
            if cpu_idle < 0 or cpu_idle > 100:
                self.logger.warning(f"CPU idle value out of range: {cpu_idle}")
                return None

            # CPU usage = 100 - CPU idle (SNMP returns idle %, we want usage %)
            cpu_usage = 100.0 - cpu_idle
            return cpu_usage
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Failed to parse CPU idle value: {cpu_idle}, error: {e}")
            return None


    def _get_memory_usage(self, ip: str) -> Optional[float]:

        mem_total, total_ok = self.snmp_get(ip, self.OID_MEM_TOTAL)
        mem_avail, avail_ok = self.snmp_get(ip, self.OID_MEM_AVAIL)

        if total_ok and avail_ok and mem_total and mem_avail:
            try:
                total = int(mem_total)
                avail = int(mem_avail)
                usage = 100 * (total - avail) / total
                return float(round(usage, 2))
            except (ValueError, TypeError, ZeroDivisionError):
                return None
        return None

    def _get_disk_usage(self, ip: str) -> Optional[float]:
        disk_size = self.snmp_walk(ip, self.OID_DISK_SIZE)
        disk_used = self.snmp_walk(ip, self.OID_DISK_USED)

        if not disk_size:
            return None

        try:
            first_oid = list(disk_size.keys())[0]
            idx = first_oid.split(".")[-1]
            size = int(disk_size[f"{self.OID_DISK_SIZE}.{idx}"])
            used = int(disk_used[f"{self.OID_DISK_USED}.{idx}"])

            if size > 0:
                return float(round(100 * used / size, 2))
        except (ValueError, KeyError, IndexError, ZeroDivisionError):
            pass

        return None

    def _get_interface_stats(self, ip: str) -> Dict[str, Any]:

        stats = {
            'in_bytes': 0,
            'out_bytes': 0,
            'in_packets': 0,
            'out_packets': 0,
            'in_errors': 0,
            'out_errors': 0,
            'mac_address': None
        }

        oper_status = self.snmp_walk(ip, self.OID_IF_OPER)

        for oid, status in oper_status.items():
            idx = oid.split(".")[-1]

            if int(status) == self.IF_STATUS_UP and idx != self.LOOPBACK_INTERFACE_INDEX:
                try:
                    stats['in_bytes'] = int(self.snmp_get(ip, f"{self.OID_IF_IN_OCTETS}.{idx}")[0])
                    stats['out_bytes'] = int(self.snmp_get(ip, f"{self.OID_IF_OUT_OCTETS}.{idx}")[0])
                    stats['in_packets'] = int(self.snmp_get(ip, f"{self.OID_IF_IN_PACKETS}.{idx}")[0])
                    stats['out_packets'] = int(self.snmp_get(ip, f"{self.OID_IF_OUT_PACKETS}.{idx}")[0])
                    stats['in_errors'] = int(self.snmp_get(ip, f"{self.OID_IF_IN_ERRORS}.{idx}")[0])
                    stats['out_errors'] = int(self.snmp_get(ip, f"{self.OID_IF_OUT_ERRORS}.{idx}")[0])

                    mac_raw = self.snmp_get(ip, f"{self.OID_IF_MAC}.{idx}")[0]
                    stats['mac_address'] = ":".join(["%02x" % x for x in bytes(mac_raw)])
                except (ValueError, TypeError, AttributeError):
                    pass

                break

        return stats

    def collect_device_metrics(
        self,
        hostname: str,
        device_type: str,
        ip: str,
        mac_placeholder: str = "00:00:00:00:00:00"
    ) -> Dict[str, Any]:

        self.logger.info(f"Collecting metrics for {hostname} ({ip})")

        # First, check if device is reachable via ping
        latency, packet_loss = self.ping_device(ip)

        # If device is down (100% packet loss), skip SNMP checks and return DOWN status
        if packet_loss >= 100.0:
            self.logger.warning(f"Device {hostname} ({ip}) is DOWN - skipping SNMP collection")
            return {
                "hostname": hostname,
                "device_type": device_type,
                "device_ip": ip,
                "device_mac": mac_placeholder,

                "cpu": None,
                "ram": None,
                "disk": None,

                "in_bytes": 0,
                "out_bytes": 0,
                "in_packets": 0,
                "out_packets": 0,
                "in_errors": 0,
                "out_errors": 0,

                "latency": None,
                "packet_loss": 100.0,

                "status": "down",
                "timestamp": int(time.time()),
            }

        # Device is up, collect SNMP metrics
        cpu = self._get_cpu_usage(ip)
        ram = self._get_memory_usage(ip)
        disk = self._get_disk_usage(ip)

        interface_stats = self._get_interface_stats(ip)

        # Determine status based on packet loss and latency
        # UP: packet_loss < 100% and latency is available
        # DOWN: packet_loss >= 100% or no latency
        if packet_loss >= 100.0 or latency is None:
            status = "down"
        else:
            status = "up"

        result = {
            "hostname": hostname,
            "device_type": device_type,
            "device_ip": ip,
            "device_mac": interface_stats['mac_address'] or mac_placeholder,

            "cpu": cpu,
            "ram": ram,
            "disk": disk,

            "in_bytes": float(interface_stats['in_bytes']),
            "out_bytes": float(interface_stats['out_bytes']),
            "in_packets": float(interface_stats['in_packets']),
            "out_packets": float(interface_stats['out_packets']),
            "in_errors": float(interface_stats['in_errors']),
            "out_errors": float(interface_stats['out_errors']),

            "latency": float(latency) if latency else None,
            "packet_loss": float(packet_loss),

            "status": status,  # Returns "up" or "down"
            "timestamp": int(time.time()),
        }
        return result


    def collect_metrics_as_dataclass(
        self,
        hostname: str,
        device_type: str,
        ip: str,
        mac_placeholder: str = "00:00:00:00:00:00"
    ):

        metrics = self.collect_device_metrics(hostname, device_type, ip, mac_placeholder)
        return metrics