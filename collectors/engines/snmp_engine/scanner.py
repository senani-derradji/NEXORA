import asyncio
import logging
import os
import re
import subprocess
from typing import Dict, List, Optional, Set

import yaml

logger = logging.getLogger('nexora.collector.scanner')


class NetworkScanner:

    SERVICE_NAMES = {
        "influxdb", "postgres", "postgresql", "core", "collectors",
        "backend", "frontend", "grafana", "redis", "rabbitmq",
        "elasticsearch", "kibana", "prometheus", "nginx", "apache",
        "mongodb", "mysql", "mariadb", "memcached", "consul",
        "vault", "traefik", "haproxy", "zookeeper", "kafka",
    }

    SERVICE_IPS = {
        "172.18.0.1",
        "172.18.0.10",
        "172.18.0.20",
        "172.18.0.30",
        "172.18.0.40",
        "172.18.0.50",
        "172.18.0.60",
    }

    def __init__(
        self,
        subnet: str = "172.18.0.0/24",
        devices_file: str = "config/devices.yml",
        default_interval: int = 15,
        bootstrapper=None,
    ):
        self.subnet = subnet
        self.devices_file = devices_file
        self.default_interval = default_interval
        self.bootstrapper = bootstrapper

    def _is_service(self, hostname: str, ip: str) -> bool:
        if ip in self.SERVICE_IPS:
            return True
        clean_name = hostname.split(".")[0].lower()
        return clean_name in self.SERVICE_NAMES

    def _clean_hostname(self, hostname: str) -> str:
        cleaned = hostname.split(".")[0]
        cleaned = re.sub(r"_\d+$", "", cleaned)
        cleaned = re.sub(r"[-_]+$", "", cleaned)
        return cleaned if cleaned else hostname

    def _detect_device_type(self, hostname: str) -> str:
        h = hostname.lower()
        if any(kw in h for kw in ("router", "rtr", "gw", "gateway")):
            return "router"
        if any(kw in h for kw in ("switch", "sw", "l2", "l3")):
            return "switch"
        if any(kw in h for kw in ("firewall", "fw", "fortinet", "palo", "checkpoint")):
            return "firewall"
        if any(kw in h for kw in ("ap", "wifi", "wireless", "wlc")):
            return "access_point"
        if any(kw in h for kw in ("server", "srv", "host")):
            return "server"
        if any(kw in h for kw in ("desktop", "pc", "workstation", "win")):
            return "workstation"
        if any(kw in h for kw in ("printer", "prt")):
            return "printer"
        if any(kw in h for kw in ("camera", "cam", "nvr", "dvr", "hikvision", "dahua")):
            return "camera"
        return "unknown"

    def _load_existing_devices(self) -> List[dict]:
        if not os.path.exists(self.devices_file):
            return []

        with open(self.devices_file, "r") as f:
            data = yaml.safe_load(f) or {}

        devices = data.get("devices", [])

        cleaned_devices = []
        for d in devices:
            d.setdefault("mac_address", "00:00:00:00:00:00")
            d.setdefault("interval", self.default_interval)

            raw_hostname = d.get("hostname", "unknown")
            hostname = self._clean_hostname(raw_hostname)

            if d.get("device_type", "unknown") == "unknown":
                device_type = self._detect_device_type(hostname)
            else:
                device_type = d["device_type"]

            cleaned_devices.append({
                "ip_address": d["ip_address"],
                "hostname": hostname,
                "device_type": device_type,
                "mac_address": d["mac_address"],
                "interval": d["interval"],
            })

        return cleaned_devices

    def _save_devices(self, devices: List[dict]) -> None:
        os.makedirs(os.path.dirname(self.devices_file), exist_ok=True)

        db_ips = self._load_existing_ips_from_db()

        merged: Dict[str, dict] = {}
        for d in devices:
            ip = d["ip_address"]
            if ip in merged:
                merged[ip].update(d)
            else:
                merged[ip] = dict(d)

        cleaned = []
        for d in merged.values():
            ip = d["ip_address"]
            hostname = d.get("hostname", "unknown")
            if ip in db_ips:
                continue
            if self._is_service(hostname, ip):
                continue
            cleaned.append({
                "ip_address": ip,
                "interval": d.get("interval", self.default_interval),
                "hostname": self._clean_hostname(hostname),
                "device_type": d.get("device_type", self._detect_device_type(hostname)),
                "mac_address": d.get("mac_address", "00:00:00:00:00:00"),
            })

        with open(self.devices_file, "w") as f:
            yaml.dump({"devices": cleaned}, f, default_flow_style=False, sort_keys=False)

    def _nmap_discover(self) -> List[dict]:
        try:
            result = subprocess.run(
                ["nmap", "-sn", "--min-parallelism", "10", self.subnet],
                capture_output=True,
                text=True,
                timeout=120,
            )
            output = result.stdout
        except FileNotFoundError:
            logger.error("nmap not found. Install nmap or add it to PATH.")
            return []
        except subprocess.TimeoutExpired:
            logger.error("nmap scan timed out.")
            return []

        devices: List[dict] = []
        blocks = re.split(r"\n(?=Nmap scan report for )", output)

        for block in blocks:
            if "Host is up" not in block:
                continue

            ip_match = re.search(r"Nmap scan report for (?:([\w.\-]+)\s+)?\((\d+\.\d+\.\d+\.\d+)\)", block)
            if not ip_match:
                ip_match = re.search(r"Nmap scan report for (\d+\.\d+\.\d+\.\d+)", block)
                if not ip_match:
                    continue
                ip = ip_match.group(1)
                raw_hostname = f"device-{ip.replace('.', '-')}"
            else:
                ip = ip_match.group(2)
                raw_hostname = ip_match.group(1) if ip_match.group(1) else f"device-{ip.replace('.', '-')}"

            if self._is_service(raw_hostname, ip):
                logger.debug(f"Skipping service: {raw_hostname} ({ip})")
                continue

            hostname = self._clean_hostname(raw_hostname)
            device_type = self._detect_device_type(hostname)

            mac_match = re.search(r"MAC Address:\s+([0-9A-Fa-f:]{17})", block)
            mac = mac_match.group(1) if mac_match else "00:00:00:00:00:00"

            devices.append({
                "ip_address": ip,
                "interval": self.default_interval,
                "hostname": hostname,
                "device_type": device_type,
                "mac_address": mac,
            })

        return devices

    def _load_existing_ips_from_db(self) -> Set[str]:
        if self.bootstrapper is None:
            return set()
        try:
            db_devices = self.bootstrapper._load_db_devices()
            return {d["ip_address"] for d in db_devices}
        except Exception as e:
            logger.warning(f"Could not load DB devices: {e}")
            return set()

    def _load_existing_macs_from_db(self) -> Set[str]:
        if self.bootstrapper is None:
            return set()
        try:
            db_devices = self.bootstrapper._load_db_devices()
            return {d["mac_address"] for d in db_devices if d.get("mac_address")}
        except Exception as e:
            logger.warning(f"Could not load DB devices: {e}")
            return set()

    def scan(self) -> List[dict]:
        existing = self._load_existing_devices()
        existing = [d for d in existing if not self._is_service(d["hostname"], d["ip_address"])]

        yaml_ips: Set[str] = {d["ip_address"] for d in existing}
        yaml_macs: Set[str] = {d.get("mac_address", "") for d in existing if d.get("mac_address")}

        db_ips = self._load_existing_ips_from_db()
        db_macs = self._load_existing_macs_from_db()

        known_ips = yaml_ips | db_ips
        known_macs = yaml_macs | db_macs

        logger.info(f"Scanning {self.subnet} with nmap...")
        live_hosts = self._nmap_discover()
        logger.info(f"nmap found {len(live_hosts)} live host(s)")

        discovered: List[dict] = []
        for device in live_hosts:
            ip = device["ip_address"]
            mac = device.get("mac_address", "00:00:00:00:00:00")
            if ip not in known_ips and mac not in known_macs:
                logger.info(f"New device: {device['hostname']} ({ip})")
                discovered.append(device)
            else:
                logger.debug(f"Skipping known device: {device['hostname']} ({ip})")

        if discovered:
            all_devices = existing + discovered
            self._save_devices(all_devices)
            logger.info(f"Added {len(discovered)} new device(s) to {self.devices_file}")
        else:
            logger.info("No new devices discovered")

        return discovered

    async def scan_async(self) -> List[dict]:
        return await asyncio.to_thread(self.scan)


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

    parser = argparse.ArgumentParser(description="NEXORA Network Scanner")
    parser.add_argument("--subnet", default="172.18.0.0/24", help="Subnet to scan (e.g. 172.18.0.0/24)")
    parser.add_argument("--devices-file", default="/collectors/config/devices.yml", help="Path to devices.yml")
    parser.add_argument("--interval", type=int, default=15, help="Default polling interval in seconds")
    args = parser.parse_args()

    scanner = NetworkScanner(
        subnet=args.subnet,
        devices_file=args.devices_file,
        default_interval=args.interval,
    )

    discovered = scanner.scan()
    print(f"Discovered {len(discovered)} new device(s).")
