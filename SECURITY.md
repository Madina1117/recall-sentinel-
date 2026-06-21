# Recall Sentinel: Threat Model & Security Architecture

This document outlines the threat model for the Recall Sentinel system using the STRIDE methodology. It identifies potential threats and maps them to the specific mitigations already implemented in the codebase.

## STRIDE Threat Model

### Spoofing
| Threat | Description | Mitigation | Implementation |
|--------|-------------|------------|----------------|
| Fake Role Claims | A user attempts to spoof their role to execute unauthorized actions. | Role-Based Access Control (RBAC) verifies the active role before permitting critical actions. | `app/security.py` -> `check_permission()` |

### Tampering
| Threat | Description | Mitigation | Implementation |
|--------|-------------|------------|----------------|
| Malicious Input Override | An attacker inputs prompt injection payloads (e.g., "ignore previous instructions") or modifies input data to tamper with agent behavior. | Input sanitization intercepts and blocks known injection patterns before they reach the LLM pipeline. | `app/security.py` -> `sanitize_input()` |

### Repudiation
| Threat | Description | Mitigation | Implementation |
|--------|-------------|------------|----------------|
| Untraceable Quarantine Actions | Lack of an audit trail allows users to repudiate taking drastic containment actions. | The system returns a structured log of executed tools (`actions_taken`) and statuses to maintain an audit trail. | `agents/mitigation_agent.py` -> `MitigationResult` |

### Information Disclosure
| Threat | Description | Mitigation | Implementation |
|--------|-------------|------------|----------------|
| PII Leaking to LLM | Sensitive technician notes could contain customer names, phone numbers, or emails that get exposed to models. | A regex-based PII redaction layer scrubs data of sensitive information, replacing it with `[REDACTED]`. | `app/security.py` -> `redact_pii()` |

### Denial of Service
| Threat | Description | Mitigation | Implementation |
|--------|-------------|------------|----------------|
| Rate Limit Exhaustion | Excessive parallel agent calls to the API trigger 429 Resource Exhausted errors, halting operations. | The UI orchestrator implements retry logic with backoff on 429 errors. | `app/ui.py` -> `run_agent()` |

### Elevation of Privilege
| Threat | Description | Mitigation | Implementation |
|--------|-------------|------------|----------------|
| Unauthorized Executive Actions | A user attempts to escalate privileges, such as an Engineer accessing Executive-only reports or an Executive issuing quarantines. | Strict RBAC wrappers around all MCP tool calls enforce that only authorized roles can execute them. | `agents/mitigation_agent.py` -> `safe_quarantine_batch()`, `safe_create_ticket()` |

## Security Controls Summary

Recall Sentinel employs a defense-in-depth approach with four primary security layers:

1. **Role-Based Access Control (RBAC)**: Validates authorization dynamically before allowing critical actions to be executed against external MCP servers.
2. **PII Redaction (GDPR/CCPA Layer)**: Prevents accidental data exfiltration of personal identifiers to language models via proactive regex scrubbing.
3. **Prompt Injection Defense (OWASP LLM Top 10)**: Inspects and sanitizes free-text inputs against malicious override prompts to ensure LLM agent safety.
4. **Static Analysis (Semgrep Pre-Commit Scanning)**: Automatically scans for hardcoded secrets, unsafe LLM prompt construction, and missing authorization checks before any code is committed.
