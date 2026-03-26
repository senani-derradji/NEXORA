#!/bin/bash

# NEXORA Pre-Start Device Check Script
# This script validates devices before starting the collector
# Uses existing SNMP engine with async SNMP queries

set -e

CONFIG_FILE="/collectors/config/devices.yml"
LOG_FILE="/collectors/pre_start_check.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_info() {
    log "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    log "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    log "${RED}[ERROR]${NC} $1"
}

# Check if devices.yml exists
check_file_exists() {
    log_info "Checking if $CONFIG_FILE exists..."
    if [ ! -f "$CONFIG_FILE" ]; then
        log_error "File $CONFIG_FILE does not exist!"
        exit 1
    fi
    log_info "File $CONFIG_FILE exists."
}

# Validate YAML format
validate_yaml_format() {
    log_info "Validating YAML format..."

    # DEBUG: Show first few lines of the file
    log_info "DEBUG: First 10 lines of $CONFIG_FILE:"
    head -n 10 "$CONFIG_FILE" | while read -r line; do
        log_info "DEBUG LINE: '$line'"
    done

    # DEBUG: Check what patterns match
    log_info "DEBUG: Checking for 'ip:' pattern..."
    if grep -qE "^[[:space:]]*- ip:" "$CONFIG_FILE"; then
        log_info "DEBUG: Found '- ip:' pattern"
    else
        log_info "DEBUG: Did NOT find '- ip:' pattern"
    fi

    if grep -qE "ip_address:" "$CONFIG_FILE"; then
        log_info "DEBUG: Found 'ip_address:' pattern"
    else
        log_info "DEBUG: Did NOT find 'ip_address:' pattern"
    fi

    # DEBUG: Show all lines containing 'ip'
    log_info "DEBUG: Lines containing 'ip':"
    grep -E "ip" "$CONFIG_FILE" | while read -r line; do
        log_info "DEBUG: '$line'"
    done

    if ! head -n 1 "$CONFIG_FILE" | grep -q "^devices:"; then
        log_error "Invalid YAML format: File must start with 'devices:'"
        exit 1
    fi

    # Fixed: Use parentheses to ensure correct operator precedence
    if (! grep -qE "^[[:space:]]*- ip:" "$CONFIG_FILE") && (! grep -qE "ip_address:" "$CONFIG_FILE"); then
        log_error "Invalid YAML format: No devices with ip found"
        exit 1
    fi

    log_info "YAML format is valid."
}

# Process all devices using Python with async SNMP
process_devices() {
    log_info "Processing devices from $CONFIG_FILE..."

    python3 << 'PYTHON_SCRIPT'
import yaml
import sys
import subprocess
import re
import time
import asyncio
import logging
import os

# Add paths to import existing SNMP utils
sys.path.insert(0, '/collectors')
sys.path.insert(0, '/collectors/engines')
sys.path.insert(0, '/collectors/engines/snmp_engine')

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

CONFIG_FILE = "/collectors/config/devices.yml"
TEMP_FILE = "/tmp/devices_updated.yml"

# Import existing SNMP engine utilities
try:
    from engines.snmp_engine.utils.detect_type import detect_device_type
    from engines.snmp_engine.utils.detect_vendor import detect_vendor
    from engines.snmp_engine.snmp_collector import SNMPMonitor, SNMPConfig
    logger.info("Successfully imported SNMP engine utils")
    SNMP_UTILS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Could not import SNMP utils: {e}")
    SNMP_UTILS_AVAILABLE = False

# OIDs
OID_SYS_OBJECT_ID = "1.3.6.1.2.1.1.2.0"
OID_SYS_NAME = "1.3.6.1.2.1.1.5.0"
OID_SYS_DESCR = "1.3.6.1.2.1.1.1.0"

def log_info(msg):
    print(f"[INFO] {msg}")

def log_warn(msg):
    print(f"[WARN] {msg}")

def log_error(msg):
    print(f"[ERROR] {msg}")

async def get_device_info_async(ip, community="public", timeout=5):
    """Get device info via SNMP using async calls"""
    info = {
        'hostname': '',
        'device_type': 'unknown',
        'vendor': 'unknown',
        'description': '',
        'snmp_available': False
    }

    if not SNMP_UTILS_AVAILABLE:
        return info

    try:
        config = SNMPConfig(community=community, timeout=timeout)
        monitor = SNMPMonitor(config=config)

        # Use asyncio.to_thread for SNMP queries
        sys_name, name_ok = await asyncio.to_thread(
            monitor.snmp_get, ip, OID_SYS_NAME
        )

        if name_ok and sys_name:
            info['snmp_available'] = True
            info['hostname'] = str(sys_name)

        # Get sysObjectID for device type and vendor
        sys_object_id, oid_ok = await asyncio.to_thread(
            monitor.snmp_get, ip, OID_SYS_OBJECT_ID
        )

        if oid_ok and sys_object_id:
            # Convert to tuple format expected by detect_type/detect_vendor
            oid_tuple = (str(sys_object_id),)

            # Get device type
            if SNMP_UTILS_AVAILABLE:
                try:
                    info['device_type'] = detect_device_type(oid_tuple)
                except Exception as e:
                    logger.warning(f"detect_type error: {e}")

            # Get vendor
            if SNMP_UTILS_AVAILABLE:
                try:
                    info['vendor'] = detect_vendor(oid_tuple)
                except Exception as e:
                    logger.warning(f"detect_vendor error: {e}")

        # Get sysDescr
        sys_descr, desc_ok = await asyncio.to_thread(
            monitor.snmp_get, ip, OID_SYS_DESCR
        )

        if desc_ok and sys_descr:
            info['description'] = str(sys_descr)

    except Exception as e:
        logger.warning(f"SNMP error for {ip}: {e}")

    return info

def ping_device(ip, timeout=30, interval=5):
    """Ping a device and return True if reachable"""
    log_info(f"Pinging {ip} (timeout: {timeout}s)...")
    elapsed = 0
    while elapsed < timeout:
        try:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "2", ip],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                log_info(f"{ip} is reachable")
                return True
        except Exception:
            pass
        time.sleep(interval)
        elapsed += interval
    log_warn(f"{ip} is not reachable after {timeout}s")
    return False

