# AGENTS.md — Recall Sentinel

> **Kaggle 5-Day AI Agents Intensive — Agents for Business Track**
> Madina Ochilova · Deadline: July 6, 2026
> All data in this project is synthetic and for demonstration purposes only.

---

## System Overview

Recall Sentinel is an autonomous multi-agent system that monitors vehicle telemetry and service data, detects emerging defect patterns that could indicate a safety recall, and takes containment actions — automatically, before a human analyst notices the pattern.

**The problem it solves:** Automotive recall signals exist across three disconnected sources — raw telemetry fault codes, technician service notes, and historical recall databases. Correlating them manually takes days. This agent does it in seconds.

**What makes it agentic:** The system does not just summarize data. It makes a structured risk decision and then *takes real actions*: it opens an engineering investigation ticket, quarantines the affected inventory batch via MCP tools, and generates an executive risk brief — all without human intervention.

---

## Architecture

```
                    ┌─────────────────┐
                    │   User / UI     │
                    │ (uploads CSVs)  │
                    └────────┬────────┘
                             │
              ┌──────────────▼──────────────┐
              │      Orchestration Layer     │
              │   (ADK parallel dispatch)    │
              └──┬──────────────────────┬───┘
                 │          │           │
     ┌───────────▼─┐  ┌─────▼────┐  ┌──▼──────────┐
     │ Telemetry   │  │ Service  │  │   Recall    │
     │   Agent     │  │  Notes   │  │  Pattern    │
     │  (Agent 1)  │  │  Agent   │  │   Agent     │
     │             │  │ (Agent 2)│  │  (Agent 3)  │
     └───────────┬─┘  └─────┬────┘  └──┬──────────┘
                 │          │           │
              ┌──▼──────────▼───────────▼──┐
              │     RiskAssessmentAgent     │
              │          (Agent 4)          │
              └────────────┬────────────────┘
                           │
              ┌────────────▼────────────────┐
              │    MitigationOrchestrator   │
              │         (Agent 5)           │
              └──┬──────────────────────┬───┘
                 │                      │
     ┌───────────▼──┐          ┌────────▼────────┐
     │ Inventory MCP│          │Investigation MCP │
     │   Server     │          │    Server        │
     │quarantine_   │          │ create_ticket()  │
     │  batch()     │          │ update_ticket()  │
     └──────────────┘          └─────────────────┘
```

**Parallel execution:** Agents 1, 2, and 3 run concurrently. Agent 4 waits for all three to complete before synthesizing results. Agent 5 runs after Agent 4.

---

## Agent Specifications

### Agent 1 — TelemetryAgent

**File:** `agents/telemetry_agent.py`
**Priority:** MVP (required for minimum viable submission)

**Input:**
```
telemetry.csv
  columns: vehicle_id, fault_code, timestamp, battery_temp, severity
```

**What it does:**
- Groups fault events by fault_code
- Calculates frequency change % compared to a baseline window (first 30 days vs last 7 days)
- Identifies which vehicle_ids are affected and extracts their batch_id prefix
- Classifies risk signal as HIGH / MEDIUM / LOW based on frequency thresholds:
  - HIGH: frequency increase > 300% AND affected_vehicles > 50
  - MEDIUM: frequency increase > 100% OR affected_vehicles > 20
  - LOW: everything else

**Output (structured dict):**
```python
{
  "fault_code": "BAT_COOL_004",
  "frequency_change_pct": 620,
  "affected_vehicles": 137,
  "affected_batch": "B1042",
  "risk_signal": "HIGH"
}
```

**Rules:**
- Does NOT call external tools — reasoning over CSV data only
- Must handle the case where no spike is detected (returns risk_signal: "LOW")
- Must not fabricate numbers — all calculations from actual CSV rows

---

### Agent 2 — ServiceNotesAgent

**File:** `agents/service_agent.py`

**Input:**
```
service_notes.csv
  columns: vehicle_id, date, technician_note (free text)
```

**What it does:**
- Uses Gemini to read technician notes and extract recurring symptoms
- Clusters similar symptoms together (e.g. "coolant near battery" and "battery connector residue" → same symptom cluster)
- Counts occurrences of each symptom cluster
- Assigns severity (HIGH/MEDIUM/LOW) based on language cues (e.g. "burning smell" = HIGH)

**Output:**
```python
{
  "symptoms": [
    {
      "symptom": "coolant residue near battery connectors",
      "occurrences": 47,
      "severity": "HIGH"
    },
    {
      "symptom": "minor battery temp fluctuation",
      "occurrences": 8,
      "severity": "LOW"
    }
  ]
}
```

