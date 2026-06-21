import os

def check_permission(role: str, action: str) -> bool:
    """Check if the given role has permission to perform the action."""
    permissions = {
        "quarantine_batch": ["Engineer", "Manufacturing"],
        "create_ticket": ["Engineer"],
        "read_brief": ["Engineer", "Manufacturing", "Executive"]
    }
    return role in permissions.get(action, [])
