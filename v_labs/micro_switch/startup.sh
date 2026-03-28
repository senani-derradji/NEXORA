#!/bin/bash
set -e

# ── MikroTik CRS326-24G-2S+RM Switch Simulator ──────────────────────
# Creates 24 Gigabit Ethernet ports + 2 SFP+ 10G ports as dummy
# interfaces so snmpd exposes realistic IF-MIB data.

echo "[switch] Creating dummy network interfaces..."

# 24x Gigabit Ethernet ports (ether1 → ether24)
for i in $(seq 1 12); do
  ip link add "ether${i}" type dummy 2>/dev/null || true
  ip link set "ether${i}" up
  printf -v mac "02:00:00:00:01:%02x" "$i"
  ip link set "ether${i}" address "$mac"
done

# 2x SFP+ 10G ports (sfp-sfpplus1 → sfp-sfpplus2)
for i in $(seq 1 2); do
  ip link add "sfp-sfpplus${i}" type dummy 2>/dev/null || true
  ip link set "sfp-sfpplus${i}" up
  printf -v mac "02:00:00:00:02:%02x" "$i"
  ip link set "sfp-sfpplus${i}" address "$mac"
done

echo "[switch] Created 26 interfaces: ether[1-24], sfp-sfpplus[1-2]"
ip link show | grep -E "ether[0-9]|sfp-sfpplus" | head -5
echo "[switch] ... and $((26 - 5)) more"

# ── Start snmpd ──────────────────────────────────────────────────────
echo "[switch] Starting snmpd..."
exec snmpd -f -Lo
