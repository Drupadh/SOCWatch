from pydantic import BaseModel
from typing import List, Optional

class AlertBase(BaseModel):
    source_ip: str
    attack_type: str
    attempt_count: int
    severity: str

class AlertResponse(AlertBase):
    id: int
    created_at: str

class DashboardStatsResponse(BaseModel):
    total_alerts: int
    critical_alerts: int
    high_alerts: int
    medium_alerts: int

class ParsedLog(BaseModel):
    ip_address: str
    status: str
    timestamp: str
    username: str
    raw_log: str
