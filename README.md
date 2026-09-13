# AetherMind v1.1 — Intelligence / Reasoning Layer

**Role in the ecosystem:** Evidence → Hypotheses → Confidence → Recommendation

## Purpose

AetherMind is the reasoning layer. It does not only detect anomalies — it forms hypotheses and produces recommendations with explicit confidence scores.

## Reasoning Pipeline

```
Collect Evidence
      ↓
Generate Hypotheses
      ↓
Score Confidence
      ↓
Emit Recommendation (Evidence First)
```

Rule: **No strong recommendation when confidence is low.**

## Outputs

| File                        | Purpose                              |
|-----------------------------|--------------------------------------|
| `core.py`                   | Intelligence engine                  |
| `aether_state.json`         | Persistent state + history           |
| `aether_recommendations.json` | Recent reasoned decisions          |
| `aether_report.txt`         | Human-readable report                |
| `aether.log`                | Operational log                      |

## Run

```bash
pip install -r requirements.txt
python core.py
```

## Automation

Runs every 2 hours via GitHub Actions.

---

**Ecosystem position:**  
Receives context → produces reasoned recommendations with confidence.
