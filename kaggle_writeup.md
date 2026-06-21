# Recall Sentinel: Autonomous Vehicle Defect Detection and Containment

**Track:** Agents for Business
**Author:** Madina Ochilova
**GitHub:** https://github.com/Madina1117/recall-sentinel-

---

## The Problem

Vehicle safety recalls are expensive, slow, and largely reactive. By the time a manufacturer issues a recall, vehicles with known defects have often been on the road for weeks or months. The signals that predict a recall almost always exist earlier — buried across three disconnected data sources that no single analyst monitors simultaneously:

**Telemetry logs** capture fault codes from vehicles in the field in real time. When a specific fault code starts appearing more frequently across a cluster of vehicles from the same production batch, that pattern is statistically significant. But raw telemetry data is high-volume and noisy — a human analyst reviewing it manually would struggle to distinguish a genuine spike from background noise.

**Service technician notes** are free-text observations written by mechanics during vehicle inspections. When technicians across different service centers start writing about the same physical symptoms — coolant residue near battery connectors, for example — that's a meaningful signal. But because these notes are unstructured text, they're rarely aggregated or analyzed systematically.

**Historical recall records** contain the patterns of prior recalls: which fault codes triggered them, what symptoms technicians reported, which production batches were affected, and what the outcome was. A current fault pattern that closely resembles a prior recall is a strong predictor of a new one. But matching current signals against historical records requires a cross-reference that doesn't happen automatically.

The result: analysts who *do* spot recall signals manually typically find them days or weeks after the data first appeared. In automotive manufacturing, that delay translates directly into safety risk and financial exposure.

Recall Sentinel was built to close that gap.

---

## Why Agents — Not a Script, Not a Dashboard

The first design question was: why does this need to be agentic? A traditional analytics pipeline could read the same data sources and produce a report. A dashboard could visualize the trends.

The answer is in what happens *after* pattern detection. A script can flag an anomaly. An agent can act on it.

Recall Sentinel's value isn't the risk score — it's the three containment actions that follow automatically when the score exceeds the threshold: the inventory batch is quarantined via an MCP tool call, an engineering investigation ticket is created in the tracking system, and an executive risk brief is generated and ready for review. A human still makes the final decision about whether to issue a formal recall, but by the time they see the brief, the most urgent containment steps are already done.

This also requires genuine multi-agent reasoning, not a single model call. The three detection signals — telemetry frequency, symptom extraction, historical pattern matching — come from fundamentally different data types (structured CSV, unstructured text, JSON records) and require different analytical approaches. Running them in parallel, then synthesizing their outputs into a unified risk decision, is a task that fits naturally into a multi-agent architecture.

---

## Architecture

Recall Sentinel uses a 5-agent pipeline built with Google ADK and Gemini 3.1 Pro, developed entirely in Antigravity IDE.

**Agents 1, 2, and 3 run in parallel:**

**TelemetryAgent (Agent 1)** reads `telemetry.csv` — a log of vehicle fault events including fault code, timestamp, battery temperature, and severity. Rather than asking the LLM to do arithmetic over raw CSV rows (which produces inconsistent results), the agent uses a Python `before_agent_callback` to compute the frequency change deterministically using pandas: it compares fault code occurrence rates in a baseline window against the most recent 7 days. The computed statistics are passed to Gemini, which classifies the risk signal as HIGH, MEDIUM, or LOW and returns a structured Pydantic output object.

**ServiceNotesAgent (Agent 2)** reads `service_notes.csv` — free-text technician observations. The full text is loaded via callback and passed to Gemini, which clusters recurring symptoms, counts occurrences per cluster, and assigns severity based on language cues. This is where the LLM's natural language capability is genuinely needed — no deterministic script can reliably cluster semantically similar technician notes the way Gemini does.

**RecallPatternAgent (Agent 3)** loads `historical_recalls.json` — a set of prior recall records with fault codes, symptom keywords, part families, and outcomes. Gemini compares the current fault code and top symptom against historical patterns and returns a similarity score (0.0–1.0) and a `known_risk` boolean.

**RiskAssessmentAgent (Agent 4)** waits for all three agents to complete, then synthesizes their outputs. Risk scoring is handled deterministically in Python: HIGH telemetry signal (+40 points), known historical match (+30), similarity > 0.7 (+15), HIGH symptom severity (+15). Gemini receives the computed score and writes the reasoning paragraph. Recommended action is CONTAIN (≥70), MONITOR (40–69), or CLEAR (<40).

**MitigationOrchestrator (Agent 5)** receives the risk assessment and takes action. For a CONTAIN recommendation, it calls two FastMCP tools: `quarantine_batch()` on the Inventory MCP server (which updates batch status in `inventory_state.json`) and `create_ticket()` on the Investigation MCP server (which creates a record in `tickets_state.json`). Gemini then generates a structured executive brief. All cost estimates in the brief are clearly labeled as synthetic illustrative figures.

---

## Key Concepts Demonstrated