def get_mac_address(ip):
    """Get MAC address from ARP cache"""
    mac = ""
    try:
        subprocess.run(["ping", "-c", "1", "-W", "1", ip],
                      capture_output=True, timeout=5)
        time.sleep(1)

        result = subprocess.run(["arp", "-n", ip], capture_output=True, text=True)
        match = re.search(r'([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}', result.stdout)
        if match:
            return match.group(0).lower()

        result = subprocess.run(["ip", "neigh", "show", ip], capture_output=True, text=True)
        match = re.search(r'([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}', result.stdout)
        if match:
            return match.group(0).lower()
    except Exception as e:
        log_warn(f"Error getting MAC for {ip}: {e}")
    return mac

def detect_device_type_from_hostname(hostname):
    """Fallback: detect device type from hostname patterns"""
    hostname_lower = hostname.lower() if hostname else ""

    if any(x in hostname_lower for x in ['win', 'windows', 'desktop', 'pc']):
        return "workstation"
    elif any(x in hostname_lower for x in ['server', 'srv']):
        return "server"
    elif any(x in hostname_lower for x in ['router', 'rtr', 'gw']):
        return "router"
    elif any(x in hostname_lower for x in ['switch', 'sw']):
        return "switch"
    elif any(x in hostname_lower for x in ['firewall', 'fw']):
        return "firewall"
    return "unknown"

