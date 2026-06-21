import os
import pandas as pd
from pydantic import BaseModel, Field
from typing import Literal
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext

class SymptomCluster(BaseModel):
    symptom: str = Field(description="A concise description of the recurring symptom cluster.")
    occurrences: int = Field(description="The number of occurrences matching this symptom cluster.")
    severity: Literal["HIGH", "MEDIUM", "LOW"] = Field(description="Severity based on language cues (e.g. burning smell/leak = HIGH, intermittent = MEDIUM, normal/spec = LOW).")

class ServiceNotesAnalysis(BaseModel):
    symptoms: list[SymptomCluster] = Field(description="List of all extracted symptom clusters.")

async def read_service_notes_csv(callback_context: CallbackContext) -> None:
    """Callback to load service_notes.csv and pass raw notes into state."""
    csv_path = "data/service_notes.csv"
    if not os.path.exists(csv_path):
        csv_path = os.path.join(os.getcwd(), "data/service_notes.csv")
        
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        # We only need the technician_note column for the LLM to cluster
        notes = df['technician_note'].tolist()
        
        # We'll format them as a numbered list for easier reading
        notes_text = "\n".join([f"{i+1}. {note}" for i, note in enumerate(notes)])
        
        callback_context.state["raw_notes"] = notes_text
    else:
        callback_context.state["raw_notes"] = "No service notes found."

service_agent = Agent(
    name="service_agent",
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
    instruction="""You are the ServiceNotesAgent. Your job is to read a batch of technician service notes, extract recurring symptoms, and cluster them.

The raw technician notes are provided below:

<raw_notes>
{raw_notes}
</raw_notes>

Follow these steps exactly:
1. Extract recurring symptoms from the technician notes.
2. Cluster similar symptoms together (e.g. "coolant near battery" and "battery connector residue" should be the same cluster).
3. Count the total occurrences of each symptom cluster from the notes.
4. Assign severity (HIGH / MEDIUM / LOW) based on language cues (e.g. "burning smell", "leak", "corroded", "ingress" = HIGH, "intermittent" = MEDIUM, "minor fluctuation", "spec", "normal" = LOW).

You MUST NOT call external tools. You must reason over the raw notes provided above.
Do NOT fabricate occurrences. Only return clusters that appear in the text.""",
    output_schema=ServiceNotesAnalysis,
    before_agent_callback=read_service_notes_csv,
)
