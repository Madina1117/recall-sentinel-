# Skill: contain_defect

## Description
Executes containment actions for a confirmed high-risk defect: quarantines the affected inventory batch, opens an engineering investigation ticket, and generates an executive risk brief.

## Trigger phrases
- "contain the defect"
- "quarantine the batch"
- "take action"
- "contain this"
- "start the investigation"
- "lock down the batch"
- "initiate containment"

## What this skill does
Runs **MitigationOrchestrator** (Agent 5), which takes three actions via MCP tools:

1. **Quarantine batch** — calls `quarantine_batch(batch_id, reason)` on the Inventory MCP server
2. **Open ticket** — calls `create_ticket(fault_code, affected_vehicles, risk_score, batch_id)` on the Investigation MCP server
3. **Generate executive brief** — uses Gemini to produce a structured risk briefing for leadership

## Security requirements
This skill enforces role-based access control before executing any action:

| Action | Required role |
|--------|--------------|
| Quarantine batch | Engineer or Manufacturing |
| Create ticket | Engineer only |
| Read executive brief | Any role (Executive, Manufacturing, Engineer) |

Unauthorized attempts return an error — no action is taken.

## Inputs required
- Output from `assess_recall_risk` skill with `recommended_action == "CONTAIN"`
- Current user role (Engineer / Manufacturing / Executive)

## Output
```json
{
  "actions_taken": ["quarantine_batch", "create_ticket", "generate_brief"],
  "ticket_id": "TKT-2026-001",
  "quarantine_status": "QUARANTINED",
  "batch_id": "B1042",
  "brief": "EXECUTIVE RISK BRIEF — [synthetic demo content]"
}
```

## Example usage
```
User: Contain the defect for batch B1042 (role: Engineer)
Agent: [runs contain_defect skill]
→ ✅ Batch B1042 quarantined (137 vehicles)
→ ✅ Investigation ticket TKT-2026-001 opened
→ ✅ Executive brief generated and ready for review

User: Quarantine batch B1042 (role: Executive)
Agent: ❌ Unauthorized: Executive role cannot perform quarantine
```

## Notes
- This skill takes real (simulated) actions against MCP state — batch status changes persist in inventory_state.json
- Executive brief contains synthetic illustrative figures — label clearly in all outputs
- If risk score is below CONTAIN threshold, this skill will not execute quarantine but may create a monitoring ticket
