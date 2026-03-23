from pysnmp.hlapi import getCmd, setCmd, nextCmd, bulkCmd, SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity
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

    # Default OIDs for Linux/Unix (UCD-SNMP-MIB)
    # Using RAW OIDs that work on modern Linux systems
    # These are counter values that need to be sampled over time to calculate percentage
    OID_CPU_RAW_USER = "1.3.6.1.4.1.2021.11.9.0"    # ssCpuRawUser - counter
    OID_CPU_RAW_SYSTEM = "1.3.6.1.4.1.2021.11.10.0"  # ssCpuRawSystem - counter
    OID_CPU_RAW_IDLE = "1.3.6.1.4.1.2021.11.11.0"   # ssCpuRawIdle - counter
    OID_CPU_RAW_NICE = "1.3.6.1.4.1.2021.11.12.0"   # ssCpuRawNice - counter

    # Legacy percentage OID (may not work on modern systems)
    OID_CPU_IDLE_LEGACY = "1.3.6.1.4.1.2021.11.11.0"  # Deprecated - uses ssCpuIdle which is often unavailable

    # HOST-RESOURCES-MIB for system uptime/processes
    OID_HR_SYSTEM_UPTIME = "1.3.6.1.2.1.25.1.1.0"  # hrSystemUptime
    OID_HR_SYSTEM_PROCESSES = "1.3.6.1.2.1.25.1.6.0"  # hrSystemProcesses
    OID_MEM_TOTAL = "1.3.6.1.4.1.2021.4.5.0"
    OID_MEM_AVAIL = "1.3.6.1.4.1.2021.4.6.0"
    OID_DISK_SIZE = "1.3.6.1.2.1.25.2.3.1.5"
    OID_DISK_USED = "1.3.6.1.2.1.25.2.3.1.6"

    # Device-type specific CPU OIDs
    # Cisco CPU OIDs (various models)
    OID_CISCO_CPU = "1.3.6.1.4.1.9.2.1.58.0"  # Old Cisco IOS
    OID_CISCO_CPU_2 = "1.3.6.1.4.1.9.9.109.1.1.1.1.7.1"  # Cisco IOS-XE
    OID_CISCO_CPU_3 = "1.3.6.1.4.1.9.9.109.1.1.1.1.8.1"  # Cisco IOS-XE (5min)

    # Juniper CPU OID
    OID_JUNIPER_CPU = "1.3.6.1.4.1.2636.3.1.13.1.5.1.6.0"

    # HP/Aruba CPU OID
    OID_HP_CPU = "1.3.6.1.4.1.11.2.14.11.5.1.1.6.1.0"

    # Dell CPU OID
    OID_DELL_CPU = "1.3.6.1.4.1.674.10895.5000.1.1.1.0"

    # Mikrotik CPU OID
    OID_MIKROTIK_CPU = "1.3.6.1.4.1.14988.1.1.1.1.0"

    # Network interface OIDs (standard)
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

    # CPU OID mapping for different vendors
    # Linux uses RAW counters which require time-based sampling
    CPU_OID_MAP = {
        'cisco': [OID_CISCO_CPU, OID_CISCO_CPU_2, OID_CISCO_CPU_3],
        'juniper': [OID_JUNIPER_CPU],
        'hp': [OID_HP_CPU],
        'dell': [OID_DELL_CPU],
        'mikrotik': [OID_MIKROTIK_CPU],
        'linux': [OID_CPU_RAW_USER, OID_CPU_RAW_IDLE],
        'server': [OID_CPU_RAW_USER, OID_CPU_RAW_IDLE],
        'router': [OID_CPU_RAW_USER, OID_CPU_RAW_IDLE],
        'unix': [OID_CPU_RAW_USER, OID_CPU_RAW_IDLE],
        # Fallback to legacy if needed
        'default': [OID_CPU_RAW_USER, OID_CPU_RAW_IDLE, OID_CPU_IDLE_LEGACY],
    }

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
                UdpTransportTarget((ip, self.config.port), timeout=self.config.timeout, retries=self.config.retries),
                ContextData(),
                ObjectType(ObjectIdentity(oid)),
            )

            errorIndication, errorStatus, errorIndex, varBinds = next(iterator)

            if errorIndication:
                self.logger.warning(
                    f"SNMP GET failed for {ip} OID {oid}: "
                    f"{errorIndication}"
                )
                return None, False

            if errorStatus:
                self.logger.warning(
                    f"SNMP GET failed for {ip} OID {oid}: "
                    f"{errorStatus.prettyPrint()} at "
                    f"{errorIndex and varBinds[int(errorIndex) - 1][0] or '?'}"
                )
                return None, False

            for varBind in varBinds:
                return varBind[1], True

            return None, False

        except Exception as e:
            self.logger.error(f"SNMP GET exception for {ip} OID {oid}: {e}")
            return None, False


    def snmp_walk(self, ip: str, oid: str) -> Dict[str, Any]:

        results = {}

        try:
            iterator = nextCmd(
                SnmpEngine(),
                CommunityData(self.config.community, mpModel=self.config.mp_model),
                UdpTransportTarget((ip, self.config.port), timeout=self.config.timeout, retries=self.config.retries),
                ContextData(),
                ObjectType(ObjectIdentity(oid)),
                lexicographicMode=False,
            )

            for errorIndication, errorStatus, errorIndex, varBinds in iterator:

                if errorIndication:
                    self.logger.warning(
                        f"SNMP WALK failed for {ip} OID {oid}: "
                        f"{errorIndication}"
                    )
                    break

                if errorStatus:
                    self.logger.warning(
                        f"SNMP WALK failed for {ip} OID {oid}: "
                        f"{errorStatus.prettyPrint()} at "
                        f"{errorIndex and varBinds[int(errorIndex) - 1][0] or '?'}"
                    )
                    break

                for varBind in varBinds:
                    results[str(varBind[0])] = varBind[1]

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

    def _get_cpu_usage(self, ip: str, device_type: str = "linux") -> Optional[float]:
        """
        Get CPU usage for the device. Tries multiple OIDs based on device type.

        For Linux systems with UCD-SNMP-MIB, uses RAW counters which require
        sampling over time to calculate CPU percentage.

        Args:
            ip: Device IP address
            device_type: Type of device (linux, cisco, juniper, hp, dell, mikrotik, etc.)
        """

        # Normalize device type
        device_type = device_type.lower() if device_type else "linux"

        # Get list of OIDs to try for this device type
        oids_to_try = self.CPU_OID_MAP.get(device_type, self.CPU_OID_MAP.get('default', [self.OID_CPU_RAW_USER]))

        # For Linux/Unix systems, try to use RAW counters with time-based calculation
        if device_type in ('linux', 'server', 'router', 'unix'):
            cpu_usage = self._get_cpu_from_raw_counters(ip)
            if cpu_usage is not None:
                return cpu_usage

        # Fallback: try legacy OIDs or vendor-specific OIDs
        # Also always try the legacy OID as fallback
        legacy_oids = [self.OID_CPU_IDLE_LEGACY]
        for oid in legacy_oids:
            if oid not in oids_to_try:
                oids_to_try.append(oid)

        # Try each OID until one works
        for oid in oids_to_try:
            cpu_idle, sec = self.snmp_get(ip, oid)
            self.logger.debug(f"CPU query for {ip} OID {oid}: {cpu_idle}")

            # Check if we got valid data
            if sec and cpu_idle is not None and cpu_idle not in (b'', ''):
                try:
                    # Handle bytes or string values from SNMP
                    if isinstance(cpu_idle, (bytes, str)):
                        cpu_idle = float(cpu_idle)
                    elif isinstance(cpu_idle, int):
                        cpu_idle = float(cpu_idle)
                    else:
                        cpu_idle = float(cpu_idle)

                    # Validate the value is in reasonable range (0-100)
                    if 0 <= cpu_idle <= 100:
                        # CPU usage = 100 - CPU idle (assuming idle percentage)
                        # For some devices, the OID might return usage directly
                        if cpu_idle > 0 and cpu_idle <= 100:
                            cpu_usage = 100.0 - cpu_idle
                            return cpu_usage
                        elif cpu_idle == 0:
                            return 0.0
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"Failed to parse CPU value from {oid}: {cpu_idle}, error: {e}")
                    continue

        self.logger.warning(f"CPU query failed for {ip} (device type: {device_type}) - tried OIDs: {oids_to_try}")
        return None

    def _get_cpu_from_raw_counters(self, ip: str) -> Optional[float]:
        """
        Calculate CPU usage from RAW counters (UCD-SNMP-MIB).

        RAW counters are cumulative values that need to be sampled twice
        over a time interval to calculate the percentage.

        Returns CPU usage as a percentage (0-100).
        """
        def parse_cpu_value(value):
            """Parse CPU value from SNMP response - handle bytes, strings, and empty values."""
            if value is None:
                return None
            if isinstance(value, bytes):
                value = value.decode('utf-8').strip()
            if isinstance(value, str):
                value = value.strip()
            if not value or value == b'' or value == '':
                return None
            return int(value)

        try:
            # First sample - get all CPU counters
            cpu_user_1, ok1 = self.snmp_get(ip, self.OID_CPU_RAW_USER)
            cpu_system_1, ok2 = self.snmp_get(ip, self.OID_CPU_RAW_SYSTEM)
            cpu_idle_1, ok3 = self.snmp_get(ip, self.OID_CPU_RAW_IDLE)
            cpu_nice_1, ok4 = self.snmp_get(ip, self.OID_CPU_RAW_NICE)

            if not all([ok1, ok2, ok3, ok4]):
                self.logger.debug(f"RAW CPU counters not available for {ip}")
                return None

            # Convert to integers with proper handling
            try:
                user_1 = parse_cpu_value(cpu_user_1)
                system_1 = parse_cpu_value(cpu_system_1)
                idle_1 = parse_cpu_value(cpu_idle_1)
                nice_1 = parse_cpu_value(cpu_nice_1)

                if any(v is None for v in [user_1, system_1, idle_1, nice_1]):
                    self.logger.warning(f"Failed to parse RAW CPU counters: some values were empty")
                    return None
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Failed to parse RAW CPU counters: {e}")
                return None

            # Wait a short interval for counter delta calculation
            time.sleep(0.5)

            # Second sample
            cpu_user_2, _ = self.snmp_get(ip, self.OID_CPU_RAW_USER)
            cpu_system_2, _ = self.snmp_get(ip, self.OID_CPU_RAW_SYSTEM)
            cpu_idle_2, _ = self.snmp_get(ip, self.OID_CPU_RAW_IDLE)
            cpu_nice_2, _ = self.snmp_get(ip, self.OID_CPU_RAW_NICE)

            # Parse second sample values
            user_2 = parse_cpu_value(cpu_user_2)
            system_2 = parse_cpu_value(cpu_system_2)
            idle_2 = parse_cpu_value(cpu_idle_2)
            nice_2 = parse_cpu_value(cpu_nice_2)

            if any(v is None for v in [user_2, system_2, idle_2, nice_2]):
                self.logger.warning(f"Failed to parse second RAW CPU sample")
                return None

            # Calculate deltas
            user_delta = user_2 - user_1
            system_delta = system_2 - system_1
            idle_delta = idle_2 - idle_1
            nice_delta = nice_2 - nice_1

            # Total CPU time = user + system + idle + nice
            total_delta = user_delta + system_delta + idle_delta + nice_delta

            if total_delta <= 0:
                self.logger.debug(f"Invalid CPU delta for {ip}: total={total_delta}")
                return None

            # CPU usage = 100 * (total - idle) / total
            # Or equivalently: 100 * (user + system + nice) / total
            cpu_usage = 100.0 * (user_delta + system_delta + nice_delta) / total_delta

            # Validate result is in reasonable range
            if 0 <= cpu_usage <= 100:
                self.logger.debug(f"CPU usage for {ip}: {cpu_usage:.2f}% (from RAW counters)")
                return round(cpu_usage, 2)
            else:
                self.logger.warning(f"CPU usage out of range for {ip}: {cpu_usage}")
                return None

        except Exception as e:
            self.logger.warning(f"Error calculating CPU from RAW counters for {ip}: {e}")
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

        if not disk_size or not disk_used:
            return None

        try:
            total = 0
            used = 0

            for oid, value in disk_size.items():
                idx = oid.split(".")[-1]
                size = int(disk_size[oid])
                used += int(disk_used.get(f"{self.OID_DISK_USED}.{idx}", 0))
                total += size

            if total > 0:
                usage = 100 * used / total
                return float(round(usage, 2))
        except (ValueError, TypeError, ZeroDivisionError):
            pass

        return None

    def _get_interface_stats(self, ip: str) -> Dict[str, Any]:

        stats = {
            "in_bytes": 0,
            "out_bytes": 0,
            "in_packets": 0,
            "out_packets": 0,
            "in_errors": 0,
            "out_errors": 0,
        }

        try:
            oper_status = self.snmp_walk(ip, self.OID_IF_OPER)

            for oid, status in oper_status.items():
                idx = oid.split(".")[-1]

                if int(status) != self.IF_STATUS_UP:
                    continue

                # Get byte counters for this interface
                in_octets = self.snmp_get(ip, f"{self.OID_IF_IN_OCTETS}.{idx}")
                out_octets = self.snmp_get(ip, f"{self.OID_IF_OUT_OCTETS}.{idx}")

                in_packets_val = self.snmp_get(ip, f"{self.OID_IF_IN_PACKETS}.{idx}")
                out_packets_val = self.snmp_get(ip, f"{self.OID_IF_OUT_PACKETS}.{idx}")

                in_errors_val = self.snmp_get(ip, f"{self.OID_IF_IN_ERRORS}.{idx}")
                out_errors_val = self.snmp_get(ip, f"{self.OID_IF_OUT_ERRORS}.{idx}")

                # Skip loopback
                if idx == self.LOOPBACK_INTERFACE_INDEX:
                    continue

                if in_octets[1]:
                    stats["in_bytes"] += int(in_octets[0])
                if out_octets[1]:
                    stats["out_bytes"] += int(out_octets[0])
                if in_packets_val[1]:
                    stats["in_packets"] += int(in_packets_val[0])
                if out_packets_val[1]:
                    stats["out_packets"] += int(out_packets_val[0])
                if in_errors_val[1]:
                    stats["in_errors"] += int(in_errors_val[0])
                if out_errors_val[1]:
                    stats["out_errors"] += int(out_errors_val[0])

        except Exception as e:
            self.logger.error(f"Error getting interface stats for {ip}: {e}")

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

        # Device is up, collect SNMP metrics - pass device_type for OID selection
        cpu = self._get_cpu_usage(ip, device_type)
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
            "device_mac": mac_placeholder,

            "cpu": cpu,
            "ram": ram,
            "disk": disk,

            "in_bytes": interface_stats["in_bytes"],
            "out_bytes": interface_stats["out_bytes"],
            "in_packets": interface_stats["in_packets"],
            "out_packets": interface_stats["out_packets"],
            "in_errors": interface_stats["in_errors"],
            "out_errors": interface_stats["out_errors"],

            "latency": latency,
            "packet_loss": packet_loss,

            "status": status,
            "timestamp": int(time.time()),
        }

        return result

    # Alias for backward compatibility with scheduler
    def collect_metrics_as_dataclass(self, hostname: str, device_type: str, ip: str, mac_placeholder: str = "00:00:00:00:00:00") -> Dict[str, Any]:
        """Alias for collect_device_metrics - kept for backward compatibility."""
        return self.collect_device_metrics(hostname, device_type, ip, mac_placeholder)
