import streamlit as st
import asyncio
import os
import sys
import json
import pandas as pd
from dotenv import load_dotenv

# Add project root to sys.path so we can import agents
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.telemetry_agent import telemetry_agent
from agents.service_agent import service_agent
from agents.recall_agent import recall_agent
from agents.risk_agent import risk_agent
from agents.mitigation_agent import mitigation_agent

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.apps import App
from google.genai import types

load_dotenv()

st.set_page_config(page_title="Recall Sentinel", layout="wide")

st.title("Recall Sentinel 🛡️")
st.markdown("### Autonomous Vehicle Defect Detection & Mitigation System")
st.markdown("This system analyzes telemetry spikes, technician service notes, and historical recall patterns to autonomously quarantine defective vehicle batches and alert engineers before a human notices.")

st.sidebar.header("Configuration")
role = st.sidebar.selectbox("Select Your Role", ["Engineer", "Manufacturing", "Executive"])

st.sidebar.markdown("---")
st.sidebar.markdown("**Pre-loaded Synthetic Data:**")
st.sidebar.markdown("✅ `telemetry.csv` (10,000+ records)")
st.sidebar.markdown("✅ `service_notes.csv` (Unstructured text)")
st.sidebar.markdown("✅ `historical_recalls.json`")

async def run_agent(agent, session_id, initial_state=None, prompt="Analyze the data."):
    app = App(name="app", root_agent=agent)
    session_service = InMemorySessionService()
    await session_service.create_session(app_name="app", user_id="user", session_id=session_id)
    
    if initial_state:
        session = await session_service.get_session(app_name="app", user_id="user", session_id=session_id)
        session.state.update(initial_state)
        
    runner = Runner(app=app, session_service=session_service)
    result_json = None
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            async for event in runner.run_async(
                user_id="user",
                session_id=session_id,
                new_message=types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
            ):
                if event.content:
                    text = event.content.parts[0].text
                    if "```json" in text:
                        text = text.split("```json")[1].split("```")[0].strip()
                    elif "```" in text:
                        text = text.split("```")[1].strip()
                        
                    try:
                        result_json = json.loads(text)
                    except json.JSONDecodeError:
                        pass
            return result_json  # Success, return immediately
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "ResourceExhausted" in error_msg:
                if attempt < max_retries - 1:
                    st.warning(f"Rate limited (429)! Waiting 30 seconds and retrying {agent.name} (Attempt {attempt + 2}/{max_retries})...")
                    await asyncio.sleep(30)
                else:
                    st.error(f"Failed to run {agent.name} after {max_retries} attempts due to rate limits.")
                    return None
            else:
                st.error(f"Error running {agent.name}: {e}")
                return None
                
    return result_json