**Agent / Multi-agent (ADK):** The 5-agent graph uses ADK's `Agent` class with structured Pydantic output schemas, `before_agent_callback` for data loading, and `InMemoryRunner` for orchestration. Agents 1–3 run in parallel; Agent 4 synthesizes their combined output; Agent 5 acts on the decision.

**MCP Servers:** Two custom FastMCP servers handle external actions. `inventory_server.py` exposes `quarantine_batch()`, `release_batch()`, and `get_batch_status()`. `investigation_server.py` exposes `create_ticket()`, `update_ticket()`, and `get_ticket()`. Both store state in JSON files and are called as tools by MitigationOrchestrator.

**Antigravity IDE:** The entire project was built in Antigravity IDE. Antigravity read `AGENTS.md` at project open, used it to understand the architecture, generated each agent file with the correct ADK patterns, self-diagnosed a JSON serialization bug between Agent 4 and Agent 5, and added automatic retry logic for API rate limiting — all within the same conversation.

**Security Features:** `app/security.py` implements role-based access control with three roles: Engineer, Manufacturing, and Executive. Only Engineer and Manufacturing roles can quarantine a batch. Only Engineer can create investigation tickets. All roles can read the executive brief. Unauthorized action attempts return a clear error message and halt execution.

**Agent Skills:** Three SKILL.md files in `.agents/skills/` follow the Antigravity skills format with YAML frontmatter (name, description) for routing and full instructions in the body. Skills: `detect_failure_pattern`, `assess_recall_risk`, `contain_defect`. These are loaded progressively — metadata always in context, full instructions only when the skill is triggered.

**Deployability:** The project runs locally via Streamlit (`app/ui.py`) with a FastAPI-compatible backend. The UI allows role selection, displays each agent's output as it completes, shows the risk score and recommended action, and executes the security denial scenario for demonstration. `requirements.txt` and `.env.example` are included for reproducible setup.

---

## Demo Walkthrough

**Scenario 1 — Full containment (HIGH risk):**

With role set to Engineer, clicking Run Analysis triggers the full pipeline on synthetic data. TelemetryAgent detects fault code BAT_COOL_004 with a frequency spike of 19,721% in the most recent 7-day window across 146 vehicles in batch B1042 — risk signal HIGH. ServiceNotesAgent extracts the top symptom: "coolant residue near battery connector terminals," occurring across 47 technician notes, severity HIGH. RecallPatternAgent finds an 88% similarity match to historical recall RC-2024-BAT-003, a prior coolant-related battery recall affecting the same fault code and part family — known_risk: true.

RiskAssessmentAgent computes: HIGH signal (+40) + known_risk (+30) + similarity > 0.7 (+15) + HIGH symptom severity (+15) = **100/100**. Recommended action: CONTAIN.

MitigationOrchestrator quarantines batch B1042 (146 vehicles), creates investigation ticket TKT-2026-001, and generates an executive brief. All figures in the brief are labeled synthetic.

**Scenario 2 — Security denial:**

With role switched to Executive, attempting to trigger the same analysis results in the containment actions being blocked: "Unauthorized: Executive role cannot perform quarantine." The executive brief is generated and readable, but no MCP actions execute.

**Important note:** All data in both scenarios is entirely synthetic, generated programmatically for demonstration. The fault codes, vehicle counts, technician notes, and historical recall records do not represent any real manufacturer's data.

---

## Lessons Learned

The most important lesson: don't ask an LLM to do arithmetic. The first version of TelemetryAgent asked Gemini to calculate frequency change percentages directly from CSV rows in the prompt. The results were inconsistent — 110% one run, 77% the next — because LLMs estimate rather than compute. Moving all numerical calculations to deterministic Python in the callback and giving Gemini only the classification task produced consistent, reliable outputs every run.

The second lesson: Antigravity is genuinely useful as a development environment for agentic projects. The AGENTS.md file created before any code was written gave Antigravity enough context to generate correctly structured ADK agents from the first prompt. When a JSON serialization bug appeared between Agent 4 and Agent 5, Antigravity identified it, explained the root cause, and patched it without being asked. The skills system in `.agents/skills/` was immediately recognized and used.

The third lesson: free-tier API rate limits are a real constraint for multi-agent testing. Running 5 sequential LLM inferences hits the 15-requests-per-minute limit on Gemini Flash Lite. The solution — automatic retry with exponential backoff built into the UI — is also a useful production pattern.

---

## Future Work

Recall Sentinel as built demonstrates the multi-agent architecture on synthetic data. The natural next steps toward production would be: integration with real OBD-II telemetry streams via a streaming data connector; live connection to a manufacturer's service management database instead of CSV files; regulatory reporting output formatted for NHTSA submission; and deployment to Vertex AI Agent Engine for enterprise-scale operation with proper authentication, logging, and observability.

The architecture is designed to support these extensions — the MCP server interface means each data source can be replaced with a live connector without changing the agent logic.

---

*All data in this project is synthetic and was generated programmatically for demonstration purposes. It does not represent any real manufacturer, vehicle, or recall record. GitHub: https://github.com/Madina1117/recall-sentinel-*