async def process_single_device(device):
    """Process a single device asynchronously"""
    # DIAGNOSTIC: Log input device data to understand what fields are provided
    log_info(f"DEBUG INPUT: device = {device}")

    ip = device.get('ip') or device.get('ip_address')
    if not ip:
        log_warn(f"DEBUG: No IP found in device: {device}")
        return None, None, None

    log_info(f"DEBUG: Found IP = {ip}")

    # DIAGNOSTIC: Check what optional fields are provided in input
    input_hostname = device.get('hostname')
    input_mac = device.get('mac') or device.get('mac_address')
    input_device_type = device.get('device_type')
    input_interval = device.get('interval')

    log_info(f"DEBUG INPUT FIELDS: hostname='{input_hostname}', mac='{input_mac}', device_type='{input_device_type}', interval={input_interval}")

    # Ping first
    if not ping_device(ip, timeout=30, interval=5):
        return ip, None, "not_reachable"

    # Get MAC - FIRST check if provided in input, then try ARP
    mac = input_mac if input_mac else get_mac_address(ip)
    log_info(f"DEBUG MAC: input_mac='{input_mac}', arp_mac='{get_mac_address(ip)}', final_mac='{mac}'")

    # Get SNMP info asynchronously
    snmp_info = await get_device_info_async(ip, community="public", timeout=5)

    # DIAGNOSTIC: Log SNMP-detected values
    log_info(f"DEBUG SNMP: snmp_info = {snmp_info}")

    # Use input hostname if provided, otherwise use SNMP/reverse DNS/generated
    hostname = snmp_info.get('hostname', '')

    # If no hostname from SNMP, try reverse DNS
    if not hostname:
        try:
            result = subprocess.run(["host", ip], capture_output=True, text=True, timeout=5)
            if 'domain name pointer' in result.stdout:
                hostname = result.stdout.split('domain name pointer')[1].strip().rstrip('.')
        except Exception:
            pass

    # If still no hostname, use input hostname or generate default
    if not hostname:
        hostname = input_hostname if input_hostname else f"device_{ip.replace('.', '_')}"

    log_info(f"DEBUG HOSTNAME: snmp_hostname='{snmp_info.get('hostname', '')}', input_hostname='{input_hostname}', final_hostname='{hostname}'")

    # Use input device_type if provided, otherwise use SNMP/hostname detection
    device_type = snmp_info.get('device_type', 'unknown')
    vendor = snmp_info.get('vendor', 'unknown')

    # Check if SNMP available
    snmp_available = snmp_info.get('snmp_available', False)

    # If device_type unknown or not provided in input, use hostname detection
    if device_type == 'unknown' or not input_device_type:
        detected_type = detect_device_type_from_hostname(hostname)
        device_type = input_device_type if input_device_type else detected_type

    log_info(f"DEBUG DEVICE_TYPE: snmp_type='{snmp_info.get('device_type', 'unknown')}', input_type='{input_device_type}', detected='{detect_device_type_from_hostname(hostname)}', final='{device_type}'")

    # Combine hostname with vendor: {hostname}_{vendor}
    if vendor and vendor != 'unknown':
        base_hostname = hostname.split('.')[0]
        hostname = f"{base_hostname}_{vendor}"

    # Truncate hostname to 20 chars
    hostname = hostname.split('.')[0]
    if len(hostname) > 20:
        hostname = hostname[:20]

    # Truncate device_type
    device_type = str(device_type)[:20]

    # Get interval - use input if provided, otherwise default
    interval = input_interval if input_interval else device.get('interval', 15)

    log_info(f"DEBUG INTERVAL: input_interval={input_interval}, default=15, final={interval}")

    working_device = {
        'ip_address': ip,
        'hostname': hostname,
        'mac_address': mac if mac else '',
        'device_type': device_type,
        'interval': interval
    }

    log_info(f"DEBUG OUTPUT: working_device = {working_device}")

    snmp_status = "SNMP OK" if snmp_available else "SNMP N/A"
    log_info(f"Working device: {hostname} ({ip}) - Type: {device_type} - {snmp_status}")

    return working_device, None, None

async def main():
    log_info("="*50)
    log_info("NEXORA Pre-Start Device Check")
    log_info("Using SNMP engine utils with asyncio")
    log_info("="*50)

    with open(CONFIG_FILE, 'r') as f:
        data = yaml.safe_load(f)

    if not data or 'devices' not in data:
        log_error("Invalid YAML format: 'devices' key not found")
        sys.exit(1)

    devices = data['devices']
    working_devices = []
    failed_devices = []
    snmp_unavailable = []

    log_info(f"Processing {len(devices)} devices...")

    # Process devices asynchronously
    tasks = [process_single_device(device) for device in devices]
    results = await asyncio.gather(*tasks)

    for result in results:
        if result[0]:  # working_device
            working_devices.append(result[0])
        elif result[1]:  # failed ip
            failed_devices.append(result[1])

    # Create updated data
    updated_data = {'devices': working_devices}

    with open(TEMP_FILE, 'w') as f:
        yaml.dump(updated_data, f, default_flow_style=False, sort_keys=False)

    log_info("="*50)
    log_info(f"Working devices: {len(working_devices)}")
    log_info(f"Failed devices: {len(failed_devices)}")

    if failed_devices:
        log_warn(f"Failed IPs: {', '.join(failed_devices)}")

    import shutil
    shutil.move(TEMP_FILE, CONFIG_FILE)
    log_info(f"Updated {CONFIG_FILE}")
    log_info("="*50)

    if not working_devices:
        log_error("No working devices found! Exiting.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
PYTHON_SCRIPT

    if [ $? -ne 0 ]; then
        log_error "Failed to process devices"
        exit 1
    fi

    log_info "Device processing completed successfully"
}

# Main execution
main() {
    log_info "========================================="
    log_info "NEXORA Pre-Start Device Check"
    log_info "========================================="

    check_file_exists
    validate_yaml_format
    process_devices

    log_info "========================================="
    log_info "Pre-start check completed successfully"
    log_info "========================================="
}

# Run main
main "$@"
