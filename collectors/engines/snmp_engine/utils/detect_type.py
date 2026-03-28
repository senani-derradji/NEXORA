def detect_device_type(sys_object_id) -> str:
    """
    Detects the device type based on the SNMP sysObjectID.
    Returns a category string such as 'router', 'switch', 'firewall', etc.
    """

    oid_str = str(sys_object_id[0])

    DEVICE_TYPE_MAP = {
        "1.3.6.1.4.1.9":      "router",          # Cisco (IOS routers, ASR, ISR)
        "1.3.6.1.4.1.2011":   "router",          # Huawei routers (NE series)
        "1.3.6.1.4.1.2636":   "router",          # Juniper (MX, SRX, EX)
        "1.3.6.1.4.1.14988":  "router",          # MikroTik RouterOS
        "1.3.6.1.4.1.30065":  "switch",          # Arista (primarily switches)
        "1.3.6.1.4.1.2928":   "router",          # Ericsson routers

        "1.3.6.1.4.1.4526":   "switch",          # NETGEAR switches
        "1.3.6.1.4.1.25506":  "switch",          # H3C switches
        "1.3.6.1.4.1.1916":   "switch",          # Extreme Networks switches
        "1.3.6.1.4.1.1991":   "switch",          # Brocade Ethernet switches
        "1.3.6.1.4.1.11":     "switch",          # HP / HPE ProCurve switches
        "1.3.6.1.4.1.47196":  "switch",          # Aruba switches
        "1.3.6.1.4.1.207":    "switch",          # Allied Telesis switches
        "1.3.6.1.4.1.5567":   "switch",          # Enterasys switches
        "1.3.6.1.4.1.800":    "switch",          # Xylan (Alcatel legacy)
        "1.3.6.1.4.1.6486":   "switch",          # Alcatel-Lucent Enterprise
        "1.3.6.1.4.1.890":    "switch",          # ZyXEL switches
        "1.3.6.1.4.1.89":     "switch",          # RAD Data Communications
        "1.3.6.1.4.1.4329":   "switch",          # Zhone Technologies
        "1.3.6.1.4.1.17409":  "switch",          # ZTE switches
        "1.3.6.1.4.1.6027":   "switch",          # Dell Force10 / Dell EMC Networking

        "1.3.6.1.4.1.14179":  "wireless_controller",  # Cisco WLC
        "1.3.6.1.4.1.388":    "access_point",    # Symbol Technologies / Zebra AP
        "1.3.6.1.4.1.26928":  "access_point",    # Ruckus APs
        "1.3.6.1.4.1.41112":  "access_point",    # Ubiquiti UniFi / EdgeOS

        "1.3.6.1.4.1.25461":  "firewall",        # Palo Alto Networks
        "1.3.6.1.4.1.12356":  "firewall",        # Fortinet FortiGate
        "1.3.6.1.4.1.2620":   "firewall",        # Check Point
        "1.3.6.1.4.1.9694":   "firewall",        # WatchGuard
        "1.3.6.1.4.1.3417":   "firewall",        # Barracuda
        "1.3.6.1.4.1.5813":   "firewall",        # NetScreen (legacy Juniper)
        "1.3.6.1.4.1.3076":   "vpn_concentrator",# Altiga / Cisco VPN 3000 (legacy)
        "1.3.6.1.4.1.21317":  "firewall",        # Hillstone Networks
        "1.3.6.1.4.1.38446":  "firewall",        # Sangfor Technologies
        "1.3.6.1.4.1.3375":   "load_balancer",   # F5 BIG-IP (also does security)

        "1.3.6.1.4.1.10128":  "load_balancer",   # Citrix NetScaler / ADC
        "1.3.6.1.4.1.7146":   "load_balancer",   # Radware

        "1.3.6.1.4.1.232":    "server",          # HPE ProLiant (iLO)
        "1.3.6.1.4.1.674":    "server",          # Dell PowerEdge (iDRAC)
        "1.3.6.1.4.1.19046":  "server",          # Lenovo ThinkSystem

        "1.3.6.1.4.1.8072":   "linux",           # Net-SNMP / Linux host
        "1.3.6.1.4.1.311":    "windows",         # Microsoft Windows
        "1.3.6.1.4.1.2021":   "linux",           # Net-SNMP generic (Linux)

        "1.3.6.1.4.1.6876":   "virtual_machine", # VMware vSphere / NSX

        "1.3.6.1.4.1.789":    "storage",         # NetApp ONTAP
        "1.3.6.1.4.1.1588":   "storage",         # Brocade SAN / Fibre Channel

        "1.3.6.1.4.1.318":    "ups",             # APC by Schneider (UPS/PDU)
        "1.3.6.1.4.1.476":    "ups",             # Liebert / Vertiv UPS
        "1.3.6.1.4.1.5528":   "ups",             # APC Rack PDU

        "1.3.6.1.4.1.11.2.3.9": "printer",       # HP JetDirect printers
        "1.3.6.1.4.1.367":    "printer",         # Ricoh MFP
        "1.3.6.1.4.1.1248":   "printer",         # Epson
        "1.3.6.1.4.1.236":    "printer",         # Samsung printers
        "1.3.6.1.4.1.253":    "printer",         # Xerox

        "1.3.6.1.4.1.3224":   "cpe",             # Netopia / Motorola DSL CPE
        "1.3.6.1.4.1.3417":   "cpe",             # Barracuda (also has CPE)
    }

    for prefix, device_type in sorted(DEVICE_TYPE_MAP.items(), key=lambda x: -len(x[0])):
        if oid_str.startswith(prefix):
            return device_type

    return "unknown"