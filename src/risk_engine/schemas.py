from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class RawDocument(BaseModel):
    document_id: str
    source_id: str
    source_type: str # 'news' | 'social'
    data_origin: str # 'PUBLIC-REAL' | 'CURATED-REPLAY' | 'SYNTHETIC'
    ingest_mode: str # 'LIVE' | 'REPLAY' | 'BATCH'
    headline: str
    text: Optional[str] = None
    url: Optional[str] = None
    author: Optional[str] = None
    language: str = "en"
    published_at: datetime
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    native_ticker_hint: Optional[str] = None
    source_meta: Optional[Dict[str, Any]] = None

class EntityMatch(BaseModel):
    text: str
    type: str # 'ORG', 'GPE', 'PERSON', 'MONEY', etc.
    ticker: Optional[str] = None
    match_type: str # 'cashtag', 'alias', 'fuzzy', 'ner-only'
    confidence: float

class RiskSignalSchema(BaseModel):
    signal_id: str
    document_id: str
    event_id: Optional[str] = None
    timestamp: datetime
    processed_at: datetime
    
    source: str
    source_type: str
    data_origin: str
    ingest_mode: str
    
    headline: str
    text_excerpt: Optional[str] = None
    url: Optional[str] = None
    
    primary_company: Optional[str] = None
    scope: Optional[str] = None
    regions: List[str] = []
    
    sentiment_score: float
    sentiment_label: str
    sentiment_confidence: float
    
    event_type: str
    event_confidence: float
    event_top2: Optional[str] = None
    
    direction: str
    
    impact_score: float
    risk_level: str
    
    impact_reasoning: Dict[str, Any]
    entities: List[EntityMatch] = []
    companies: Dict[str, float] = {} # ticker to weight mapping
    
    signal_confidence: float
    corroboration_count: int = 1
    stress_eligible: bool = False
    model_version: Dict[str, str] = {}
