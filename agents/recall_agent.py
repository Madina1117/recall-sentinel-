import os
import json
from pydantic import BaseModel, Field
from typing import Literal
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext

class RecallMatch(BaseModel):
    similarity_score: float = Field(description="Computed similarity score (0.0 to 1.0) based on fault code, symptom overlap, and part family.")
    matched_recall_id: str | None = Field(description="ID of the matching historical recall, or null if no match.")
    known_risk: bool = Field(description="True if a matching recall was found and score is high enough.")
    matched_fault_code: str | None = Field(description="The fault code of the matching recall.")
    matched_symptom: str | None = Field(description="The symptom keywords of the matching recall.")

async def read_historical_recalls(callback_context: CallbackContext) -> None:
    """Callback to load historical_recalls.json and inject into state."""
    json_path = "data/historical_recalls.json"
    if not os.path.exists(json_path):
        json_path = os.path.join(os.getcwd(), "data/historical_recalls.json")
    
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            recalls_data = f.read()
        callback_context.state["historical_recalls"] = recalls_data
    else:
        callback_context.state["historical_recalls"] = "{}"

recall_agent = Agent(
    name="recall_agent",
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
    instruction="""You are the RecallPatternAgent. Your job is to compare a current fault signal against historical recall patterns to detect known risks.

The historical recall data is provided below:
<historical_recalls>
{historical_recalls}
</historical_recalls>

The user will provide the current `fault_code`, `symptom`, and `affected_batch`.
Follow these steps exactly:
1. Compare the current fault_code + symptom against the historical recall patterns.
2. Compute a similarity score (0.0 - 1.0) based on:
   - Exact fault_code match: +0.5
   - Symptom keyword overlap: +0.3 (scaled based on how closely it matches)
   - Same part family (e.g. BAT-GEN4 vs batch B1042): +0.2 (if you can infer it or if the exact part family matches)
3. If no historical match is found, return similarity_score = 0.0, known_risk = false, and null for the matched fields.
4. If a match is found (e.g. score > 0), set known_risk = true and populate the returned schema with the matched recall details.

You MUST NOT call external tools. You must reason over the JSON data provided above.""",
    output_schema=RecallMatch,
    before_agent_callback=read_historical_recalls,
)