**Rules:**
- No external tools — Gemini NLP reasoning over text only
- Simplification allowed for MVP: keyword matching instead of full NLP if time is short

---

### Agent 3 — RecallPatternAgent

**File:** `agents/recall_agent.py`

**Input:**
- `fault_code` from Agent 1
- `symptom` (top symptom) from Agent 2
- `affected_batch` from Agent 1
- `historical_recalls.json` (loaded as context)

**What it does:**
- Compares current fault_code + symptom against historical recall patterns
- Computes a similarity score (0.0–1.0) based on:
  - Exact fault_code match: +0.5
  - Symptom keyword overlap: +0.3 (scaled)
  - Same part family: +0.2
- Returns whether a known recall match exists

**Output:**
```python
{
  "similarity_score": 0.88,
  "matched_recall_id": "RC-2024-BAT-003",
  "known_risk": true,
  "matched_fault_code": "BAT_COOL_004",
  "matched_symptom": "coolant ingress at battery terminals"
}
```

**Rules:**
- No external tools — reasoning over historical JSON only
- If no historical match found: similarity_score = 0.0, known_risk = false

---

### Agent 4 — RiskAssessmentAgent

**File:** `agents/risk_agent.py`
**Priority:** MVP (required for minimum viable submission)

**Input:** Outputs from Agents 1, 2, and 3 (combined dict)

**What it does:**
- Synthesizes all signals into a single risk_score (0–100) using a point-based system:

| Signal | Points |
|--------|--------|
| risk_signal == "HIGH" from Agent 1 | +40 |
| risk_signal == "MEDIUM" from Agent 1 | +20 |
| known_risk == true from Agent 3 | +30 |
| similarity_score > 0.7 from Agent 3 | +15 |
| top symptom severity == "HIGH" from Agent 2 | +15 |

- Computes confidence % based on how many input signals are present vs. missing
- Determines recommended_action:
  - CONTAIN: risk_score >= 70
  - MONITOR: risk_score 40–69
  - CLEAR: risk_score < 40

**Output:**
```python
{
  "risk_score": 85,
  "confidence_pct": 92,
  "affected_batch": "B1042",
  "affected_vehicles": 137,
  "fault_code": "BAT_COOL_004",
  "recommended_action": "CONTAIN",
  "reasoning": "High frequency spike (620%) combined with known historical recall match (similarity: 0.88) and confirmed coolant symptom across 47 service notes warrants immediate containment."
}
```

**Rules:**
- No external tools — synthesis and structured decision only
- The point values are design choices for this demo, not industry standards — adjust as data warrants
- Must always produce a recommended_action even if confidence is low

---

### Agent 5 — MitigationOrchestrator

**File:** `agents/mitigation_agent.py`
**Priority:** MVP (this is the "wow" moment of the demo)

**Input:** Output from Agent 4 (RiskAssessmentAgent)

**What it does:**
Executes three containment actions when recommended_action == "CONTAIN":

1. **Quarantine inventory batch** via Inventory MCP → `quarantine_batch(batch_id, reason)`
2. **Open engineering ticket** via Investigation MCP → `create_ticket(fault_code, affected_vehicles, risk_score)`
3. **Generate executive brief** (Gemini synthesis — no MCP needed)

When recommended_action == "MONITOR":
- Creates a monitoring ticket only (no quarantine)
- Generates a shorter status note instead of full brief

When recommended_action == "CLEAR":
- Logs decision only, no actions taken

**Output:**
```python
{
  "actions_taken": ["quarantine_batch", "create_ticket", "generate_brief"],
  "ticket_id": "TKT-2026-001",
  "quarantine_status": "QUARANTINED",
  "batch_id": "B1042",
  "brief": "EXECUTIVE RISK BRIEF\n[Synthetic demo data...]\n..."
}
```

**Rules:**
- Must check security role before executing any action (see security.py)
- Only "Engineer" and "Manufacturing" roles may quarantine a batch
- Only "Engineer" role may create investigation tickets
- "Executive" role may only read the brief
- If unauthorized: return error, do NOT execute the action

---

## MCP Servers

### Inventory MCP Server

**File:** `mcp/inventory_server.py`
**State storage:** `data/inventory_state.json` (auto-created, gitignored)

**Tools exposed:**

| Tool | Parameters | Returns |
|------|-----------|---------|
| `quarantine_batch(batch_id, reason)` | batch_id: str, reason: str | `{status: "QUARANTINED", batch_id, timestamp}` |
| `release_batch(batch_id, authorized_by)` | batch_id: str, authorized_by: str | `{status: "RELEASED", batch_id, timestamp}` |
| `get_batch_status(batch_id)` | batch_id: str | `{batch_id, status, vehicle_count, last_updated}` |

