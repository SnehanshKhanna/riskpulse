from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from src.db.session import get_db
from src.db.models import RiskSignal, StressRun, Portfolio, PortfolioPosition
from src.api.schemas import HealthResponse, ModeResponse, ReplayStateResponse, APIRiskSignal, APIStressRun, AnalyzeRequest, DashboardOverviewResponse
from src.api.replay import replay_manager
from src.api.live_polling import live_service
from src.risk_engine.engine import RiskEngine
from src.risk_engine.schemas import RawDocument
from datetime import datetime
import uuid

router = APIRouter()

# Global mode
APP_MODE = "REPLAY" # Default

@router.get("/", response_model=HealthResponse)
def root():
    return HealthResponse(status="ok", version="1.0.0")

@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok", version="1.0.0")

@router.get("/mode", response_model=ModeResponse)
def get_mode():
    return ModeResponse(
        current_mode=APP_MODE,
        live_available=True 
    )

@router.post("/mode")
async def set_mode(mode: str):
    global APP_MODE
    if mode.upper() not in ["LIVE", "REPLAY"]:
        raise HTTPException(400, "Mode must be LIVE or REPLAY")
    APP_MODE = mode.upper()
    
    if APP_MODE == "LIVE":
        live_service.start()
        replay_manager.stop()
    else:
        live_service.stop()
        
    return {"status": "success", "mode": APP_MODE}

@router.get("/replay/status", response_model=ReplayStateResponse)
def replay_status():
    return ReplayStateResponse(
        status=replay_manager.status,
        speed=replay_manager.speed,
        processed_count=replay_manager.processed_count,
        total_count=replay_manager.total_count
    )

@router.post("/replay/start")
async def replay_start(speed: float = 1.0):
    replay_manager.start(speed=speed)
    return {"status": "started", "speed": speed}

@router.post("/replay/pause")
async def replay_pause():
    replay_manager.pause()
    return {"status": "paused"}

@router.post("/replay/stop")
async def replay_stop():
    replay_manager.stop()
    return {"status": "stopped"}

@router.post("/replay/reset")
async def replay_reset():
    replay_manager.reset()
    return {"status": "reset"}

@router.get("/signals", response_model=list[APIRiskSignal])
def get_signals(limit: int = 50, db: Session = Depends(get_db)):
    signals = db.query(RiskSignal).order_by(RiskSignal.timestamp.desc()).limit(limit).all()
    results = []
    for s in signals:
        prov = s.ingest_mode if s.ingest_mode else "UNKNOWN"
        results.append(APIRiskSignal(
            signal_id=s.signal_id,
            document_id=s.document_id,
            timestamp=s.timestamp,
            source=s.source,
            source_type=s.source_type if s.source_type else "unknown",
            data_origin=s.data_origin if s.data_origin else "UNKNOWN",
            ingest_mode=s.ingest_mode if s.ingest_mode else "UNKNOWN",
            provenance=prov,
            headline=s.headline,
            text_excerpt=s.text_excerpt,
            primary_company=s.primary_company,
            scope=s.scope,
            sentiment_score=s.sentiment_score if s.sentiment_score else 0.0,
            sentiment_label=s.sentiment_label if s.sentiment_label else "neutral",
            event_type=s.event_type if s.event_type else "unknown",
            event_confidence=s.event_confidence if s.event_confidence else 0.0,
            direction=s.direction if s.direction else "neutral",
            impact_score=s.impact_score if s.impact_score else 0.0,
            risk_level=s.risk_level if s.risk_level else "Low",
            impact_reasoning=s.impact_reasoning if s.impact_reasoning else {},
            entities=[], # Not populated in basic DB schema json yet
            signal_confidence=s.signal_confidence if s.signal_confidence else 0.0,
            stress_eligible=s.stress_eligible
        ))
    return results

@router.get("/signals/{id}", response_model=APIRiskSignal)
def get_signal(id: str, db: Session = Depends(get_db)):
    s = db.query(RiskSignal).filter_by(signal_id=id).first()
    if not s:
        raise HTTPException(404, "Signal not found")
        
    prov = s.ingest_mode if s.ingest_mode else "UNKNOWN"
    return APIRiskSignal(
        signal_id=s.signal_id,
        document_id=s.document_id,
        timestamp=s.timestamp,
        source=s.source,
        source_type=s.source_type if s.source_type else "unknown",
        data_origin=s.data_origin if s.data_origin else "UNKNOWN",
        ingest_mode=s.ingest_mode if s.ingest_mode else "UNKNOWN",
        provenance=prov,
        headline=s.headline,
        text_excerpt=s.text_excerpt,
        primary_company=s.primary_company,
        scope=s.scope,
        sentiment_score=s.sentiment_score if s.sentiment_score else 0.0,
        sentiment_label=s.sentiment_label if s.sentiment_label else "neutral",
        event_type=s.event_type if s.event_type else "unknown",
        event_confidence=s.event_confidence if s.event_confidence else 0.0,
        direction=s.direction if s.direction else "neutral",
        impact_score=s.impact_score if s.impact_score else 0.0,
        risk_level=s.risk_level if s.risk_level else "Low",
        impact_reasoning=s.impact_reasoning if s.impact_reasoning else {},
        entities=[],
        signal_confidence=s.signal_confidence if s.signal_confidence else 0.0,
        stress_eligible=s.stress_eligible
    )

