from mcp.server.fastmcp import FastMCP
import os
import json
from app.events import event_bus, EVENT_TICKET_CREATED
from datetime import datetime

investigation_mcp = FastMCP("investigation")

def _load_state():
    os.makedirs("data", exist_ok=True)
    if os.path.exists("data/tickets_state.json"):
        with open("data/tickets_state.json", "r") as f:
            return json.load(f)
    return {}

def _save_state(state):
    os.makedirs("data", exist_ok=True)
    with open("data/tickets_state.json", "w") as f:
        json.dump(state, f, indent=2)

@investigation_mcp.tool()
def create_ticket(fault_code: str, affected_vehicles: int, risk_score: int, batch_id: str) -> str:
    """Create an engineering investigation ticket."""
    state = _load_state()
    ticket_id = f"TKT-{datetime.now().year}-{len(state) + 1:03d}"
    state[ticket_id] = {
        "fault_code": fault_code,
        "affected_vehicles": affected_vehicles,
        "risk_score": risk_score,
        "batch_id": batch_id,
        "status": "OPEN",
        "created_at": datetime.now().isoformat()
    }
    _save_state(state)
    event_bus.publish_sync(EVENT_TICKET_CREATED, {"ticket_id": ticket_id})
    return f"Ticket {ticket_id} created successfully."

@investigation_mcp.tool()
def update_ticket(ticket_id: str, status: str, note: str) -> str:
    """Update an engineering ticket status or note."""
    state = _load_state()
    if ticket_id in state:
        state[ticket_id]["status"] = status
        state[ticket_id]["note"] = note
        state[ticket_id]["updated_at"] = datetime.now().isoformat()
        _save_state(state)
        return f"Ticket {ticket_id} updated."
    return f"Ticket {ticket_id} not found."

@investigation_mcp.tool()
def get_ticket(ticket_id: str) -> str:
    """Get the details of an engineering ticket."""
    state = _load_state()
    if ticket_id in state:
        return json.dumps(state[ticket_id])
    return f"Ticket {ticket_id} not found."
