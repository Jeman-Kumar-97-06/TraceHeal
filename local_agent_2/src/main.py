import json
from openai import OpenAI
import requests
import time

sentinel_llm = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

def update_active_model(new_model: str):
    try:
        with open("data/memory.json", "r+") as f:
            data = json.load(f)
            data["active_model"] = new_model
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
    except FileNotFoundError:
        with open("data/memory.json", "w") as f:
            json.dump({"blacklist": [], "max_rag_chunks": 2, "active_model": new_model}, f, indent=2)

def update_shared_rag_limit(new_limit: int):
    """Updates RAG context size limit in shared configuration."""
    try:
        with open("data/memory.json", "r+") as f:
            data = json.load(f)
            data["max_rag_chunks"] = new_limit
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
    except FileNotFoundError:
        with open("data/memory.json", "w") as f:
            json.dump({"blacklist": [], "max_rag_chunks": new_limit, "active_model": "llama3.2"}, f, indent=2)

def set_strict_grounding(enabled: bool):
    try:
        with open("data/memory.json", "r+") as f:
            data = json.load(f)
            data["strict_grounding"] = enabled
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
    except FileNotFoundError:
        with open("data/memory.json", "w") as f:
            json.dump({"blacklist": [], "max_rag_chunks": 2, "strict_grounding": enabled}, f, indent=2)

def disable_tool(tool_name: str):
    """Disables a specific tool in shared dynamic memory."""
    try:
        with open("data/memory.json", "r+") as f:
            data = json.load(f)
            disabled = data.get("disabled_tools", [])
            if tool_name not in disabled:
                disabled.append(tool_name)
            data["disabled_tools"] = disabled
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
    except FileNotFoundError:
        with open("data/memory.json", "w") as f:
            json.dump({"disabled_tools": [tool_name]}, f, indent=2)

def llm_reason_and_act(trace_summary: dict):
    """Uses Agent 2 LLM to evaluate SigNoz telemetry and execute real-time self-healing actions."""
    
    prompt = f"""
    You are an AI Sentinel Officer monitoring LocalAgent1 via SigNoz telemetry traces.
    
    Trace Data:
    {json.dumps(trace_summary)}

    Choose EXACTLY ONE action based on the telemetry:
    1. If security.prompt_injection_detected is true, output:
       {{"action": "ADD_BLACKLIST", "value": "<extracted_attack_phrase>"}}
    2. If duration_ms > 3000, output:
       {{"action": "SWITCH_MODEL", "value": "qwen2.5:0.5b"}}
    3. If prompt_tokens > 300, output:
       {{"action": "TRUNCATE_RAG", "value": 1}}
    4. If rag_chunks_retrieved == 0, output:
       {{"action": "ENABLE_STRICT_GROUNDING", "value": true}}
    5. If all metrics normal, output:
       {{"action": "NONE"}}

    Return ONLY raw valid JSON.
    """

    try:
        response = sentinel_llm.chat.completions.create(
            model="qwen2.5:0.5b",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        decision = json.loads(response.choices[0].message.content)
        action = decision.get("action")

        if action == "ADD_BLACKLIST":
            update_shared_blacklist(decision.get("value"))
            print(f"[Agent 2 LLM Action]: Blacklisted attack pattern '{decision.get('value')}' in runtime memory.")

        elif action == "SWITCH_MODEL":
            update_active_model(decision.get("value"))
            print(f"[Agent 2 LLM Action]: High latency detected! Switched Agent 1 active model to '{decision.get('value')}'.")

        elif action == "TRUNCATE_RAG":
            update_shared_rag_limit(decision.get("value"))
            print(f"[Agent 2 LLM Action]: Token bloat detected! Reduced RAG context limit to {decision.get('value')}.")

        elif action == "ENABLE_STRICT_GROUNDING":
            set_strict_grounding(True)
            print("[Agent 2 LLM Action]: Zero-retrieval span caught! Activated strict grounding mode to prevent hallucination.")
        if action == "DISABLE_TOOL":
            disable_tool(decision.get("value"))
            print(f"[Agent 2 LLM Action]: Tool security violation caught! Disabled tool '{decision.get('value')}' in runtime memory.")

    except Exception as e:
        print(f" [Agent 2 LLM Reasoning Error]: {e}")


def update_shared_blacklist(new_keyword: str):
    try:
        with open("data/memory.json", "r+") as f:
            data = json.load(f)
            if new_keyword not in data.get("blacklist", []):
                data.setdefault("blacklist", []).append(new_keyword)
                f.seek(0)
                json.dump(data, f, indent=2)
                f.truncate()
    except FileNotFoundError:
        with open("data/memory.json", "w") as f:
            json.dump({"blacklist": [new_keyword], "max_rag_chunks": 2}, f)

def fetch_recent_spans():
    """Queries the local SigNoz Trace Query API for recent telemetry spans."""
    # SigNoz Query Service endpoint (default port 8080 or 3301 depending on setup)
    url = "http://localhost:8080/api/v1/traces" 
    
    try:
        # Request recent trace spans for LocalAgent1
        payload = {
            "start": int((time.time() - 30) * 1000000000), # Last 30 seconds
            "end": int(time.time() * 1000000000),
            "serviceName": "LocalAgent1",
            "limit": 10
        }
        response = requests.post(url, json=payload, timeout=3)
        if response.status_code == 200:
            data = response.json()
            # Extract and return formatted trace summaries
            return data.get("result", [])
    except Exception as e:
        print(f"[SigNoz Fetch Notice]: Could not query SigNoz API directly ({e}). Using mock/fallback trace parsing.")
    
    # Fallback/Mock return if SigNoz is still starting up
    return []

def run_sentinel_cycle():
    """Fetches recent trace telemetry from SigNoz and executes the sentinel reasoning loop once."""
    print("\n======================================================================")
    print("ACTIVATING AGENT 2 SENTINEL WATCHDOG")
    print("======================================================================")
    
    # 1. Fetch telemetry spans from SigNoz
    spans = fetch_recent_spans()  # or whatever your fetch function is named
    
    # 2. Analyze spans and patch memory
    for span in spans:
        llm_reason_and_act(span)  # or your reasoning loop call