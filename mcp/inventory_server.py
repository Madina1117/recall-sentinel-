from mcp.server.fastmcp import FastMCP
import os
import json
from datetime import datetime

inventory_mcp = FastMCP("inventory")

def _load_state():
    os.makedirs("data", exist_ok=True)
    if os.path.exists("data/inventory_state.json"):
        with open("data/inventory_state.json", "r") as f:
            return json.load(f)
    return {}

def _save_state(state):
    os.makedirs("data", exist_ok=True)
    with open("data/inventory_state.json", "w") as f:
        json.dump(state, f, indent=2)

@inventory_mcp.tool()
def quarantine_batch(batch_id: str, reason: str) -> str:
    """Quarantine an inventory batch. Call this when a defect requires containment."""
    state = _load_state()
    state[batch_id] = {
        "status": "QUARANTINED",
        "reason": reason,
        "timestamp": datetime.now().isoformat()
    }
    _save_state(state)
    return f"Batch {batch_id} successfully QUARANTINED."

@inventory_mcp.tool()
def get_batch_status(batch_id: str) -> str:
    """Get the status of an inventory batch."""
    state = _load_state()
    if batch_id in state:
        return json.dumps(state[batch_id])
    return f"Batch {batch_id} not found."

@inventory_mcp.tool()
def release_batch(batch_id: str, authorized_by: str) -> str:
    """Release a quarantined batch."""
    state = _load_state()
    if batch_id in state:
        state[batch_id]["status"] = "RELEASED"
        state[batch_id]["authorized_by"] = authorized_by
        state[batch_id]["timestamp"] = datetime.now().isoformat()
        _save_state(state)
        return f"Batch {batch_id} successfully RELEASED."
    return f"Batch {batch_id} not found."
