---
name: detect_failure_pattern
description: Analyzes vehicle telemetry CSV and service notes to detect emerging fault patterns that may indicate a product defect or recall risk. Use when asked to analyze telemetry, check for fault patterns, or detect vehicle defects.
---

# Detect Failure Pattern Skill

When detecting a failure pattern, follow these steps:

## Step 1 — Load and analyze telemetry data
- Read `data/telemetry.csv`
- Group fault events by `fault_code`
- Calculate frequency change % between baseline window (first 30 days) and recent window (last 7 days)
- Identify which `vehicle_id` values are affected and extract their batch prefix
- Classify risk signal: HIGH (>300% increase AND >50 vehicles), MEDIUM (>100% OR >20 vehicles), LOW (everything else)

## Step 2 — Extract symptoms from service notes
- Read `data/service_notes.csv`
- Cluster recurring symptoms from `technician_note` column
- Count occurrences per symptom cluster
- Assign severity based on language cues (e.g. "burning", "leak", "residue" = HIGH)

## Step 3 — Match against historical recalls
- Read `data/historical_recalls.json`
- Compare current fault_code and top symptom against each historical recall
- Compute similarity score (0.0–1.0)
- Return matched recall ID and known_risk flag

## Output format
Return a structured summary with:
- `fault_code` and `frequency_change_pct`
- `affected_vehicles` count and `affected_batch`
- `risk_signal` (HIGH/MEDIUM/LOW)
- Top symptom with occurrence count and severity
- `similarity_score` and `known_risk` from historical match

## Important
- All data is synthetic demo data — label outputs accordingly
- Do not fabricate numbers; derive all values from actual CSV rows
- If no spike detected, return risk_signal: LOW and proceed
