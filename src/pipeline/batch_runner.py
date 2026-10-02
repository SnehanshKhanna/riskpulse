import os
import uuid
import pyarrow.parquet as pq
import json
from datetime import datetime
from sqlalchemy.orm import Session
from src.db.session import engine, SessionLocal
from src.db.models import Document, RiskSignal, Event
from src.risk_engine.engine import RiskEngine
from src.risk_engine.schemas import RawDocument
from src.pipeline.dedup import Deduplicator
from tqdm import tqdm

DATA_FILE = "data/raw/hf_financial_news.parquet"
DEMO_DATA_FILE = "data/demo/replay_dataset.jsonl"
BATCH_SIZE = 500

def process_batch():
    if not os.path.exists(DATA_FILE):
        print(f"Data file {DATA_FILE} not found. Please fetch data first.")
        return

    os.makedirs("data/demo", exist_ok=True)
    
    # Initialize Engine (Downloads models if not present)
    risk_engine = RiskEngine()
    deduplicator = Deduplicator(threshold=0.85)
    
    db: Session = SessionLocal()
    
    parquet_file = pq.ParquetFile(DATA_FILE)
    total_rows = parquet_file.metadata.num_rows
    print(f"Starting batch processing of {total_rows} records...")
    
    stats = {
        "processed": 0,
        "duplicates": 0,
        "high_impact": 0,
        "errors": 0
    }
    
    demo_file = open(DEMO_DATA_FILE, "w", encoding="utf-8")
    
    try:
        batch_count = 0
        for batch in parquet_file.iter_batches(batch_size=BATCH_SIZE):
            if batch_count >= 1:
                print("Validation limit reached (1 batch). Stopping early.")
                break
            batch_count += 1
            
            rows = batch.to_pylist()
            
            db_docs = []
            db_signals = []
            
            for row in rows:
                text = row.get("text", "")
                if not text:
                    continue
                    
                doc_id = str(uuid.uuid4())
                
                # 1. Deduplication
                if deduplicator.is_duplicate(doc_id, text):
                    stats["duplicates"] += 1
                    continue
                
                stats["processed"] += 1
                
                # 2. Build RawDocument
                doc = RawDocument(
                    document_id=doc_id,
                    source_id="twitter-financial-news",
                    source_type="social",
                    data_origin="CURATED-REPLAY",
                    ingest_mode="BATCH",
                    headline=text, # tweets are mostly just headlines
                    text=None,
                    published_at=datetime.utcnow()
                )
                
                # 3. Process via RiskEngine
                try:
                    signal = risk_engine.process(doc)
                    
                    # 4. Filter for DEMO dataset (only keep high impact/stress eligible for demo to keep it curated)
                    if signal.impact_score >= 5.0 or signal.stress_eligible:
                        stats["high_impact"] += 1
                        demo_file.write(signal.model_dump_json() + "\n")
                    
                    # 5. Prepare DB Models
                    db_docs.append(Document(
                        document_id=doc.document_id,
                        source_id=doc.source_id,
                        source_type=doc.source_type,
                        data_origin=doc.data_origin,
                        ingest_mode=doc.ingest_mode,
                        headline=doc.headline,
                        text=doc.text,
                        published_at=doc.published_at
                    ))
                    
                    db_signals.append(RiskSignal(
                        signal_id=signal.signal_id,
                        document_id=signal.document_id,
                        timestamp=signal.timestamp,
                        source=signal.source,
                        source_type=signal.source_type,
                        data_origin=signal.data_origin,
                        ingest_mode=signal.ingest_mode,
                        headline=signal.headline,
                        primary_company=signal.primary_company,
                        scope=signal.scope,
                        sentiment_score=signal.sentiment_score,
                        sentiment_label=signal.sentiment_label,
                        sentiment_confidence=signal.sentiment_confidence,
                        event_type=signal.event_type,
                        event_confidence=signal.event_confidence,
                        direction=signal.direction,
                        impact_score=signal.impact_score,
                        risk_level=signal.risk_level,
                        impact_reasoning=signal.impact_reasoning,
                        stress_eligible=signal.stress_eligible
                    ))
                    
                except Exception as e:
                    print(f"Error processing document {doc_id}: {e}")
                    stats["errors"] += 1
            
            # Save chunk to DB
            if db_docs:
                db.bulk_save_objects(db_docs)
            if db_signals:
                db.bulk_save_objects(db_signals)
            db.commit()
            
            print(f"Processed batch. Stats so far: {stats}")
            
    finally:
        demo_file.close()
        db.close()
        
    print("\n--- BATCH PROCESSING COMPLETE ---")
    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    process_batch()