async def run_analysis():
    progress_bar = st.progress(0, text="Initializing Agents...")
    
    # --- AGENT 1: Telemetry ---
    progress_bar.progress(10, text="Agent 1: Analyzing Telemetry Data...")
    res1 = await run_agent(telemetry_agent, "s1")
    await asyncio.sleep(8)
    
    st.markdown("### 1. Telemetry Agent")
    if res1:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Fault Code", res1.get("fault_code", "N/A"))
        c2.metric("Frequency Change", f"+{res1.get('frequency_change_pct', 0)}%")
        c3.metric("Affected Vehicles", res1.get("affected_vehicles", 0))
        
        signal = res1.get("risk_signal", "LOW")
        color = "red" if signal == "HIGH" else "orange" if signal == "MEDIUM" else "green"
        c4.markdown(f"**Risk Signal:** <br><span style='color:{color}; font-size:32px; font-weight:bold;'>{signal}</span>", unsafe_allow_html=True)
        
    st.divider()

    # --- AGENT 2: Service Notes ---
    progress_bar.progress(30, text="Agent 2: Clustering NLP Service Notes...")
    res2 = await run_agent(service_agent, "s2")
    await asyncio.sleep(8)
    
    st.markdown("### 2. Service Notes Agent")
    if res2 and "symptoms" in res2:
        df = pd.DataFrame(res2["symptoms"])
        st.dataframe(df, use_container_width=True)
    
    st.divider()

    # --- AGENT 3: Recall Pattern ---
    progress_bar.progress(50, text="Agent 3: Checking Historical Databases...")
    if res1 and res2:
        fault_code = res1.get("fault_code", "UNKNOWN")
        symptom = res2.get("symptoms", [{}])[0].get("symptom", "UNKNOWN") if res2.get("symptoms") else "UNKNOWN"
        batch = res1.get("affected_batch", "UNKNOWN")
        prompt = f"Current fault_code: '{fault_code}', top symptom: '{symptom}', affected_batch: '{batch}'."
    else:
        prompt = "Analyze the data."
        
    res3 = await run_agent(recall_agent, "s3", prompt=prompt)
    await asyncio.sleep(8)
    
    st.markdown("### 3. Recall Pattern Agent")
    if res3:
        c1, c2 = st.columns(2)
        c1.metric("Historical Match ID", res3.get("matched_recall_id", "None"))
        c2.metric("Similarity Score", f"{res3.get('similarity_score', 0):.2f}")
    
    st.divider()

    # --- AGENT 4: Risk Assessment ---
    progress_bar.progress(70, text="Agent 4: Synthesizing Risk Score...")
    risk_state = {
        "telemetry_result": res1 or {},
        "service_result": res2 or {},
        "recall_result": res3 or {}
    }
    res4 = await run_agent(risk_agent, "s4", initial_state=risk_state, prompt="Assess overall risk.")
    await asyncio.sleep(8)
    
    st.markdown("### 4. Risk Assessment Agent")
    if res4:
        c1, c2 = st.columns(2)
        score = res4.get("risk_score", 0)
        c1.markdown(f"<div style='text-align: center;'><h4>Overall Risk Score</h4><h1 style='color: {'red' if score >= 70 else 'orange' if score >= 40 else 'green'}; font-size: 72px;'>{score}/100</h1></div>", unsafe_allow_html=True)
        
        action = res4.get("recommended_action", "CLEAR")
        box_color = "#ff4b4b" if action == "CONTAIN" else "#ffa500" if action == "MONITOR" else "#00cc66"
        c2.markdown(f"<div style='background-color: {box_color}; padding: 20px; border-radius: 10px; text-align: center; color: white;'><h4>Recommended Action</h4><h1 style='color: white;'>{action}</h1></div>", unsafe_allow_html=True)
    
    st.divider()

    # --- AGENT 5: Mitigation ---
    progress_bar.progress(90, text="Agent 5: Executing Containment MCP Tools...")
    mit_state = {"risk_assessment": res4 or {}}
    res5 = await run_agent(mitigation_agent, "s5", initial_state=mit_state, prompt="Take mitigation actions.")
    
    progress_bar.progress(100, text="Analysis Complete!")
    
    st.markdown("### 5. Mitigation Orchestrator")
    if res5:
        brief = res5.get("brief", "")
        
        # Check for Security Denial
        if "Unauthorized" in brief and "Executive" in brief:
            st.error(f"🚨 **SECURITY DENIAL:** {brief}")
        else:
            c1, c2 = st.columns(2)
            actions = res5.get("actions_taken", [])
            c1.markdown("**MCP Actions Executed:**")
            for a in actions:
                c1.markdown(f"- `{a}`")
                
            c2.metric("Investigation Ticket", res5.get("ticket_id", "None"))
            c2.metric("Quarantine Status", res5.get("quarantine_status", "None"))
            
            st.markdown("#### Executive Brief")
            st.info(brief)

if st.sidebar.button("Run Analysis", type="primary"):
    os.environ["CURRENT_ROLE"] = role
    st.sidebar.success(f"Role initialized as: {role}")
    asyncio.run(run_analysis())
