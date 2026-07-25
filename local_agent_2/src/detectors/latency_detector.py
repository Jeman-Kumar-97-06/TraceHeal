from typing import List, Dict, Any
from shared.alert_schema import AlertDetail

LATENCY_THRESHOLD_MS = 2500.0  # 2.5 seconds limit

def evaluate_latency(spans: List[Dict[str, Any]]) -> List[AlertDetail]:
    alerts = []
    for span in spans:
        duration_ms = span.get("durationNano", 0) / 1_000_000.0
        trace_id = span.get("traceId", "unknown")
        
        if duration_ms > LATENCY_THRESHOLD_MS:
            alerts.append(AlertDetail(
                category="LATENCY",
                severity="WARNING",
                message=f"Prompt response latency exceeded threshold ({duration_ms:.1f}ms > {LATENCY_THRESHOLD_MS}ms)",
                metric_value=duration_ms,
                threshold_value=LATENCY_THRESHOLD_MS,
                trace_id=trace_id
            ))
    return alerts