from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.risk_engine.schemas import EntityMatch

class HealthResponse(BaseModel):
    status: str
    version: str

class ModeResponse(BaseModel):
    current_mode: str # 'REPLAY' or 'LIVE'
    live_available: bool

class ReplayStateResponse(BaseModel):
    status: str # 'running', 'paused', 'stopped'
    speed: float
    processed_count: int
    total_count: int

class APIRiskSignal(BaseModel):
    signal_id: str
    document_id: str
    timestamp: datetime
    source: str
    source_type: str
    data_origin: str
    ingest_mode: str
    provenance: str
    headline: str
    text_excerpt: Optional[str] = None
    primary_company: Optional[str] = None
    scope: Optional[str] = None
    sentiment_score: float
    sentiment_label: str
    event_type: str
    event_confidence: float
    direction: str
    impact_score: float
    risk_level: str
    impact_reasoning: Dict[str, Any]
    entities: List[EntityMatch] = []
    signal_confidence: float
    stress_eligible: bool
    stress_run_id: Optional[str] = None

class APIStressRun(BaseModel):
    run_id: str
    triggering_signal_id: Optional[str]
    scenario: str
    portfolio_value_before: float
    portfolio_value_after: float
    absolute_loss: float
    pct_loss: float
    shocks_applied: Dict[str, Any]
    run_mode: str
    timestamp: datetime

class DashboardOverviewResponse(BaseModel):
    mode: str
    total_signals: int
    total_stress_runs: int
    portfolio_value: float
    severity_counts: Dict[str, int]

class AnalyzeRequest(BaseModel):
    text: str
    source: str = "manual"
