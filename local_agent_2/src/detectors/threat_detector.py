from typing import List, Dict, Any
from shared.alert_schema import AlertDetail

def evaluate_threats(spans: List[Dict[str, Any]]) -> List[AlertDetail]:
    alerts = []
    for span in spans:
        attributes = span.get("tagMap", {})
        is_attack = attributes.get("security.prompt_injection_detected", False)
        pattern = attributes.get("security.attack_pattern", "Unknown")
        trace_id = span.get("traceId", "unknown")

        if is_attack:
            alerts.append(AlertDetail(
                category="SECURITY",
                severity="CRITICAL",
                message=f"🚨 PROMPT INJECTION ATTACK DETECTED! Keyword pattern matched: '{pattern}'",
                trace_id=trace_id
            ))
    return alerts