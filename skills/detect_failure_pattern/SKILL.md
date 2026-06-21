# Skill: detect_failure_pattern

## Description
Analyzes vehicle telemetry and service notes to detect emerging fault patterns that may indicate a product defect or recall risk.

## Trigger phrases
- "analyze telemetry"
- "check for fault patterns"
- "detect failure"
- "look for defects"
- "analyze fault codes"
- "check vehicle data"

## What this skill does
This skill runs Agents 1, 2, and 3 in parallel:
- **TelemetryAgent** scans fault code frequency changes across vehicle batches
- **ServiceNotesAgent** extracts recurring symptom patterns from technician observations
- **RecallPatternAgent** matches current signals against historical recall records

## Inputs required
- `telemetry.csv` — vehicle fault event log
- `service_notes.csv` — technician observation records

## Output
A structured summary containing:
- Detected fault code and frequency change %
- Number and batch of affected vehicles
- Risk signal level (HIGH / MEDIUM / LOW)
- Recurring symptom clusters from service notes
- Historical recall similarity score (0.0–1.0)

## Example usage
```
User: Analyze the latest telemetry for batch B1042
Agent: [runs detect_failure_pattern skill]
→ Detected: BAT_COOL_004 spike (+620%) across 137 vehicles in batch B1042
→ Top symptom: coolant residue near battery connectors (47 occurrences, HIGH severity)
→ Historical match: RC-2024-BAT-003 (similarity: 0.88) — prior recall for same fault
```

## Notes
- All data is synthetic for demo purposes
- This skill does not take any containment actions — use `assess_recall_risk` next
