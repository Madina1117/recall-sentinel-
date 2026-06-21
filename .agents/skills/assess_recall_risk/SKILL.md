---
name: assess_recall_risk
description: Synthesizes telemetry, service note, and historical pattern signals into a risk score with a recommended containment action. Use when asked to assess recall risk, score a defect, or determine how serious a fault pattern is.
---

# Assess Recall Risk Skill

When assessing recall risk, follow these steps:

## Step 1 — Gather inputs
Collect outputs from the detect_failure_pattern skill:
- `risk_signal` from telemetry analysis
- Top symptom `severity` from service notes
- `similarity_score` and `known_risk` from historical pattern match

## Step 2 — Calculate risk score (0–100)
Apply the following point system:

| Signal | Points |
|--------|--------|
| risk_signal == HIGH | +40 |
| risk_signal == MEDIUM | +20 |
| known_risk == true | +30 |
| similarity_score > 0.7 | +15 |
| top symptom severity == HIGH | +15 |

## Step 3 — Determine recommended action
- Score 70–100 → **CONTAIN** (immediate action required)
- Score 40–69 → **MONITOR** (watch closely, no quarantine yet)
- Score 0–39 → **CLEAR** (no action required)

## Step 4 — Calculate confidence
Confidence % = (number of signals present / 5 total signals) × 100

## Output format
Return structured result with:
- `risk_score` (0–100)
- `confidence_pct`
- `affected_batch` and `affected_vehicles`
- `fault_code`
- `recommended_action` (CONTAIN/MONITOR/CLEAR)
- `reasoning` — one paragraph explaining the decision

## Important
- The point values are design choices for this demo, not industry standards
- Always produce a recommended_action even if confidence is low
- Label all outputs as synthetic demo data
