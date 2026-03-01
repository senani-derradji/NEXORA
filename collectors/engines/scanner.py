import nmap
import socket

def scan_subnet(subnet="192.168.0.0/24"):
    nm = nmap.PortScanner()
    nm.scan(hosts=subnet, arguments='-sn')

    active_hosts = []

    for host in nm.all_hosts():
        if nm[host].state() == "up":
            if is_snmp_open(host):
                active_hosts.append({
                    "ip": host,
                    "snmp": True
                })
            else:
                active_hosts.append({
                    "ip": host,
                    "snmp": False
                })

    return active_hosts


def is_snmp_open(ip):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1)
    try:
        sock.sendto(b'', (ip, 161))
        return True
    except:
        return False
    finally:
        sock.close()


print(scan_subnet())