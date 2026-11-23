#!/usr/bin/env bash
# dr-train chain after the 23 Nov 2026 reboot (owner: "restart ได้เลย"). Runs the two held jobs one after the other, never
# overlapping (the P2-T02 OOM lesson): 1) G03 A3r1 Stage A pilot evaluation (frozen queue, GPU lock inside),
# 2) P2-T02 coverage control with the memory-safe build (frozen protocol bd30d3f7; dr-train defaults: V100 = device 1,
# 32 claims-scan workers, 16 tokeniser workers, 24 GiB watchdog). P2-T02 starts even if A3r1 fails (independent jobs).
# Launch: setsid nohup bash /data/ptp-paper2/drtrain_chain_20261123.sh > /data/ptp-paper2/chain-20261123.log 2>&1 < /dev/null &
set -uo pipefail
stamp() { echo "$1 $(date -Is)"; }
stamp CHAIN_START
free -g | head -2
nvidia-smi --query-gpu=index,name,memory.used,memory.total --format=csv,noheader

stamp A3R1_PILOT_START
bash /data/ptp-paper2/g03-dev/code/g03_queue_a3r1_pilot.sh > /data/ptp-paper2/g03-dev/logs-a3r1-pilot.log 2>&1
rc=$?
tail -2 /data/ptp-paper2/g03-dev/logs-a3r1-pilot.log
if grep -q '^G03_A3R1_PILOT_DONE' /data/ptp-paper2/g03-dev/logs-a3r1-pilot.log; then stamp A3R1_PILOT_DONE; else stamp "A3R1_PILOT_FAILED rc=$rc"; fi

stamp P2T02_START
R=/data/ptp-paper2/p2-coverage
mkdir -p "$R/logs"
# the partial content build of the crashed 23 Nov launch is incomplete by construction (no manifest.json): remove it
if [ -d "$R/content" ] && [ ! -f "$R/content/manifest.json" ]; then rm -rf "$R/content"; echo "removed partial content build"; fi
bash "$R/code/p2t02_queue.sh" > "$R/logs/queue.log" 2>&1
tail -3 "$R/logs/queue.log"
if grep -q '^P2T02_DONE' "$R/logs/queue.log"; then stamp P2T02_DONE_IN_CHAIN; else stamp P2T02_FAILED_IN_CHAIN; fi
stamp CHAIN_DONE
