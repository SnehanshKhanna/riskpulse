import pytest
import datetime
from src.risk_engine.schemas import RawDocument
from src.risk_engine.engine import RiskEngine

# We will mark this with @pytest.mark.model so it can be skipped if models aren't downloaded
@pytest.mark.model
def test_vertical_slice_execution():
    # 1. Initialize Engine (this downloads/loads models if not present)
    engine = RiskEngine(device="cpu") # Force CPU for tests to avoid CUDA OOM issues in CI
    
    # 2. Create mock documents (covering Geopolitical, Credit Event, low-impact, etc.)
    docs = [
        RawDocument(
            document_id="doc-1",
            source_id="test_gdelt",
            source_type="news",
            data_origin="SYNTHETIC-TEST",
            ingest_mode="BATCH",
            headline="NVIDIA factory in Taiwan destroyed by massive earthquake",
            text="A massive earthquake hit Taiwan, severely impacting Nvidia's supply chain.",
            published_at=datetime.datetime.utcnow()
        ),
        RawDocument(
            document_id="doc-2",
            source_id="test_gdelt",
            source_type="news",
            data_origin="SYNTHETIC-TEST",
            ingest_mode="BATCH",
            headline="JPMorgan files for Chapter 11 bankruptcy following massive derivative losses",
            text="JPMorgan Chase defaults on its massive derivative portfolio. This is a severe collapse and crisis.",
            published_at=datetime.datetime.utcnow()
        ),
        RawDocument(
            document_id="doc-3",
            source_id="test_gdelt",
            source_type="news",
            data_origin="SYNTHETIC-TEST",
            ingest_mode="BATCH",
            headline="Apple announces new color for iPhone 15",
            text="The new iPhone will come in slightly darker blue.",
            published_at=datetime.datetime.utcnow()
        )
    ]
    
    signals = []
    
    # 3. Process documents
    for doc in docs:
        signal = engine.process(doc)
        signals.append(signal)
        
    # 4. Assertions on Doc 1 (Geopolitical / Operational)
    assert signals[0].primary_company == "NVDA"
    assert signals[0].sentiment_label == "negative"
    assert signals[0].direction == "adverse"
    assert signals[0].impact_score >= 5.0 # Should be high impact
    
    # Assertions on Doc 2 (Credit Event)
    assert signals[1].primary_company == "JPM"
    assert signals[1].event_type == "Credit Event"
    assert signals[1].impact_score >= 7.0 # High impact trigger
    assert signals[1].stress_eligible == True
    
    # Assertions on Doc 3 (Low impact product launch)
    assert signals[2].primary_company == "AAPL"
    assert signals[2].sentiment_label in ["positive", "neutral"]
    assert signals[2].impact_score < 4.0 # Low impact
    assert signals[2].stress_eligible == False

    print("Vertical slice test passed successfully!")
