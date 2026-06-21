import asyncio
import os
import json
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.apps import App
from agents.telemetry_agent import telemetry_agent
from agents.service_agent import service_agent
from agents.recall_agent import recall_agent
from agents.risk_agent import risk_agent

from agents.mitigation_agent import mitigation_agent

# Make sure dotenv is loaded if the user created a .env file later
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

async def run_agent_and_get_json(agent, data_desc, session_id, initial_state=None, prompt="Analyze the data."):
    print(f"\nInitializing ADK app and runner for {agent.name}...")
    app = App(name="app", root_agent=agent)
    session_service = InMemorySessionService()
    await session_service.create_session(app_name="app", user_id="user", session_id=session_id)
    
    if initial_state:
        # We need to inject state into the session before running
        session = await session_service.get_session(app_name="app", user_id="user", session_id=session_id)
        session.state.update(initial_state)
        
    runner = Runner(app=app, session_service=session_service)
    
    print(f"Running {agent.name} on {data_desc}...\n")
    
    result_json = None
    try:
        from google.genai import types
        async for event in runner.run_async(
            user_id="user",
            session_id=session_id,
            new_message=types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
        ):
            if event.content:
                print(f"--- {agent.name.upper()} OUTPUT ---")
                text = event.content.parts[0].text
                print(text)
                print("--------------------")
                
                # Extract json block
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].strip()
                    
                try:
                    result_json = json.loads(text)
                except json.JSONDecodeError:
                    pass
    except Exception as e:
        print(f"Error during execution: {e}")
        
    return result_json

async def main():
    if not os.getenv("GOOGLE_API_KEY"):
        print("ERROR: GOOGLE_API_KEY is not set. Please set it in your environment or .env file.")
        return

    # 1. Telemetry Agent
    telemetry_result = await run_agent_and_get_json(telemetry_agent, "data/telemetry.csv", "s1")
    await asyncio.sleep(15)
    
    # 2. Service Agent
    service_result = await run_agent_and_get_json(service_agent, "data/service_notes.csv", "s2")
    await asyncio.sleep(15)
    
    # 3. Recall Agent
    if telemetry_result and service_result:
        fault_code = telemetry_result.get("fault_code", "UNKNOWN")
        symptom = service_result.get("symptoms", [{}])[0].get("symptom", "UNKNOWN")
        batch = telemetry_result.get("affected_batch", "UNKNOWN")
        recall_prompt = f"Current fault_code: '{fault_code}', top symptom: '{symptom}', affected_batch: '{batch}'."
    else:
        recall_prompt = "Current fault_code: 'BAT_COOL_004', top symptom: 'coolant residue near battery connectors', affected_batch: 'B1042'."
        
    recall_result = await run_agent_and_get_json(recall_agent, "data/historical_recalls.json", "s3", prompt=recall_prompt)
    await asyncio.sleep(15)
    
    # 4. Risk Assessment Agent
    risk_state = {
        "telemetry_result": telemetry_result or {},
        "service_result": service_result or {},
        "recall_result": recall_result or {}
    }
    
    risk_result = await run_agent_and_get_json(risk_agent, "orchestrated inputs", "s4", initial_state=risk_state, prompt="Assess the overall risk.")
    await asyncio.sleep(15)
    
    # 5. Mitigation Orchestrator Agent
    mitigation_state = {
        "risk_assessment": risk_result or {}
    }
    
    await run_agent_and_get_json(mitigation_agent, "risk assessment", "s5", initial_state=mitigation_state, prompt="Take the necessary mitigation actions based on the risk assessment.")

if __name__ == "__main__":
    asyncio.run(main())
