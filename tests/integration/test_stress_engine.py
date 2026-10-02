import pytest
import datetime
from sqlalchemy.orm import Session
from src.db.session import SessionLocal, engine, Base
from src.db.models import Portfolio, PortfolioPosition, StressRun, RiskSignal
from src.risk_engine.schemas import RiskSignalSchema
from src.stress_engine.engine import StressEngine

@pytest.fixture(scope="module")
def db_session():
    # Use the existing test database setup or actual DB
    # We'll just run this against the actual populated DB for integration test
    db = SessionLocal()
    yield db
    db.close()

def test_stress_engine_trigger_and_run(db_session):
    # Setup Stress Engine
    stress_engine = StressEngine(db_session=db_session)
    
    # 1. Create a mock systemic high-impact signal (e.g. Geopolitical)
    signal = RiskSignalSchema(
        signal_id="test-signal-1",
        document_id="doc-1",
        timestamp=datetime.datetime.utcnow(),
        processed_at=datetime.datetime.utcnow(),
        source="gdelt",
        source_type="news",
        data_origin="SYNTHETIC",
        ingest_mode="BATCH",
        headline="Massive geopolitical escalation disrupts global trade",
        sentiment_score=-0.8,
        sentiment_label="negative",
        sentiment_confidence=0.9,
        event_type="Geopolitical",
        event_confidence=0.95,
        direction="adverse",
        impact_score=8.5, # > 7.0 triggers TRIGGER_SYSTEMIC
        risk_level="High",
        impact_reasoning={},
        entities=[],
        companies={},
        signal_confidence=0.9,
        stress_eligible=True
    )
    
    # Check trigger logic
    action = stress_engine.check_trigger(signal)
    assert action == "TRIGGER_SYSTEMIC", f"Expected TRIGGER_SYSTEMIC, got {action}"
    
    # Run stress test against the synthetic portfolio
    portfolio_id = "synthetic-1" # This was seeded in Phase 1
    
    # Ensure portfolio exists
    portfolio_exists = db_session.query(Portfolio).filter_by(portfolio_id=portfolio_id).first()
    if not portfolio_exists:
        pytest.skip("Synthetic portfolio not found. Did you run src.db.seed?")
        
    run_id = stress_engine.run_stress(signal, portfolio_id=portfolio_id, run_mode="auto")
    
    assert run_id is not None, "Stress engine failed to return a run_id"
    
    # Validate the run output in DB
    run = db_session.query(StressRun).filter_by(run_id=run_id).first()
    assert run is not None
    assert run.trigger_signal_id == "test-signal-1"
    assert run.scenario_name == "Geopolitical"
    assert run.absolute_loss > 0, "Expected the adverse geopolitical scenario to generate a loss"
    assert run.portfolio_value_before > run.portfolio_value_after

    print(f"Stress test run successfully generated. Total Loss: ${run.absolute_loss:,.2f} ({run.pct_loss*100:.2f}%)")

if __name__ == "__main__":
    pytest.main([__file__, "-s"])
