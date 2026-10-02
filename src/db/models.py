from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON, Index
from sqlalchemy.orm import relationship
from .session import Base

class Source(Base):
    __tablename__ = "sources"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False) # news, social
    
class Company(Base):
    __tablename__ = "companies"
    ticker = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    sector = Column(String)
    industry = Column(String)
    systemic_importance = Column(Float, default=0.5)

class Document(Base):
    __tablename__ = "documents"
    document_id = Column(String, primary_key=True, index=True)
    source_id = Column(String, ForeignKey("sources.id"))
    source_type = Column(String)
    data_origin = Column(String) # PUBLIC-REAL, CURATED-REPLAY, SYNTHETIC
    ingest_mode = Column(String) # LIVE, REPLAY, BATCH
    headline = Column(Text, nullable=False)
    text = Column(Text)
    url = Column(String)
    author = Column(String)
    language = Column(String, default="en")
    published_at = Column(DateTime)
    ingested_at = Column(DateTime, default=datetime.utcnow)

class Event(Base):
    __tablename__ = "events"
    event_id = Column(String, primary_key=True, index=True)
    first_seen = Column(DateTime)
    last_seen = Column(DateTime)
    n_docs = Column(Integer, default=1)
    n_sources = Column(Integer, default=1)
    representative_doc_id = Column(String, ForeignKey("documents.document_id"))

class RiskSignal(Base):
    __tablename__ = "risk_signals"
    signal_id = Column(String, primary_key=True, index=True)
    document_id = Column(String, ForeignKey("documents.document_id"), nullable=False)
    event_id = Column(String, ForeignKey("events.event_id"))
    
    timestamp = Column(DateTime, index=True)
    processed_at = Column(DateTime, default=datetime.utcnow)
    
    source = Column(String)
    source_type = Column(String)
    data_origin = Column(String)
    ingest_mode = Column(String)
    
    headline = Column(Text)
    text_excerpt = Column(Text)
    url = Column(String)
    
    primary_company = Column(String, index=True) # ticker
    scope = Column(String) # company, sector, market
    
    sentiment_score = Column(Float)
    sentiment_label = Column(String)
    sentiment_confidence = Column(Float)
    
    event_type = Column(String, index=True)
    event_confidence = Column(Float)
    event_top2 = Column(String)
    
    direction = Column(String) # adverse, favourable, neutral
    
    impact_score = Column(Float, index=True)
    risk_level = Column(String) # Low, Medium, High, Critical
    
    impact_reasoning = Column(JSON) # explanation object
    entities = Column(JSON)
    companies = Column(JSON)
    regions = Column(JSON)
    
    signal_confidence = Column(Float)
    corroboration_count = Column(Integer, default=1)
    stress_eligible = Column(Boolean, default=False)
    model_version = Column(JSON)

class Portfolio(Base):
    __tablename__ = "portfolios"
    portfolio_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class PortfolioPosition(Base):
    __tablename__ = "portfolio_positions"
    position_id = Column(String, primary_key=True, index=True)
    portfolio_id = Column(String, ForeignKey("portfolios.portfolio_id"))
    asset_class = Column(String, nullable=False)
    instrument_type = Column(String, nullable=False)
    obligor = Column(String)
    ticker = Column(String)
    sector = Column(String)
    country = Column(String)
    currency = Column(String, default="USD")
    notional = Column(Float)
    current_value = Column(Float)
    exposure = Column(Float) # EAD
    rating_bucket = Column(String)
    maturity_years = Column(Float)
    rate_type = Column(String)
    modified_duration = Column(Float)
    convexity = Column(Float)
    spread_duration = Column(Float)
    dv01 = Column(Float)
    delta = Column(Float)
    beta = Column(Float)
    lgd = Column(Float)
    pd_base = Column(Float)
    data_origin = Column(String)

class StressRun(Base):
    __tablename__ = "stress_runs"
    run_id = Column(String, primary_key=True, index=True)
    trigger_signal_id = Column(String, ForeignKey("risk_signals.signal_id"), nullable=True)
    event_type = Column(String)
    impact_score = Column(Float)
    multiplier = Column(Float)
    scenario_name = Column(String)
    shocks_applied = Column(JSON)
    
    portfolio_id = Column(String, ForeignKey("portfolios.portfolio_id"))
    portfolio_value_before = Column(Float)
    portfolio_value_after = Column(Float)
    absolute_loss = Column(Float)
    pct_loss = Column(Float)
    
    run_mode = Column(String) # auto, manual, combined
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

class StressPositionResult(Base):
    __tablename__ = "stress_position_results"
    result_id = Column(String, primary_key=True, index=True)
    run_id = Column(String, ForeignKey("stress_runs.run_id"))
    position_id = Column(String, ForeignKey("portfolio_positions.position_id"))
    value_before = Column(Float)
    value_after = Column(Float)
    loss = Column(Float)
    driver_breakdown = Column(JSON) # {rate, spread, equity, credit_loss, fx, vol}
