import os
from pydantic import BaseModel, Field
from typing import Literal
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext

class RiskAssessment(BaseModel):
    risk_score: int = Field(description="The computed risk score (0-100).")
    confidence_pct: int = Field(description="Confidence percentage based on the completeness and strength of the signals.")
    affected_batch: str = Field(description="The affected vehicle batch ID.")
    affected_vehicles: int = Field(description="The total number of affected vehicles.")
    fault_code: str = Field(description="The primary fault code.")
    recommended_action: Literal["CONTAIN", "MONITOR", "CLEAR"] = Field(description="Recommended containment action based on score.")
    reasoning: str = Field(description="A concise executive reasoning paragraph explaining the recommendation.")

async def compute_risk_score(callback_context: CallbackContext) -> None:
    """Callback to deterministically compute the risk score based on agent inputs."""
    t_result = callback_context.state.get("telemetry_result", {})
    s_result = callback_context.state.get("service_result", {})
    r_result = callback_context.state.get("recall_result", {})
    
    risk_score = 0
    
    # 1. Telemetry signal
    t_signal = t_result.get("risk_signal", "LOW")
    if t_signal == "HIGH":
        risk_score += 40
    elif t_signal == "MEDIUM":
        risk_score += 20
        
    # 2. Historical recall signal
    known_risk = r_result.get("known_risk", False)
    if known_risk:
        risk_score += 30
        
    sim_score = r_result.get("similarity_score", 0.0)
    if sim_score > 0.7:
        risk_score += 15
        
    # 3. Service notes signal
    symptoms = s_result.get("symptoms", [])
    top_symptom_severity = "LOW"
    if symptoms and isinstance(symptoms, list):
        top_symptom_severity = symptoms[0].get("severity", "LOW")
        
    if top_symptom_severity == "HIGH":
        risk_score += 15
        
    # Cap score at 100 just in case
    risk_score = min(risk_score, 100)
    
    callback_context.state["computed_risk"] = {
        "risk_score": risk_score,
        "affected_batch": t_result.get("affected_batch", "UNKNOWN"),
        "affected_vehicles": t_result.get("affected_vehicles", 0),
        "fault_code": t_result.get("fault_code", "UNKNOWN")
    }

risk_agent = Agent(
    name="risk_agent",
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
    instruction="""You are the RiskAssessmentAgent. An internal python orchestrator has computed the exact risk score based on inputs from three other agents.

<computed_risk>
{computed_risk}
</computed_risk>

Follow these steps exactly:
1. Review the provided computed risk score. Do not change it.
2. Determine the recommended action based strictly on the score:
   - CONTAIN if score >= 70
   - MONITOR if score is between 40 and 69
   - CLEAR if score < 40
3. Write a concise executive reasoning paragraph explaining the recommendation. Mention the data signals that led to this score, e.g. the fault code spike and matched recall. (Assume confidence is 90-95% when multiple strong signals are present).
4. Populate the final output schema with the exact values from <computed_risk> along with your calculated confidence_pct, recommendation, and reasoning.

You MUST NOT call external tools.""",
    output_schema=RiskAssessment,
    before_agent_callback=compute_risk_score,
)
