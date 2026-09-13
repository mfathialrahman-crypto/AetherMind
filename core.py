#!/usr/bin/env python3
"""
AetherMind — Intelligence / Reasoning Layer
Version: 1.1

Role in ecosystem:
  Consumes telemetry context and produces reasoned recommendations
  with explicit evidence, hypotheses, and confidence.
"""

import os
import json
import platform
import socket
import hashlib
from datetime import datetime, timezone
from statistics import mean, stdev
from pathlib import Path
from typing import Dict, List, Any, Tuple

STATE_FILE = "aether_state.json"
REPORT_FILE = "aether_report.txt"
RECOMMENDATIONS_FILE = "aether_recommendations.json"
LOG_FILE = "aether.log"
MAX_HISTORY = 200
MAX_RECOMMENDATIONS = 30

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def log(msg: str, level: str = "INFO"):
    ts = utc_now().strftime("%Y-%m-%d %H:%M:%S UTC")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] [{level}] {msg}\n")

def load_state() -> Dict:
    if Path(STATE_FILE).exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log(f"Failed to load state: {e}", "ERROR")
    return {
        "identity": "AetherMind v1.1 — Intelligence Layer",
        "evolution": 0,
        "history": [],
        "alerts": [],
        "recommendations": [],
        "status": "initializing"
    }

def save_state(state: Dict):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def collect_metrics() -> Dict[str, Any]:
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
        metrics["boot_time"] = datetime.fromtimestamp(
            psutil.boot_time(), tz=timezone.utc
        ).isoformat()
    except Exception as e:
        log(f"Metrics collection error: {e}", "ERROR")
    return metrics

def compute_signature(data: dict) -> str:
    raw = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:20]

def reason(current: Dict, history: List[Dict]) -> Tuple[List[str], List[Dict], Dict]:
    """
    Intelligence pipeline:
    Evidence → Hypotheses → Confidence → Recommendation
    """
    anomalies = []
    alerts = []
    evidence = []
    hypotheses = []
    confidence = 0.4

    # Collect evidence
    evidence.append({"signal": "cpu", "value": current["cpu"]})
    evidence.append({"signal": "memory", "value": current["memory"]})
    evidence.append({"signal": "disk", "value": current["disk"]})
    evidence.append({"signal": "load_avg", "value": current["load_avg"]})

    # Hard evidence
    if current["cpu"] >= 90:
        anomalies.append("CRITICAL: CPU saturation")
        alerts.append({"level": "critical", "type": "cpu", "value": current["cpu"]})
        hypotheses.append("System under heavy computational load")
        confidence += 0.3
    elif current["cpu"] >= 75:
        anomalies.append("WARNING: High CPU")
        hypotheses.append("Elevated processing activity")
        confidence += 0.15

    if current["memory"] >= 92:
        anomalies.append("CRITICAL: Memory pressure")
        alerts.append({"level": "critical", "type": "memory", "value": current["memory"]})
        hypotheses.append("Possible memory leak or large workload")
        confidence += 0.25
    elif current["memory"] >= 82:
        anomalies.append("WARNING: Elevated memory")
        hypotheses.append("Memory usage trending high")
        confidence += 0.1

    if current["disk"] >= 93:
        anomalies.append("CRITICAL: Disk critically low")
        alerts.append({"level": "critical", "type": "disk", "value": current["disk"]})
        hypotheses.append("Disk space exhaustion risk")
        confidence += 0.25

    # Statistical evidence
    if len(history) >= 8:
        recent = history[-12:]
        cpu_series = [h.get("cpu", 0) for h in recent]
        mem_series = [h.get("memory", 0) for h in recent]
        try:
            cpu_mean = mean(cpu_series)
            cpu_std = stdev(cpu_series) if len(cpu_series) > 1 else 0
            mem_mean = mean(mem_series)

            if current["cpu"] > cpu_mean + max(2.5 * cpu_std, 15) and current["cpu"] > 40:
                anomalies.append(f"ANOMALY: CPU spike vs baseline {cpu_mean:.1f}%")
                hypotheses.append("Sudden change in workload pattern")
                confidence += 0.15

            if current["memory"] > mem_mean + 12:
                anomalies.append(f"ANOMALY: Memory above baseline {mem_mean:.1f}%")
                hypotheses.append("Memory growth relative to recent history")
                confidence += 0.1
        except Exception:
            pass

    # Correlation hypothesis
    if current["cpu"] >= 75 and current["memory"] >= 80:
        hypotheses.append("Correlated CPU + Memory pressure — possible single root cause")
        confidence += 0.1

    if not anomalies:
        anomalies.append("STABLE: Metrics within normal operating range")
        hypotheses.append("No significant issues detected")
        confidence = 0.8

    confidence = min(0.95, max(0.25, confidence))

    # Recommendation generation (Evidence First)
    if confidence < 0.45:
        recommendation = {
            "action": "observe",
            "priority": "low",
            "reason": "Insufficient confidence to recommend strong action",
            "confidence": round(confidence, 2)
        }
    elif any("CRITICAL" in a for a in anomalies):
        recommendation = {
            "action": "investigate_immediately",
            "priority": "critical",
            "reason": "Critical threshold(s) breached",
            "confidence": round(confidence, 2)
        }
    elif any("WARNING" in a or "ANOMALY" in a for a in anomalies):
        recommendation = {
            "action": "monitor_closely",
            "priority": "medium",
            "reason": "Elevated or anomalous signals present",
            "confidence": round(confidence, 2)
        }
    else:
        recommendation = {
            "action": "continue_normal_operations",
            "priority": "info",
            "reason": "System appears stable",
            "confidence": round(confidence, 2)
        }

    decision = {
        "timestamp": utc_now().isoformat(),
        "evidence": evidence,
        "hypotheses": hypotheses,
        "anomalies": anomalies,
        "recommendation": recommendation,
        "confidence": round(confidence, 2)
    }

    return anomalies, alerts, decision