@router.post("/analyze", response_model=APIRiskSignal)
def analyze_text(req: AnalyzeRequest, db: Session = Depends(get_db)):
    engine = RiskEngine(device="cpu")
    doc = RawDocument(
        document_id=str(uuid.uuid4()),
        source_id="manual-api",
        source_type=req.source,
        data_origin="MANUAL",
        ingest_mode=APP_MODE,
        headline=req.text,
        published_at=datetime.utcnow()
    )
    signal = engine.process(doc)
    
    # Save to DB
    from src.db.models import RiskSignal, Document
    db_doc = Document(
        document_id=doc.document_id,
        source_id=doc.source_id,
        published_at=doc.published_at,
        text=doc.headline,
        headline=doc.headline,
        ingest_mode="MANUAL"
    )
    db.add(db_doc)
    
    db_signal = RiskSignal(
        signal_id=signal.signal_id,
        document_id=signal.document_id,
        timestamp=signal.timestamp,
        source=signal.source,
        source_type=signal.source_type,
        ingest_mode="MANUAL",
        headline=signal.headline,
        primary_company=signal.primary_company,
        sentiment_score=signal.sentiment_score,
        sentiment_label=signal.sentiment_label,
        event_type=signal.event_type,
        event_confidence=signal.event_confidence,
        impact_score=signal.impact_score,
        risk_level=signal.risk_level,
        impact_reasoning=signal.impact_reasoning,
        stress_eligible=signal.stress_eligible
    )
    db.add(db_signal)
    db.commit()
    
    # Trigger Stress Engine if eligible
    from src.stress_engine.engine import StressEngine
    stress_engine = StressEngine(db_session=db)
    run_id = stress_engine.run_stress(signal, portfolio_id="synthetic-1", run_mode="manual")
    
    return APIRiskSignal(
        signal_id=signal.signal_id,
        document_id=signal.document_id,
        timestamp=signal.timestamp,
        source=signal.source,
        source_type=signal.source_type,
        data_origin=signal.data_origin,
        ingest_mode=signal.ingest_mode,
        provenance="MANUAL",
        headline=signal.headline,
        text_excerpt=signal.text_excerpt,
        primary_company=signal.primary_company,
        scope=signal.scope,
        sentiment_score=signal.sentiment_score,
        sentiment_label=signal.sentiment_label,
        event_type=signal.event_type,
        event_confidence=signal.event_confidence,
        direction=signal.direction,
        impact_score=signal.impact_score,
        risk_level=signal.risk_level,
        impact_reasoning=signal.impact_reasoning,
        entities=signal.entities,
        signal_confidence=signal.signal_confidence,
        stress_eligible=signal.stress_eligible,
        stress_run_id=run_id if run_id else None
    )

@router.get("/stress/runs", response_model=list[APIStressRun])
def get_stress_runs(limit: int = 10, db: Session = Depends(get_db)):
    runs = db.query(StressRun).order_by(StressRun.timestamp.desc()).limit(limit).all()
    return [
        APIStressRun(
            run_id=r.run_id,
            triggering_signal_id=r.trigger_signal_id,
            scenario=r.scenario_name,
            portfolio_value_before=r.portfolio_value_before,
            portfolio_value_after=r.portfolio_value_after,
            absolute_loss=r.absolute_loss,
            pct_loss=r.pct_loss,
            shocks_applied=r.shocks_applied if r.shocks_applied else {},
            run_mode=r.run_mode,
            timestamp=r.timestamp
        )
        for r in runs
    ]

@router.get("/stress/runs/{id}", response_model=APIStressRun)
def get_stress_run(id: str, db: Session = Depends(get_db)):
    r = db.query(StressRun).filter_by(run_id=id).first()
    if not r:
        raise HTTPException(404, "Stress run not found")
        
    return APIStressRun(
        run_id=r.run_id,
        triggering_signal_id=r.trigger_signal_id,
        scenario=r.scenario_name,
        portfolio_value_before=r.portfolio_value_before,
        portfolio_value_after=r.portfolio_value_after,
        absolute_loss=r.absolute_loss,
        pct_loss=r.pct_loss,
        shocks_applied=r.shocks_applied if r.shocks_applied else {},
        run_mode=r.run_mode,
        timestamp=r.timestamp
    )

@router.get("/dashboard/overview", response_model=DashboardOverviewResponse)
def dashboard_overview(db: Session = Depends(get_db)):
    signal_count = db.query(RiskSignal).count()
    stress_runs = db.query(StressRun).count()
    
    portfolio_val = 0
    portfolio = db.query(Portfolio).first()
    if portfolio:
        positions = db.query(PortfolioPosition).filter_by(portfolio_id=portfolio.portfolio_id).all()
        portfolio_val = sum([p.current_value for p in positions])
        
    # Severity aggregation
    severity_counts = {"High": 0, "Medium": 0, "Low": 0}
    signals = db.query(RiskSignal.risk_level).all()
    for s in signals:
        level = s[0] if s[0] else "Low"
        if level in severity_counts:
            severity_counts[level] += 1
        else:
            severity_counts[level] = 1

    return {
        "mode": APP_MODE,
        "total_signals": signal_count,
        "total_stress_runs": stress_runs,
        "portfolio_value": portfolio_val,
        "severity_counts": severity_counts
    }
