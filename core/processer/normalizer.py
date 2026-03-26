import re
from datetime import datetime

class NormalizerValidationError(Exception):
    pass


class Validator:

    @staticmethod
    def validate_host(host: str) -> str:
        if not isinstance(host, str):
            raise NormalizerValidationError(f"host must be a string, got {type(host).__name__}")
        host = host.strip()
        if not host:
            raise NormalizerValidationError("host must not be empty")
        if len(host) > 253:
            raise NormalizerValidationError("host must not exceed 253 characters")

        return host

    @staticmethod
    def validate_ip(ip: str) -> str:
        if ip is None:
            return None
        if not isinstance(ip, str):
            raise NormalizerValidationError(f"ip must be a string, got {type(ip).__name__}")
        ip = ip.strip()
        ipv4_regex = r"^(\d{1,3}\.){3}\d{1,3}$"
        ipv6_regex = r"^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$"
        if re.match(ipv4_regex, ip):
            parts = ip.split(".")
            if not all(0 <= int(p) <= 255 for p in parts):
                raise NormalizerValidationError(f"Invalid IPv4 address: '{ip}'")
        elif not re.match(ipv6_regex, ip):
            raise NormalizerValidationError(f"Invalid IP address format: '{ip}'")
        return ip

    @staticmethod
    def validate_mac(mac: str) -> str:
        if mac is None:
            return None
        if not isinstance(mac, str):
            raise NormalizerValidationError(f"mac_address must be a string, got {type(mac).__name__}")
        mac = mac.strip()
        mac_regex = r"^([0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2}$"
        if not re.match(mac_regex, mac):
            raise NormalizerValidationError(f"Invalid MAC address format: '{mac}'")
        return mac.upper()

    @staticmethod
    def validate_status(status: str) -> str:
        if status is None:
            return None
        if not isinstance(status, str):
            raise NormalizerValidationError(f"status must be a string, got {type(status).__name__}")
        allowed = {"up", "down"}
        status = status.strip().lower()
        if status not in allowed:
            raise NormalizerValidationError(f"status must be one of {allowed}, got '{status}'")
        return status

    @staticmethod
    def validate_device_type(device_type: str) -> str:
        if device_type is None:
            return None
        if not isinstance(device_type, str):
            raise NormalizerValidationError(f"device_type must be a string, got {type(device_type).__name__}")
        allowed = {"router", "switch", "server", "firewall", "access_point", "endpoint", "unknown"}
        device_type = device_type.strip().lower()
        if device_type not in allowed:
            raise NormalizerValidationError(f"device_type must be one of {allowed}, got '{device_type}'")
        return device_type

    @staticmethod
    def validate_percentage(value, field: str) -> float:
        if value is None:
            return None
        if not isinstance(value, (int, float)):
            raise NormalizerValidationError(f"{field} must be a number, got {type(value).__name__}")
        if not (0.0 <= float(value) <= 100.0):
            raise NormalizerValidationError(f"{field} must be between 0 and 100, got {value}")
        return float(value)

    @staticmethod
    def validate_non_negative(value, field: str) -> float:
        if value is None:
            return None
        if not isinstance(value, (int, float)):
            raise NormalizerValidationError(f"{field} must be a number, got {type(value).__name__}")
        if float(value) < 0:
            raise NormalizerValidationError(f"{field} must be non-negative, got {value}")
        return float(value)

    @staticmethod
    def validate_timestamp(timestamp) -> float:
        if isinstance(timestamp, datetime):
            return timestamp.timestamp()
        if isinstance(timestamp, (int, float)):
            if timestamp < 0:
                raise NormalizerValidationError("timestamp must be non-negative")
            if timestamp < 1e9 or timestamp > 1e11:
                raise NormalizerValidationError(f"timestamp value seems out of valid Unix range: {timestamp}")
            return float(timestamp)
        if isinstance(timestamp, str):
            try:
                return datetime.fromisoformat(timestamp).timestamp()
            except ValueError:
                raise NormalizerValidationError(f"timestamp string is not a valid ISO format: '{timestamp}'")
        raise NormalizerValidationError(f"timestamp must be a datetime, number, or ISO string, got {type(timestamp).__name__}")


class Normalizer:

    @staticmethod
    def normalize(host: str, raw_metrics: dict, tags: dict, timestamp):

        if tags is None or timestamp is None or raw_metrics is None or host is None:
            return False

        try:
            tag = {
                "hostname"     : Validator.validate_host(host),
                "ip_address"   : Validator.validate_ip(tags.get("ip")),
                "mac_address"  : Validator.validate_mac(tags.get("mac")),
                "status"       : Validator.validate_status(tags.get("status")),
                "device_type"  : Validator.validate_device_type(tags.get("device_type")),
            }

            data = {
                "cpu"          : Validator.validate_percentage(raw_metrics.get("cpu"), "cpu"),
                "ram"          : Validator.validate_percentage(raw_metrics.get("ram"), "ram"),
                "disk"         : Validator.validate_percentage(raw_metrics.get("disk"), "disk"),
                "in_bytes"     : Validator.validate_non_negative(raw_metrics.get("in_bytes"), "in_bytes"),
                "out_bytes"    : Validator.validate_non_negative(raw_metrics.get("out_bytes"), "out_bytes"),
                "in_packets"   : Validator.validate_non_negative(raw_metrics.get("in_packets"), "in_packets"),
                "out_packets"  : Validator.validate_non_negative(raw_metrics.get("out_packets"), "out_packets"),
                "in_errors"    : Validator.validate_non_negative(raw_metrics.get("in_errors"), "in_errors"),
                "out_errors"   : Validator.validate_non_negative(raw_metrics.get("out_errors"), "out_errors"),
                "latency"      : Validator.validate_non_negative(raw_metrics.get("latency"), "latency"),
                "packet_loss"  : Validator.validate_percentage(raw_metrics.get("packet_loss"), "packet_loss"),
            }

        except NormalizerValidationError:
            raise

        result = {**tag, **data, "timestamp": Validator.validate_timestamp(timestamp)}
        return result if result else False