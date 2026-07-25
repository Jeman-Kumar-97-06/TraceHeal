from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class AlertDetail(BaseModel):
    category: str = Field(..., description="LATENCY, RESOURCE, or SECURITY")
    severity: str = Field(..., description="INFO, WARNING, or CRITICAL")
    message: str
    metric_value: Optional[float] = None
    threshold_value: Optional[float] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None

class SentinelReport(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    target_service: str = "LocalAgent1"
    status: str = "HEALTHY"  # HEALTHY, WARNING, CRITICAL
    total_spans_analyzed: int = 0
    alerts: List[AlertDetail] = []