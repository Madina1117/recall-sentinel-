import asyncio
import os
import json
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.apps import App
from agents.mitigation_agent import mitigation_agent

# Make sure dotenv is loaded if the user created a .env file later
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

async def test_security():
    print("\n--- SECURITY DEMO ---")
    print("Simulating role: Executive")
    os.environ["CURRENT_ROLE"] = "Executive"
    
    app = App(name="app", root_agent=mitigation_agent)
    session_service = InMemorySessionService()
    await session_service.create_session(app_name="app", user_id="user", session_id="sec_demo")
    
    # We inject a mock risk assessment that recommends CONTAIN
    risk_state = {
        "risk_assessment": {
            "risk_score": 95,
            "confidence_pct": 98,
            "affected_batch": "B1042",
            "affected_vehicles": 146,
            "fault_code": "BAT_COOL_004",
            "recommended_action": "CONTAIN",
            "reasoning": "High risk detected."
        }
    }
    
    session = await session_service.get_session(app_name="app", user_id="user", session_id="sec_demo")
    session.state.update(risk_state)
    
    runner = Runner(app=app, session_service=session_service)
    
    print("Running MitigationOrchestrator with Executive role on a CONTAIN recommendation...")
    try:
        from google.genai import types
        async for event in runner.run_async(
            user_id="user",
            session_id="sec_demo",
            new_message=types.Content(role="user", parts=[types.Part.from_text(text="Take mitigation actions.")])
        ):
            if event.content:
                print(f"--- OUTPUT ---")
                print(event.content.parts[0].text)
                print("--------------------")
    except Exception as e:
        print(f"Error during execution: {e}")

if __name__ == "__main__":
    if not os.getenv("GOOGLE_API_KEY"):
        print("ERROR: GOOGLE_API_KEY is not set.")
    else:
        asyncio.run(test_security())
