---
name: contain_defect
description: Executes containment actions for a confirmed high-risk defect — quarantines the affected inventory batch, opens an engineering investigation ticket, and generates an executive risk brief. Use when asked to contain a defect, quarantine a batch, take action, or initiate a recall investigation.
---

# Contain Defect Skill

When containing a confirmed defect, follow these steps:

## Step 0 — Security check (always do this first)
Check the current user role before any action:

| Action | Allowed roles |
|--------|--------------|
| Quarantine batch | Engineer, Manufacturing |
| Create ticket | Engineer only |
| Read executive brief | All roles |

If role is not authorized: return error message and stop. Do NOT proceed with the action.

Example denial message: `"Unauthorized: Executive role cannot perform quarantine"`

## Step 1 — Quarantine inventory batch
- Call `quarantine_batch(batch_id, reason)` via Inventory MCP server
- Update batch status from ACTIVE → QUARANTINED
- Record timestamp and reason

## Step 2 — Open engineering investigation ticket
- Call `create_ticket(fault_code, affected_vehicles, risk_score, batch_id)` via Investigation MCP server
- Assign ticket ID (format: TKT-YYYY-###)
- Set initial status to OPEN

## Step 3 — Generate executive brief
Use Gemini to produce a structured brief with:
- Fault code and description
- Number of affected vehicles and batch ID
- Risk score and confidence level
- Actions taken (quarantine + ticket)
- Recommended next steps

Label all cost estimates and projections as: **[SYNTHETIC DEMO DATA — illustrative only]**

## Output format
```
actions_taken: [quarantine_batch, create_ticket, generate_brief]
ticket_id: TKT-2026-001
quarantine_status: QUARANTINED
batch_id: B1042
brief: [full text of executive brief]
```

## If recommended_action is MONITOR (not CONTAIN)
- Create monitoring ticket only (no quarantine)
- Generate a shorter status note instead of full brief

## If recommended_action is CLEAR
- Log decision only, no actions taken
