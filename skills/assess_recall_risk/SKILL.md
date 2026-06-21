# Skill: assess_recall_risk

## Description
Synthesizes telemetry, service note, and historical pattern signals into a structured risk score with a recommended containment action.

## Trigger phrases
- "assess recall risk"
- "what is the risk score"
- "how serious is this"
- "should we be worried"
- "risk assessment"
- "evaluate defect severity"

## What this skill does
Runs **RiskAssessmentAgent** (Agent 4), which synthesizes outputs from the three detection agents into:
- A risk score from 0–100
- A confidence percentage
- A recommended action: CONTAIN, MONITOR, or CLEAR

## Risk scoring logic (design choices — not industry standards)
| Signal | Points |
|--------|--------|
| Telemetry risk_signal == HIGH | +40 |
| Telemetry risk_signal == MEDIUM | +20 |
| Historical known_risk == true | +30 |
| Historical similarity_score > 0.7 | +15 |
| Service note top symptom severity == HIGH | +15 |

**Thresholds:**
- 70–100 → CONTAIN (immediate action required)
- 40–69 → MONITOR (watch closely, no quarantine yet)
- 0–39 → CLEAR (no action required)

## Inputs required
- Output from `detect_failure_pattern` skill (or run that skill first)

## Output
```json
{
  "risk_score": 85,
  "confidence_pct": 92,
  "affected_batch": "B1042",
  "affected_vehicles": 137,
  "fault_code": "BAT_COOL_004",
  "recommended_action": "CONTAIN",
  "reasoning": "High frequency spike combined with known historical recall match..."
}
```

## Example usage
```
User: What is the risk score for the BAT_COOL_004 pattern?
Agent: [runs assess_recall_risk skill]
→ Risk score: 85/100 (HIGH)
→ Confidence: 92%
→ Recommended action: CONTAIN
→ Reasoning: High frequency spike (620%) + known prior recall match (0.88) + HIGH severity symptom confirmed
```

## Notes
- Risk score point values are design choices for this demo — adjust based on real domain thresholds
- To act on a CONTAIN recommendation, use the `contain_defect` skill
