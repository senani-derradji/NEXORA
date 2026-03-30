# `collectors/engines` — Collection Engines

This folder is the **protocol plugin layer**. Each engine knows how to speak a specific monitoring protocol (SNMP, future: WMI, Prometheus scrape, Netflow…). Currently only SNMP is implemented.

> 🔮 **Planned:** Additional engines will be added as sub-packages (e.g. `wmi_engine/`, `prometheus_engine/`) following the same pattern as `snmp_engine/`.

```
engines/
└── snmp_engine/
    ├── snmp_collector.py       # Core SNMP poller — all metrics
    ├── scanner.py              # Network discovery via nmap — auto-discovers new devices
    └── utils/
        ├── detect_vendor.py    # sysObjectID → vendor name
        └── detect_type.py      # sysObjectID → device type string
```

---

## `snmp_engine/snmp_collector.py`

### Dataclasses

#### `SNMPConfig`
SNMP session parameters. Passed to `SNMPMonitor.__init__()`.

| Field | Default | Description |
|---|---|---|
| `community` | `"public"` | Read-only community string |
| `port` | `161` | SNMP UDP port |
| `timeout` | `2` | Seconds per OID request |
| `retries` | `1` | Retries on timeout |
| `mp_model` | `1` | SNMP version: `0`=v1, `1`=v2c, `3`=v3 |

> ⚠️ **Change `community`** to match your devices, especially in production. Updated in `scheduler/scheduler.py → self.config`.

#### `DeviceMetrics`
Typed output dataclass produced by the poller (fields below are what end up in the normalised envelope).

| Field | Type | Description |
|---|---|---|
| `cpu` | `float` | CPU idle % (subtract from 100 for usage) |
| `ram` | `float` | RAM usage % |
| `disk` | `float` | Disk usage % |
| `in_bytes / out_bytes` | `float` | Interface octet counters |
| `in_packets / out_packets` | `float` | Interface packet counters |
| `in_errors / out_errors` | `float` | Interface error counters |
| `latency` | `float` | Average RTT in ms (ping) |
| `packet_loss` | `float` | % lost packets (ping) |
| `status` | `bool` | `True` if SNMP responded |
| `timestamp` | `int` | Unix epoch |

---

### `SNMPMonitor` — OID Reference

All OIDs are standard MIB-II / UCD-SNMP:

| Constant | OID | What it reads |
|---|---|---|
| `OID_CPU_IDLE` | `1.3.6.1.4.1.2021.11.11.0` | CPU idle % (UCD-SNMP) |
| `OID_MEM_TOTAL` | `1.3.6.1.4.1.2021.4.5.0` | Total RAM (kB) |
| `OID_MEM_AVAIL` | `1.3.6.1.4.1.2021.4.6.0` | Available RAM (kB) |
| `OID_DISK_SIZE` | `1.3.6.1.2.1.25.2.3.1.5` | Disk partition size |
| `OID_DISK_USED` | `1.3.6.1.2.1.25.2.3.1.6` | Disk partition used |
| `OID_IF_OPER` | `1.3.6.1.2.1.2.2.1.8` | Interface operational status |
| `OID_IF_IN_OCTETS` | `1.3.6.1.2.1.2.2.1.10` | Incoming bytes |
| `OID_IF_OUT_OCTETS` | `1.3.6.1.2.1.2.2.1.16` | Outgoing bytes |
| `OID_IF_IN_PACKETS` | `1.3.6.1.2.1.2.2.1.11` | Incoming packets |
| `OID_IF_OUT_PACKETS` | `1.3.6.1.2.1.2.2.1.17` | Outgoing packets |
| `OID_IF_IN_ERRORS` | `1.3.6.1.2.1.2.2.1.14` | Incoming errors |
| `OID_IF_OUT_ERRORS` | `1.3.6.1.2.1.2.2.1.20` | Outgoing errors |
| `OID_IF_MAC` | `1.3.6.1.2.1.2.2.1.6` | Interface MAC address |
| `OID_SYS_OBJECT_ID` | `1.3.6.1.2.1.1.2.0` | Device vendor/type fingerprint |

> ⚠️ The CPU OID (`2021.11.11.0`) is **UCD-SNMP specific** (Linux/Net-SNMP). For Cisco, Juniper, or Windows, the OID is different — extend `SNMPMonitor` with device-type-aware OID selection.

---

### Methods

#### `snmp_get(ip, oid) → (value, bool)`
Single OID lookup via SNMP GET. Returns `(None, False)` on error.

#### `snmp_walk(ip, oid) → dict[str, Any]`
Walks a subtree via SNMP GETNEXT. Returns `{oid_str: value}` dict. Empty dict on error.

#### `ping_device(ip, count=3) → (latency_ms, packet_loss_pct)`
Runs `ping -c <count> <ip>` via subprocess. Parses RTT and packet loss from output.

#### `_get_cpu_usage(ip) → float`
Reads `OID_CPU_IDLE`. Returns `0.0` on failure (not `None`).

#### `_get_memory_usage(ip) → float | None`
Reads total and available RAM, computes `(total - avail) / total * 100`.

#### `_get_disk_usage(ip) → float | None`
Walks disk size/used subtrees, reads the first partition only.

#### `_get_interface_stats(ip) → dict`
Walks `OID_IF_OPER`, finds the first UP non-loopback interface (skips index `"1"`), reads all counters for it.

