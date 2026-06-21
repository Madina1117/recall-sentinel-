import os
import json
from pydantic import BaseModel, Field
from typing import Literal
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
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

class MitigationResult(BaseModel):
    actions_taken: list[str] = Field(description="List of actions taken (e.g. 'quarantine_batch', 'create_ticket', 'generate_brief').")
    ticket_id: str | None = Field(description="The created ticket ID, if any.")
    quarantine_status: str | None = Field(description="Status of the quarantine action, if executed.")
    batch_id: str | None = Field(description="The batch ID that was processed.")
    brief: str = Field(description="The generated executive brief, or a status note if not contained. Label all figures as SYNTHETIC DEMO DATA.")

async def prepare_mitigation(callback_context: CallbackContext) -> None:
    """Callback to inject the risk assessment into the state."""
    ra = callback_context.state.get("risk_assessment", {})
    callback_context.state["risk_assessment"] = json.dumps(ra, indent=2)

mitigation_agent = Agent(
    name="mitigation_agent",
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
    instruction="""You are the MitigationOrchestrator. You receive a structured risk assessment from the RiskAssessmentAgent and must take actions.

Here is the risk assessment:
<risk_assessment>
{risk_assessment}
</risk_assessment>

IMPORTANT SECURITY RULE: 
If ANY tool returns a message starting with "Unauthorized:", you MUST immediately stop all processing. Do NOT attempt to call any other tools.
In this case, populate your final output as follows:
- actions_taken: []
- brief: The exact "Unauthorized: [role] role cannot perform [action]" message returned by the tool.
- Leave ticket_id, quarantine_status, and batch_id as null.

Read the `recommended_action` from the assessment.
If "CONTAIN":
1. Call `safe_quarantine_batch` to quarantine the affected batch. Provide a reason.
2. Call `safe_create_ticket` to open an engineering ticket.
3. Generate a detailed executive brief explaining the situation, the risk score, and the actions you just took.
   IMPORTANT: Label all figures and data in the brief as "SYNTHETIC DEMO DATA".

If "MONITOR":
1. Call `safe_create_ticket` to create a monitoring ticket. Do NOT call quarantine_batch.
2. Generate a shorter status note instead of a full brief. Label figures as "SYNTHETIC DEMO DATA".

If "CLEAR":
1. Do not call any tools.
2. Generate a brief note logging the decision.

After executing the necessary tools, return the structured JSON output.""",
    output_schema=MitigationResult,
    tools=[safe_quarantine_batch, safe_create_ticket],
    before_agent_callback=prepare_mitigation,
)
