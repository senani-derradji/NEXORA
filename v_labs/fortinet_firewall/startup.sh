#!/bin/bash
set -e

# ── Fortinet FortiGate-200E Firewall Simulator ──────────────────────
# Creates 2 Gigabit Ethernet ports as dummy interfaces so snmpd
# exposes realistic IF-MIB data.

echo "[firewall] Creating dummy network interfaces..."

# 2x Gigabit Ethernet ports (port1 → port2)
for i in $(seq 1 2); do
  ip link add "port${i}" type dummy 2>/dev/null || true
  ip link set "port${i}" up
  printf -v mac "02:00:00:00:20:%02x" "$i"
  ip link set "port${i}" address "$mac"
done

echo "[firewall] Created 2 interfaces: port[1-2]"
ip link show | grep -E "port[0-9]"

# ── Start snmpd ──────────────────────────────────────────────────────
echo "[firewall] Starting snmpd..."
exec snmpd -f -Lo
