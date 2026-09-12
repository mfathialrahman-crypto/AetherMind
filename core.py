#!/usr/bin/env python3
"""
AetherMind — Advanced Self-Evolving Intelligence Core
Version: 1.0
Author: mfathialrahman-crypto
"""

import os
import json
import platform
import socket
import hashlib
import time
from datetime import datetime, timezone
from statistics import mean, stdev
from pathlib import Path

# Configuration
STATE_FILE = "aether_state.json"
REPORT_FILE = "aether_report.txt"
LOG_FILE = "aether.log"
MAX_HISTORY = 200

def log(msg: str):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{timestamp}] {msg}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)

def load_state():
    if Path(STATE_FILE).exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log(f"Failed to load state: {e}")
    return {
        "identity": "AetherMind v1.0",
        "evolution": 0,
        "history": [],
        "alerts": [],
        "metrics_summary": {},
        "status": "initializing"
    }

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def collect_metrics():
    metrics = {
        "cpu": 0.0,
        "memory": 0.0,
        "disk": 0.0,
        "load_avg": 0.0,
        "net_sent_mb": 0.0,
        "net_recv_mb": 0.0,
        "process_count": 0,
        "boot_time": None
    }
    try:
        import psutil
        metrics["cpu"] = round(psutil.cpu_percent(interval=1), 1)
        metrics["memory"] = round(psutil.virtual_memory().percent, 1)
        metrics["disk"] = round(psutil.disk_usage('/').percent, 1)
        if hasattr(os, "getloadavg"):
            metrics["load_avg"] = round(os.getloadavg()[0], 2)
        net = psutil.net_io_counters()
        metrics["net_sent_mb"] = round(net.bytes_sent / 1024 / 1024, 2)
        metrics["net_recv_mb"] = round(net.bytes_recv / 1024 / 1024, 2)
        metrics["process_count"] = len(psutil.pids())
        metrics["boot_time"] = datetime.fromtimestamp(psutil.boot_time(), tz=timezone.utc).isoformat()
    except Exception as e:
        log(f"Metrics collection error: {e}")
    return metrics

def compute_signature(data: dict) -> str:
    raw = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:20]

def detect_anomalies(current: dict, history: list):
    anomalies = []
    alerts = []

    # Hard thresholds
    if current["cpu"] >= 90:
        anomalies.append("🔴 CRITICAL: CPU saturation")
        alerts.append({"level": "critical", "type": "cpu", "value": current["cpu"]})
    elif current["cpu"] >= 75:
        anomalies.append("⚠️ WARNING: High CPU load")

    if current["memory"] >= 92:
        anomalies.append("🔴 CRITICAL: Memory exhaustion risk")
        alerts.append({"level": "critical", "type": "memory", "value": current["memory"]})
    elif current["memory"] >= 82:
        anomalies.append("⚠️ WARNING: Elevated memory usage")

    if current["disk"] >= 93:
        anomalies.append("🔴 CRITICAL: Disk space critically low")
        alerts.append({"level": "critical", "type": "disk", "value": current["disk"]})
    elif current["disk"] >= 85:
        anomalies.append("⚠️ WARNING: Disk usage high")

    # Statistical trend detection
    if len(history) >= 8:
        recent = history[-12:]
        cpu_series = [h.get("cpu", 0) for h in recent]
        mem_series = [h.get("memory", 0) for h in recent]

        try:
            cpu_mean = mean(cpu_series)
            cpu_std = stdev(cpu_series) if len(cpu_series) > 1 else 0
            mem_mean = mean(mem_series)

            if current["cpu"] > cpu_mean + max(2.5 * cpu_std, 15) and current["cpu"] > 40:
                anomalies.append(f"📈 Anomaly: Sudden CPU spike (baseline ~{cpu_mean:.1f}%)")
                alerts.append({"level": "warning", "type": "cpu_trend", "value": current["cpu"]})

            if current["memory"] > mem_mean + 12:
                anomalies.append(f"📈 Anomaly: Memory climbing above baseline (~{mem_mean:.1f}%)")
        except Exception:
            pass

    if not anomalies:
        anomalies.append("✅ System stable — all metrics within normal range")

    return anomalies, alerts

def generate_report(state, metrics, anomalies, signature, now):
    border = "═" * 58
    lines = [
        f"╔{border}╗",
        f"║          AETHERMIND — INTELLIGENCE CORE v1.0           ║",
        f"╠{border}╣",
        f"║  Identity     : {state['identity']}",
        f"║  Host         : {socket.gethostname()}",
        f"║  Platform     : {platform.system()} {platform.release()}",
        f"║  Evolution    : Generation #{state['evolution']}",
        f"║  Timestamp    : {now.strftime('%Y-%m-%d %H:%M:%S')} UTC",
        f"║  Signature    : {signature}",
        f"╠{border}╣",
        f"║  CPU          : {metrics['cpu']}%",
        f"║  Memory       : {metrics['memory']}%",
        f"║  Disk         : {metrics['disk']}%",
        f"║  Load Average : {metrics['load_avg']}",
        f"║  Processes    : {metrics['process_count']}",
        f"║  Network ↑    : {metrics['net_sent_mb']} MB",
        f"║  Network ↓    : {metrics['net_recv_mb']} MB",
        f"╠{border}╣",
        f"║  Analysis:",
    ]
    for a in anomalies:
        lines.append(f"║    {a}")
    lines.append(f"╠{border}╣")
    lines.append(f"║  History depth: {len(state['history'])} snapshots")
    lines.append(f"║  Status       : {state['status']}")
    lines.append(f"╚{border}╝")
    return "\n".join(lines) + "\n"

def main():
    now = datetime.now(timezone.utc)
    log("AetherMind cycle started")

    state = load_state()
    metrics = collect_metrics()
    anomalies, new_alerts = detect_anomalies(metrics, state.get("history", []))

    metrics["timestamp"] = now.isoformat()
    signature = compute_signature(metrics)
    metrics["signature"] = signature

    # Update state
    state["evolution"] = state.get("evolution", 0) + 1
    history = state.get("history", [])
    history.append(metrics)
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]
    state["history"] = history
    state["alerts"] = (state.get("alerts", []) + new_alerts)[-30:]
    state["last_run"] = now.isoformat()
    state["status"] = "active"
    state["hostname"] = socket.gethostname()
    state["os"] = platform.system()

    save_state(state)

    report = generate_report(state, metrics, anomalies, signature, now)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report)

    print(report)
    log(f"Cycle completed — Generation #{state['evolution']}")

if __name__ == "__main__":
    main()
