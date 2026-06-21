import os
import pandas as pd
from pydantic import BaseModel, Field
from typing import Literal
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext

class TelemetryRiskAssessment(BaseModel):
    fault_code: str = Field(description="The primary fault code being analyzed. If no single dominant fault, return the highest frequency one.")
    frequency_change_pct: int = Field(description="Frequency change % compared to a baseline window (first 30 days vs last 7 days).")
    affected_vehicles: int = Field(description="Number of unique affected vehicles for this fault code.")
    affected_batch: str = Field(description="Batch ID prefix of affected vehicles (e.g. 'B1042' from 'VIN_B1042_111').")
    risk_signal: Literal["HIGH", "MEDIUM", "LOW"] = Field(description="Risk signal classification based on thresholds.")

async def read_telemetry_csv(callback_context: CallbackContext) -> None:
    """Callback to compute telemetry stats and inject them into state before the model runs."""
    csv_path = "data/telemetry.csv"
    if not os.path.exists(csv_path):
        csv_path = os.path.join(os.getcwd(), "data/telemetry.csv")
    
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # 1. Group by fault_code
        top_fault = df['fault_code'].value_counts().idxmax()
        fault_df = df[df['fault_code'] == top_fault]
        
        # 2. Calculate frequency change %
        min_date = fault_df['timestamp'].min()
        max_date = fault_df['timestamp'].max()
        
        baseline_mask = (fault_df['timestamp'] >= min_date) & (fault_df['timestamp'] <= min_date + pd.Timedelta(days=30))
        baseline_count = baseline_mask.sum()
        
        recent_mask = (fault_df['timestamp'] >= max_date - pd.Timedelta(days=7)) & (fault_df['timestamp'] <= max_date)
        recent_count = recent_mask.sum()
        
        baseline_rate = baseline_count / 30.0 if baseline_count > 0 else 1.0 # avoid div/0
        recent_rate = recent_count / 7.0
        
        change_pct = int(((recent_rate - baseline_rate) / baseline_rate) * 100)
        if change_pct < 0:
            change_pct = 0
            
        # 3. Affected vehicles and batch
        affected_vehicles = fault_df['vehicle_id'].nunique()
        batch_id = fault_df['vehicle_id'].iloc[0].split('_')[1]
        
        callback_context.state["telemetry_stats"] = {
            "fault_code": top_fault,
            "frequency_change_pct": change_pct,
            "affected_vehicles": affected_vehicles,
            "affected_batch": batch_id
        }
    else:
        callback_context.state["telemetry_stats"] = "No telemetry data found."

telemetry_agent = Agent(
    name="telemetry_agent",
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
    instruction="""You are the TelemetryAgent. Your job is to analyze vehicle telemetry data to detect emerging defect patterns.
The mathematical calculation has already been done for you by an internal system. You will receive the deterministic pre-calculated statistics below.

<computed_stats>
{telemetry_stats}
</computed_stats>

Follow these steps exactly:
1. Extract the `fault_code`, `frequency_change_pct`, `affected_vehicles`, and `affected_batch` directly from the computed stats provided above. Do not alter them.
2. Classify risk signal as HIGH / MEDIUM / LOW based on these frequency thresholds applied to the computed stats:
  - HIGH: frequency increase > 100% AND affected_vehicles > 50
  - MEDIUM: frequency increase > 100% OR affected_vehicles > 20
  - LOW: everything else

You MUST NOT call external tools.
If no spike is detected, return risk_signal: 'LOW'.""",
    output_schema=TelemetryRiskAssessment,
    before_agent_callback=read_telemetry_csv,
)
