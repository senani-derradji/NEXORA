def detect_vendor(sys_object_id) -> str:

    oid_str = str(sys_object_id[0])

    VENDOR_MAP = {
        # ── Routing & Switching ──────────────────────────────────────────
        "1.3.6.1.4.1.9":      "cisco",           # Cisco Systems
        "1.3.6.1.4.1.2011":   "huawei",          # Huawei Technologies
        "1.3.6.1.4.1.2636":   "juniper",         # Juniper Networks
        "1.3.6.1.4.1.14988":  "mikrotik",        # MikroTik
        "1.3.6.1.4.1.4526":   "netgear",         # NETGEAR
        "1.3.6.1.4.1.3375":   "f5",              # F5 Networks (BIG-IP)
        "1.3.6.1.4.1.25506":  "h3c",             # H3C Technologies (HPE)
        "1.3.6.1.4.1.6027":   "dell_force10",    # Dell Force10 / Dell EMC Networking
        "1.3.6.1.4.1.1916":   "extreme",         # Extreme Networks
        "1.3.6.1.4.1.1991":   "brocade",         # Brocade Communications
        "1.3.6.1.4.1.2928":   "ericsson",        # Ericsson
        "1.3.6.1.4.1.6876":   "vmware",          # VMware (vSphere, NSX)
        "1.3.6.1.4.1.30065":  "arista",          # Arista Networks (EOS)
        "1.3.6.1.4.1.8072":   "linux",           # Net-SNMP / Linux
        "1.3.6.1.4.1.311":    "windows",         # Microsoft Windows (SNMP Service)

        # ── Hewlett-Packard / HPE / Aruba ───────────────────────────────
        "1.3.6.1.4.1.11":     "hp",              # HP / HPE (ProCurve, etc.)
        "1.3.6.1.4.1.47196":  "aruba",           # Aruba Networks (HPE)

        # ── Wireless / WLAN ─────────────────────────────────────────────
        "1.3.6.1.4.1.14179":  "cisco_wlc",       # Cisco Wireless LAN Controller
        "1.3.6.1.4.1.388":    "symbol",          # Symbol Technologies (Zebra)
        "1.3.6.1.4.1.26928":  "ruckus",          # Ruckus Networks (CommScope)
        "1.3.6.1.4.1.41112":  "ubiquiti",        # Ubiquiti Networks (UniFi, EdgeOS)

        # ── Firewalls / Security ─────────────────────────────────────────
        "1.3.6.1.4.1.25461":  "palo_alto",       # Palo Alto Networks (PAN-OS)
        "1.3.6.1.4.1.12356":  "fortinet",        # Fortinet (FortiGate, FortiOS)
        "1.3.6.1.4.1.2620":   "checkpoint",      # Check Point Software
        "1.3.6.1.4.1.9694":   "watchguard",      # WatchGuard Technologies
        "1.3.6.1.4.1.3417":   "barracuda",       # Barracuda Networks
        "1.3.6.1.4.1.5813":   "netscreen",       # NetScreen (Juniper SSG/ISG legacy)
        "1.3.6.1.4.1.3076":   "altiga",          # Altiga / Cisco VPN 3000 (legacy)
        "1.3.6.1.4.1.21317":  "hillstone",       # Hillstone Networks
        "1.3.6.1.4.1.38446":  "sangfor",         # Sangfor Technologies

        # ── Switches (Access / Distribution) ────────────────────────────
        "1.3.6.1.4.1.89":     "rad",             # RAD Data Communications
        "1.3.6.1.4.1.207":    "allied_telesis",  # Allied Telesis
        "1.3.6.1.4.1.5567":   "enterasys",       # Enterasys Networks (legacy)
        "1.3.6.1.4.1.800":    "xylan",           # Xylan (Alcatel legacy)
        "1.3.6.1.4.1.6486":   "alcatel_lucent",  # Alcatel-Lucent Enterprise (ALE)
        "1.3.6.1.4.1.3224":   "netopia",         # Netopia (Motorola)
        "1.3.6.1.4.1.4329":   "zhone",           # Zhone Technologies
        "1.3.6.1.4.1.17409":  "zte",             # ZTE Corporation
        "1.3.6.1.4.1.890":    "zyxel",           # ZyXEL Communications

        # ── Load Balancers / ADC ─────────────────────────────────────────
        "1.3.6.1.4.1.10128":  "citrix_netscaler",# Citrix NetScaler / ADC
        "1.3.6.1.4.1.7146":   "radware",         # Radware

        # ── Storage / NAS / SAN ──────────────────────────────────────────
        "1.3.6.1.4.1.789":    "netapp",          # NetApp (ONTAP)
        "1.3.6.1.4.1.1588":   "brocade_san",     # Brocade SAN / Fibre Channel

        # ── Servers / UPS / Printers ─────────────────────────────────────
        "1.3.6.1.4.1.232":    "hpe_server",      # HPE ProLiant Servers (iLO)
        "1.3.6.1.4.1.674":    "dell_server",     # Dell EMC PowerEdge (iDRAC)
        "1.3.6.1.4.1.318":    "apc",             # APC by Schneider (UPS/PDU)
        "1.3.6.1.4.1.476":    "liebert",         # Liebert / Vertiv (UPS)
        "1.3.6.1.4.1.11.2.3.9": "hp_printer",   # HP Printers (JetDirect)
        "1.3.6.1.4.1.367":    "ricoh",           # Ricoh Printers/MFP
        "1.3.6.1.4.1.1248":   "epson",           # Epson
        "1.3.6.1.4.1.236":    "samsung_printer", # Samsung Printers
        "1.3.6.1.4.1.253":    "xerox",           # Xerox

        # ── Industrial / OT / IoT ────────────────────────────────────────
        "1.3.6.1.4.1.5528":   "apc_rack",        # APC Rack PDU
        "1.3.6.1.4.1.19046":  "lenovo",          # Lenovo (ThinkSystem, IMM)
        "1.3.6.1.4.1.2021":   "net_snmp",        # Net-SNMP generic (also Linux)
    }

    for prefix, vendor in VENDOR_MAP.items():
        if oid_str.startswith(prefix):
            return vendor

    return "unknown"