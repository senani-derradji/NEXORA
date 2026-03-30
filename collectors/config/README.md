# `collectors/config` — Static Configuration

This folder contains all static configuration that drives the collector's behaviour at runtime. **No source code here** — only YAML, SNMP config, and the DB initialisation helper.

```
config/
├── devices.yml          # ⚙️  Device inventory — PRIMARY FILE TO EDIT
├── snmpd.conf           # SNMP agent config (for local/simulated devices)
└── db_config/
    ├── .env             # ⚙️  DATABASE_URL (git-ignored)
    └── database.py      # DB initialisation helper called from main.py
```

---

## `devices.yml` — Device Inventory ⚙️

**Target:** The **single source of truth** for which devices the collector polls. Read by `DeviceBootstrapper` (`utils/devices_.py`) on startup and every 10 seconds. Any change to this file is picked up automatically without a restart.

### Structure

```yaml
devices:
  - hostname: <unique name>       # Used as the device identifier everywhere
    ip_address: <IPv4>            # IP the SNMP poller will target
    mac_address: <MAC>            # Used as the unique DB key (must be unique)
    device_type: server|router|switch|firewall|...
    interval: <seconds>           # Polling interval per device
```

### Current Entries

| Hostname | IP | MAC | Type | Interval |
|---|---|---|---|---|
| f_firewall | 172.18.0.3 | 06:57:47:C1:79:B9 | firewall | 15 s |

> **Note:** This file is auto-populated by `pre_start_check.sh` → `scanner.py` on container startup. The network scanner discovers live hosts on `172.18.0.0/24` via nmap and merges new devices into this file. You can also add devices manually — any manual entries are preserved as long as they are reachable.

### Rules
- **`mac_address` must be unique** — it is the primary join key between YAML and the DB.
- **`hostname` must be unique** — used as the device identifier in alerts and metrics.
- **`interval`** is in seconds. Minimum recommended: 5 s. Lower values increase SNMP load.
- **`device_type`** must match one of: `server`, `router`, `switch`, `firewall` (or any custom type you register in `engines/snmp_engine/utils/detect_type.py`).
- Devices that belong to NEXORA infrastructure (postgres, influxdb, core, etc.) are automatically excluded by the scanner.

### What to change
| What | How |
|---|---|
| Add a real device | Append a new `- hostname:` block following the structure above, or let `scanner.py` discover it automatically |
| Remove a device | Delete its block — `DeviceBootstrapper` will cancel its scheduler task within 10 s |
| Change polling frequency | Edit `interval` per device |
| Add a new field | Add the key to each device block **and** update `DeviceBootstrapper._load_yaml_devices()` and `DeviceOperations.create_device()` in `nexora-db` |
| Trigger a network scan | Restart the collectors container — `pre_start_check.sh` runs `scanner.py` automatically |

---

## `snmpd.conf` — SNMP Agent Config

Used to configure the `snmpd` daemon **on simulated/lab devices** (not on the collectors container itself). Copy this file to `/etc/snmp/snmpd.conf` on any device you want to monitor.

```
rocommunity public          # Read-only community string
agentAddress udp:0.0.0.0:161
sysLocation "Nexora Lab"
sysContact "admin@nexora.local"
view all included .1        # Expose the full MIB tree
```

### What to change
| What | How |
|---|---|
| Community string | Change `public` to a private string and update `SNMPConfig(community=...)` in `scheduler/scheduler.py` |
| Restrict access | Replace `0.0.0.0` with the collector's IP |
| Contact info | Update `sysLocation` and `sysContact` |

---

## `db_config/` — Database Initialisation

### `.env`

Contains the PostgreSQL connection string for the shared `nexora-db` database.

```env
DATABASE_URL=postgresql+psycopg2://nexorauser:nexorapass@postgres:5432/nexoradb
```

### `database.py` — `init(url_env: str = "DATABASE_URL")`

**Target:** Called once from `main.py` at startup. Loads `.env` from its own directory, reads `DATABASE_URL`, then calls `nexora-db`'s `init_database()` and `init_db_tables()`.

**Difference from backend's `config.py`:** This version raises a `ValueError` immediately if `DATABASE_URL` is not set. There is **no SQLite fallback** here.

| Item | Detail |
|---|---|
| `.env` path | Always looks in the same directory as `database.py` |
| On missing URL | Raises `ValueError` — service will not start |
| Called from | `main.py` line 3: `from config.db_config.database import init ; init(url_env="DATABASE_URL")` |

### What to change
| What | How |
|---|---|
| Use a different env var name | Pass it as `init(url_env="MY_DB_URL")` in `main.py` |
| Add a SQLite fallback | Add a `default_url` parameter similar to the backend's `config.py` |
| Load from a different `.env` path | Update the `env_path` line in `database.py` |
