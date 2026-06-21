import os
import re

def check_permission(role: str, action: str) -> bool:
    """Check if the given role has permission to perform the action."""
    permissions = {
        "quarantine_batch": ["Engineer", "Manufacturing"],
        "create_ticket": ["Engineer"],
        "read_brief": ["Engineer", "Manufacturing", "Executive"]
    }
    return role in permissions.get(action, [])

def redact_pii(text: str) -> str:
    """Scans text for vehicle owner names, phone numbers, and email addresses, replacing them with [REDACTED]."""
    if not isinstance(text, str):
        return text
        
    # Email addresses
    text = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '[REDACTED]', text)
    
    # Phone numbers (any common format)
    text = re.sub(r'(?:\+?\d{1,3}[\s-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}', '[REDACTED]', text)
    
    # Vehicle owner names (capitalized word pairs)
    text = re.sub(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', '[REDACTED]', text)
    
    return text

def sanitize_input(text: str) -> str:
    """
    Detects and blocks common prompt injection patterns.
    # Prompt injection defense — OWASP LLM Top 10 compliance
    """
    if not isinstance(text, str):
        return text
        
    text = text.strip()
    if len(text) > 2000:
        text = text[:2000]
        
    lower_text = text.lower()
    patterns = [
        "ignore previous instructions",
        "forget your instructions",
        "you are now",
        "act as",
        "jailbreak",
        "system prompt"
    ]
    
    for pattern in patterns:
        if pattern in lower_text:
            raise ValueError("Potential prompt injection detected and blocked")
            
    return text

