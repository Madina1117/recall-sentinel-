# Recall Sentinel 🛡️

> **Kaggle 5-Day AI Agents Intensive — Agents for Business Track**
> An autonomous multi-agent system that detects emerging vehicle defect patterns and takes containment actions automatically.

> ⚠️ **All data in this project is synthetic and for demonstration purposes only.** No real vehicle, manufacturer, or recall data is used.

---

## The Problem

Vehicle recalls cost manufacturers tens of millions of dollars and take months to execute — but the signals that predict them exist in the data weeks earlier. The challenge is that these signals are scattered across three disconnected sources:

- **Telemetry logs** — raw fault codes from vehicles in the field
- **Service notes** — free-text technician observations
- **Historical recall database** — known prior failure patterns

A human analyst correlating all three manually can take days. By then, more vehicles are at risk.

## The Solution

Recall Sentinel uses a 5-agent pipeline to automatically:

1. Detect fault frequency spikes in telemetry
2. Extract recurring symptoms from technician notes
3. Match patterns against historical recall records
4. Synthesize a risk score with confidence level
5. Take containment actions — quarantine the batch, open an investigation ticket, generate an executive brief

All from uploading two CSV files. The agent does the rest.

---

## Architecture

```
Upload telemetry.csv + service_notes.csv
          │
          ▼
┌─────────────────────────────────┐
│        Parallel Execution       │
│  TelemetryAgent │ ServiceNotes  │
│  (Agent 1)      │ Agent (Agt 2) │
│                 │               │
│  RecallPattern  │               │
│  Agent (Agt 3)  │               │
└────────────┬────────────────────┘
             │
             ▼
     RiskAssessmentAgent (Agent 4)
     risk_score + recommended_action
             │
             ▼
     MitigationOrchestrator (Agent 5)
             │
    ┌────────┴────────┐
    │                 │
Inventory MCP   Investigation MCP
quarantine_      create_ticket()
batch()
```

**Key concepts demonstrated:** Multi-agent (ADK), MCP Servers, Agent Skills, RBAC + PII Redaction + Prompt Injection Defense, STRIDE Threat Model, Pub/Sub Events, Semgrep Pre-commit, Antigravity IDE

---

## Course Takeaways Covered

| # | Takeaway | Where | Implementation |
|---|----------|-------|----------------|
| 1 | Multi-agent orchestration (ADK) | `agents/` | 5-agent graph, parallel + sequential execution |
| 2 | MCP server + tools | `mcp/` | 2 FastMCP servers, 6 tools |
| 3 | Custom Skills | `.agents/skills/` | 3 SKILL.md files with YAML frontmatter |
| 4 | Gemini 2.5 Flash Lite | `agents/*.py` | Model used across all 5 agents |
| 5 | ADK 2.0 graph workflow | `agents/*.py` | `before_agent_callback`, Pydantic schemas, `InMemoryRunner` |
| 6 | Semgrep pre-commit hooks | `.pre-commit-config.yaml`, `.semgrep.yml` | 3 custom rules: API keys, unsanitized LLM input, missing auth |
| 7 | PII redaction | `app/security.py` → `redact_pii()` | Regex scrub of names, phones, emails before LLM |
| 8 | Prompt injection defense | `app/security.py` → `sanitize_input()` | Blocklist check + 2000-char limit on all user inputs |
| 9 | STRIDE threat modeling | `SECURITY.md` | Full STRIDE table mapped to codebase mitigations |
| 10 | Pub/Sub event handling | `app/events.py` | `asyncio.Queue` event bus; 3 event types; UI event log |

---

## Setup

### Prerequisites
- Python 3.10+
- Google AI Studio account (for Gemini API key)
- `pip install google-adk streamlit fastapi uvicorn python-dotenv`

### Installation

```bash
git clone https://github.com/YOUR_USERNAME/recall-sentinel.git
cd recall-sentinel
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### Run locally

```bash
# Run the full agent pipeline
python agents/mitigation_agent.py

# Run the Streamlit UI
streamlit run app/ui.py
```

---

## Project Structure

```
recall-sentinel/
├── agents/
│   ├── telemetry_agent.py      # Agent 1 — fault pattern detection
│   ├── service_agent.py        # Agent 2 — technician note extraction
│   ├── recall_agent.py         # Agent 3 — historical pattern matching
│   ├── risk_agent.py           # Agent 4 — risk scoring and decision
│   └── mitigation_agent.py     # Agent 5 — containment actions via MCP
├── .agents/skills/
│   ├── detect_failure_pattern/SKILL.md
│   ├── assess_recall_risk/SKILL.md
│   └── contain_defect/SKILL.md
├── mcp/
│   ├── inventory_server.py     # quarantine_batch(), release_batch()
│   └── investigation_server.py # create_ticket(), update_ticket()
├── data/
│   ├── telemetry.csv           # Synthetic vehicle fault data
│   ├── service_notes.csv       # Synthetic technician observations
│   ├── inventory.csv           # Synthetic batch inventory
│   └── historical_recalls.json # Synthetic historical recall patterns
├── app/
│   ├── api.py                  # FastAPI backend
│   ├── ui.py                   # Streamlit frontend with event log
│   ├── security.py             # RBAC, PII redaction, prompt injection defense
│   └── events.py               # Pub/Sub event bus (asyncio.Queue)
├── AGENTS.md                   # Full agent specification
├── SECURITY.md                 # STRIDE threat model
├── .pre-commit-config.yaml     # Semgrep pre-commit hook
├── .semgrep.yml                # Custom security rules
├── .env.example                # Environment variable template
└── README.md
```

---

## Demo Scenarios

**Scenario 1 — Full Containment (High Risk)**
Upload `telemetry.csv` + `service_notes.csv`. The agents detect BAT_COOL_004 spiking 19,721% across 146 vehicles in batch B1042, match it to a known prior recall with 88% similarity (risk score: 100/100), and automatically quarantine the batch, open a ticket, and generate an executive brief. The 📡 Event Log shows all three events firing in sequence.

**Scenario 2 — Monitor Only (Low Risk)**
Modify inputs to show a minor frequency increase (3 vehicles). The risk score falls below 40. No quarantine is triggered — the system recommends monitoring only.

**Security Demo**
Attempt a quarantine action as the Executive role. The security layer denies it: `"Unauthorized: Executive role cannot perform quarantine"`.

---

## Data Notice

All CSV and JSON files in `data/` are **entirely synthetic** and were generated programmatically for this demonstration. They do not represent any real manufacturer's telemetry, service records, or recall history. All numbers (vehicle counts, fault frequencies, similarity scores) are designed to clearly illustrate the agent reasoning chain.

---

## Author

Madina Ochilova · [Kaggle Profile](https://www.kaggle.com) · Built for the Kaggle 5-Day AI Agents Intensive with Google · June–July 2026