#### `collect_device_metrics(hostname, device_type, ip, mac_placeholder) → dict`
**Main public method.** Calls all `_get_*` helpers and ping, assembles the flat result dict.

#### `collect_metrics_as_dataclass(...)`
Thin alias for `collect_device_metrics`. Returns the same `dict` (name is a legacy leftover — it does not return a dataclass despite the name).

---

### What to change

| What | How |
|---|---|
| SNMP community string | `SNMPConfig(community=...)` in `scheduler/scheduler.py` |
| SNMP version (v3) | Change `mp_model=3` and add `UsmUserData` authentication in `snmp_get()` / `snmp_walk()` |
| Windows ping support | Update `ping_device()` to use `-n` instead of `-c` |
| Add new OIDs | Add class-level constants and new `_get_*` private methods |
| Add a new engine | Create `engines/new_engine/` with the same `collect_device_metrics()` interface, then import and use in `scheduler.py` |

---

## `snmp_engine/scanner.py` — Network Discovery

Automatically discovers live devices on the network using `nmap` and merges them into `devices.yml`.

### `NetworkScanner` Class

| Parameter | Default | Description |
|---|---|---|
| `subnet` | `"172.18.0.0/24"` | Subnet to scan (CIDR notation) |
| `devices_file` | `"config/devices.yml"` | Path to the device inventory YAML |
| `default_interval` | `15` | Default polling interval (seconds) for new devices |
| `bootstrapper` | `None` | Optional `DeviceBootstrapper` instance for DB cross-checking |

### Service Filtering

The scanner automatically skips NEXORA infrastructure IPs and hostnames so they are not registered as monitored devices:

**Skipped IPs:** `172.18.0.1`, `.10` (influxdb), `.20` (postgres), `.30` (core), `.40` (collectors), `.50` (backend), `.60` (frontend)

**Skipped hostnames:** `influxdb`, `postgres`, `core`, `collectors`, `backend`, `frontend`, `grafana`, `redis`, `rabbitmq`, `elasticsearch`, `kibana`, `prometheus`, `nginx`, `apache`, `mongodb`, `mysql`, `mariadb`, and more.

### Key Methods

| Method | Description |
|---|---|
| `scan()` | Runs nmap discovery, compares against YAML + DB, appends new devices to `devices.yml` |
| `scan_async()` | Async wrapper using `asyncio.to_thread()` |
| `_nmap_discover()` | Executes `nmap -sn --min-parallelism 10 <subnet>`, parses live hosts |
| `_detect_device_type(hostname)` | Heuristic classifier: router, switch, firewall, AP, server, workstation, printer, camera |
| `_is_service(hostname, ip)` | Checks if an IP/hostname belongs to an internal NEXORA service |
| `_load_existing_devices()` | Reads and cleans existing entries from `devices.yml` |
| `_save_devices(devices)` | Merges, deduplicates, filters services, writes back to YAML |

### Deduplication Logic

A device is considered **already known** (and skipped) if:
- Its IP exists in `devices.yml`, OR
- Its IP exists in the PostgreSQL database (via bootstrapper), OR
- Its MAC address exists in either YAML or DB

### CLI Usage

```bash
python scanner.py --subnet 172.18.0.0/24 --devices-file config/devices.yml --interval 15
```

### Integration

`scanner.py` is called by `pre_start_check.sh` during the Docker container startup:
```bash
python3 /collectors/engines/snmp_engine/scanner.py --devices-file "$CONFIG_FILE" --subnet "172.18.0.0/24"
```

It can also be used programmatically:
```python
from engines.snmp_engine.scanner import NetworkScanner

scanner = NetworkScanner(subnet="172.18.0.0/24", devices_file="config/devices.yml")
new_devices = scanner.scan()  # Returns list of newly discovered devices
```

---

## `snmp_engine/utils/detect_vendor.py` — `detect_vendor(sys_object_id)`

Maps a device's `sysObjectID` OID prefix to a human-readable vendor string.

**Input:** The raw pysnmp value tuple returned by `snmp_get(ip, OID_SYS_OBJECT_ID)`.
**Output:** String like `"cisco"`, `"linux"`, `"fortinet"`, or `"unknown"`.

Currently covers **50+ vendors** across routing, switching, wireless, firewalls, servers, storage, and UPS categories.

### What to change
| What | How |
|---|---|
| Add a new vendor | Append to `VENDOR_MAP`: `"1.3.6.1.4.1.<ENTERPRISE_ID>": "vendor_name"` |
| Find enterprise ID | Look up your device at [IANA enterprise numbers](https://www.iana.org/assignments/enterprise-numbers/enterprise-numbers) |

---

## `snmp_engine/utils/detect_type.py` — `detect_device_type(sys_object_id)`

Maps the same `sysObjectID` to a device role string: `"router"`, `"switch"`, `"firewall"`, `"server"`, `"linux"`, `"windows"`, etc.

**Note:** The OID prefix matching is sorted by **descending prefix length** to ensure more specific OIDs take priority over shorter ones.

### What to change
| What | How |
|---|---|
| Add a new device type | Append to `DEVICE_TYPE_MAP` with the enterprise OID prefix |
| Add a custom type string | Any string value is valid — just be consistent with what the frontend expects |