def generate_report(state, metrics, anomalies, decision, signature, now) -> str:
    border = "═" * 60
    lines = [
        f"╔{border}╗",
        f"║         AETHERMIND v1.1 — INTELLIGENCE LAYER            ║",
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
        f"╠{border}╣",
        f"║  Confidence   : {decision['confidence']}",
        f"║  Recommendation: {decision['recommendation']['action']} ({decision['recommendation']['priority']})",
        f"╠{border}╣",
        f"║  Hypotheses:",
    ]
    for h in decision.get("hypotheses", []):
        lines.append(f"║    • {h}")
    lines.append(f"╠{border}╣")
    lines.append(f"║  Analysis:")
    for a in anomalies:
        lines.append(f"║    • {a}")
    lines.append(f"╠{border}╣")
    lines.append(f"║  History depth: {len(state['history'])} snapshots")
    lines.append(f"║  Status       : {state['status']}")
    lines.append(f"╚{border}╝")
    return "\n".join(lines) + "\n"

def main():
    now = utc_now()
    log("AetherMind v1.1 Intelligence cycle started")

    state = load_state()
    metrics = collect_metrics()
    anomalies, new_alerts, decision = reason(metrics, state.get("history", []))

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

    recommendations = state.get("recommendations", [])
    recommendations.append(decision)
    if len(recommendations) > MAX_RECOMMENDATIONS:
        recommendations = recommendations[-MAX_RECOMMENDATIONS:]
    state["recommendations"] = recommendations

    state["last_run"] = now.isoformat()
    state["status"] = "active"
    state["hostname"] = socket.gethostname()
    state["os"] = platform.system()
    state["identity"] = "AetherMind v1.1 — Intelligence Layer"
    state["last_decision"] = decision

    save_state(state)

    # Machine-readable recommendations
    with open(RECOMMENDATIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(recommendations[-10:], f, indent=2, ensure_ascii=False)

    report = generate_report(state, metrics, anomalies, decision, signature, now)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report)

    print(report)
    log(f"Cycle completed — Gen #{state['evolution']} | Confidence {decision['confidence']}")

if __name__ == "__main__":
    main()
