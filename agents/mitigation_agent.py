import os
import json
from google.adk.agents import Agent
import importlib.util
import sys
from app.security import check_permission

def load_local_mcp_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

inventory_server = load_local_mcp_module("local_inventory", "mcp/inventory_server.py")
investigation_server = load_local_mcp_module("local_investigation", "mcp/investigation_server.py")

quarantine_batch = inventory_server.quarantine_batch
create_ticket = investigation_server.create_ticket

def safe_quarantine_batch(batch_id: str, reason: str) -> str:
    """Quarantine an inventory batch. Call this when a defect requires containment."""
    role = os.getenv("CURRENT_ROLE", "Engineer")
    if not check_permission(role, "quarantine_batch"):
        return f"Unauthorized: {role} role cannot perform quarantine_batch"
    return quarantine_batch(batch_id, reason)

def safe_create_ticket(fault_code: str, affected_vehicles: int, risk_score: int, batch_id: str) -> str:
    """Create an engineering investigation ticket."""
    role = os.getenv("CURRENT_ROLE", "Engineer")
    if not check_permission(role, "create_ticket"):
        return f"Unauthorized: {role} role cannot perform create_ticket"
    return create_ticket(fault_code, affected_vehicles, risk_score, batch_id)

mitigation_agent = Agent(
    name="mitigation_agent",
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
    instruction="""You are the MitigationOrchestrator. You receive a structured risk assessment in the user message and must take actions.

# PII redaction — GDPR/CCPA compliance layer (applied to all text before LLM processing)

IMPORTANT SECURITY RULE:
If ANY tool returns a message starting with "Unauthorized:", stop immediately. Do NOT call any other tools.

Read the `recommended_action` from the risk assessment.

If "CONTAIN":
1. Call `safe_quarantine_batch` with the affected_batch and a reason string.
2. Call `safe_create_ticket` with fault_code, affected_vehicles, risk_score, and batch_id.
3. Write a detailed executive brief. Label all figures as SYNTHETIC DEMO DATA.

If "MONITOR":
1. Call `safe_create_ticket` only. Do NOT quarantine.
2. Write a short status note. Label figures as SYNTHETIC DEMO DATA.

If "CLEAR":
1. Do not call any tools.
2. Write a brief note logging the decision.

After all tool calls are done, respond with ONLY a JSON object in this exact format (no markdown, no extra text):
{
  "actions_taken": ["list of actions you called"],
  "ticket_id": "TKT-XXXX-XXX or null",
  "quarantine_status": "result string or null",
  "batch_id": "the batch ID or null",
  "brief": "your executive brief text here"
}""",
    tools=[safe_quarantine_batch, safe_create_ticket],
)
