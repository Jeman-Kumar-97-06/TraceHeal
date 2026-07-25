from typing import List, Dict, Any
from shared.alert_schema import AlertDetail

PROMPT_TOKEN_LIMIT = 300  # Threshold for context bloat in local memory

def evaluate_resources(spans: List[Dict[str, Any]]) -> List[AlertDetail]:
    alerts = []
    for span in spans:
        attributes = span.get("tagMap", {})
        prompt_tokens = attributes.get("gen_ai.prompt_tokens_est", 0)
        trace_id = span.get("traceId", "unknown")

        if prompt_tokens > PROMPT_TOKEN_LIMIT:
            alerts.append(AlertDetail(
                category="RESOURCE",
                severity="WARNING",
                message=f"Context token bloat detected! Input tokens ({prompt_tokens}) exceeded limit ({PROMPT_TOKEN_LIMIT})",
                metric_value=float(prompt_tokens),
                threshold_value=float(PROMPT_TOKEN_LIMIT),
                trace_id=trace_id
            ))
    return alerts