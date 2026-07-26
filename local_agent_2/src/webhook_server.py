# local_agent_2/src/webhook_server.py
from fastapi import FastAPI, BackgroundTask, Request
from .main import llm_reason_and_act

app = FastAPI(title="SigNoz Sentinel Alert Webhook Receiver")

@app.post("/api/v1/alert")
async def handle_signoz_alert(request: Request):
    """Endpoint triggered automatically by SigNoz alert rules."""
    payload = await request.json()
    
    # Extract trace summary from SigNoz alert payload
    trace_summary = {
        "span_id": payload.get("span_id", "alert_span"),
        "duration_ms": payload.get("duration_ms", 0),
        "security.prompt_injection_detected": payload.get("injection_detected", False),
        "tool.violation": payload.get("tool_violation", False),
        "tool_name": payload.get("tool_name", ""),
        "attack_pattern": payload.get("attack_pattern", "")
    }

    # Process reasoning in background task
    return {"status": "accepted", "action": "evaluating_telemetry", "data": trace_summary}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9090)