#!/bin/bash
set -e

# ── MikroTik CCR1036-12G-4S Router Simulator ────────────────────────
# Creates 2 Gigabit Ethernet ports as dummy interfaces so snmpd
# exposes realistic IF-MIB data.

echo "[router] Creating dummy network interfaces..."

# 2x Gigabit Ethernet ports (ether1 → ether2)
for i in $(seq 1 2); do
  ip link add "ether${i}" type dummy 2>/dev/null || true
  ip link set "ether${i}" up
  printf -v mac "02:00:00:00:10:%02x" "$i"
  ip link set "ether${i}" address "$mac"
done

echo "[router] Created 2 interfaces: ether[1-2]"
ip link show | grep -E "ether[0-9]"

# ── Start snmpd ──────────────────────────────────────────────────────
echo "[router] Starting snmpd..."
exec snmpd -f -Lo