### Investigation MCP Server

**File:** `mcp/investigation_server.py`
**State storage:** `data/tickets_state.json` (auto-created, gitignored)

**Tools exposed:**

| Tool | Parameters | Returns |
|------|-----------|---------|
| `create_ticket(fault_code, affected_vehicles, risk_score, batch_id)` | all str/int | `{ticket_id, status: "OPEN", created_at}` |
| `update_ticket(ticket_id, status, note)` | all str | `{ticket_id, status, updated_at}` |
| `get_ticket(ticket_id)` | ticket_id: str | full ticket dict |

---

## Security

### Static Analysis (Semgrep)
This project uses Semgrep as a pre-commit hook to automatically scan for security vulnerabilities before every commit. The custom `.semgrep.yml` rules check for:
- Hardcoded API keys or secrets
- Un-sanitized raw user input passed directly into LLM prompts
- Missing authentication and role checks in MCP tool calls

To ensure code quality and security, these scans are enforced locally during the `git commit` process via `.pre-commit-config.yaml`.

### Security Model

**File:** `app/security.py`

Three roles with different permissions:

| Role | Read Brief | Create Ticket | Quarantine Batch | Release Batch |
|------|-----------|--------------|-----------------|---------------|
| Executive | ✓ | ✗ | ✗ | ✗ |
| Manufacturing | ✓ | ✗ | ✓ | ✗ |
| Engineer | ✓ | ✓ | ✓ | ✓ |

Unauthorized action returns:
```python
{"error": "Unauthorized: Executive role cannot perform quarantine", "action": "quarantine_batch", "role": "Executive"}
```

---

## Agent Skills

Three SKILL.md files in `skills/` folder (ADK Agent Skills format):

| Skill | Triggers | What it does |
|-------|---------|-------------|
| `detect_failure_pattern` | "analyze telemetry", "check faults" | Runs Agents 1+2+3 |
| `assess_recall_risk` | "assess risk", "risk score" | Runs Agent 4 |
| `contain_defect` | "contain", "quarantine", "take action" | Runs Agent 5 |

---

## Data Files (All Synthetic)

| File | Purpose | Label in all outputs |
|------|---------|---------------------|
| `data/telemetry.csv` | Vehicle fault events — synthetic | "SYNTHETIC DEMO DATA" |
| `data/service_notes.csv` | Technician observations — synthetic | "SYNTHETIC DEMO DATA" |
| `data/inventory.csv` | Batch inventory — synthetic | "SYNTHETIC DEMO DATA" |
| `data/historical_recalls.json` | Historical recall patterns — synthetic | "SYNTHETIC DEMO DATA" |

**Important:** These files do not represent real Lucid Motors or any real manufacturer's data. Numbers like "620% frequency change" and "137 affected vehicles" are designed to clearly demonstrate the agent reasoning chain.

---

## Environment Variables

```bash
# Required
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash-lite   # verify availability on your key before building

# Optional
LOG_LEVEL=INFO
MCP_STATE_DIR=data/
```

---

## BDD Test Scenarios

```
Scenario: High-risk defect triggers full containment
Given telemetry shows BAT_COOL_004 fault frequency up 620% across 137 vehicles
When RiskAssessmentAgent scores risk above 85
Then MitigationOrchestrator quarantines batch B1042, creates engineering ticket, generates executive brief

Scenario: Low-risk signal triggers monitoring only
Given telemetry shows minor fault frequency increase across 3 vehicles
When RiskAssessmentAgent scores risk below 40
Then recommended_action is MONITOR — no quarantine, no ticket created

Scenario: Unauthorized action is denied
Given a user with role = Executive attempts to quarantine a batch
When security layer checks role permissions
Then action is denied with message "Unauthorized: Executive role cannot perform quarantine"

Scenario: Historical pattern match raises risk score
Given RecallPatternAgent finds similarity score of 0.88 to a known prior recall
When RiskAssessmentAgent receives this signal
Then risk_score increases significantly and known_risk flag appears in executive brief
```

---

## MVP Cutoff

If time is short, the minimum submittable system is:
- TelemetryAgent (Agent 1) ✓
- RiskAssessmentAgent (Agent 4) ✓
- MitigationOrchestrator (Agent 5) ✓
- Inventory MCP + Investigation MCP ✓
- At least 1 SKILL.md ✓
- Basic security check ✓

Agents 2 and 3 can be simplified to keyword matching and basic JSON lookup respectively without losing the core agentic argument.

---

*Recall Sentinel · Kaggle x Google AI Agents Intensive · Synthetic demo only · All data fabricated for demonstration purposes*
