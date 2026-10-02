import asyncio
import json
import os
from datetime import datetime
from src.risk_engine.schemas import RiskSignalSchema
from src.db.session import SessionLocal
from src.stress_engine.engine import StressEngine
from src.db.models import RiskSignal as DBRiskSignal, Document as DBDocument

DEMO_FILE = "data/demo/replay_dataset.jsonl"

class ReplayEngineManager:
    def __init__(self):
        self.status = "stopped"
        self.speed = 1.0
        self.processed_count = 0
        self.total_count = 0
        self.data = []
        self._task = None
        self.load_data()

    def load_data(self):
        if not os.path.exists(DEMO_FILE):
            return
        with open(DEMO_FILE, "r", encoding="utf-8") as f:
            self.data = [json.loads(line) for line in f if line.strip()]
        self.total_count = len(self.data)

    async def _run_loop(self):
        while self.status == "running" and self.processed_count < self.total_count:
            record_dict = self.data[self.processed_count]
            # It's a dict representing a RiskSignalSchema, but wait, the file contains dumped RiskSignalSchema
            signal = RiskSignalSchema(**record_dict)
            
            # Persist and trigger stress
            db = SessionLocal()
            try:
                # We assume the document already exists if it came from batch, but in a true replay we might be re-evaluating.
                # Since demo is pre-processed, we just simulate the ingestion.
                # But wait, replay should technically stream raw and run NLP, or just stream pre-processed signals?
                # Prompt: "stream data/demo/replay_dataset.jsonl ... persist generated signals ... trigger Module B"
                # Since replay_dataset.jsonl already contains RiskSignal outputs (pre-processed by batch_runner), we just load them, 
                # assign a new timestamp to simulate live ingestion, save to DB, and trigger stress engine.
                
                # Simulate new timestamp
                signal.timestamp = datetime.utcnow()
                signal.processed_at = datetime.utcnow()
                
                # Check if signal exists to avoid unique constraint, or generate new ID
                # We'll just generate new ID to allow multiple replays
                import uuid
                new_id = str(uuid.uuid4())
                signal.signal_id = new_id
                
                db_sig = DBRiskSignal(
                    signal_id=signal.signal_id,
                    document_id=signal.document_id, # Doc ID can remain same, but might violate constraints if we replay multiple times
                    timestamp=signal.timestamp,
                    source=signal.source,
                    source_type=signal.source_type,
                    data_origin=signal.data_origin,
                    ingest_mode="REPLAY", # Explicit mode
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
                )
                db.add(db_sig)
                
                # Trigger Stress
                stress_engine = StressEngine(db_session=db)
                run_id = stress_engine.run_stress(signal, portfolio_id="synthetic-1", run_mode="auto")
                # stress_engine commits inside run_stress
                
                if not run_id:
                    db.commit()
            except Exception as e:
                print(f"Replay Error: {e}")
            finally:
                db.close()
                
            self.processed_count += 1
            
            # Configurable speed (base delay e.g. 2 seconds / speed)
            await asyncio.sleep(2.0 / self.speed)
            
        if self.processed_count >= self.total_count:
            self.status = "stopped"

    def start(self, speed: float = 1.0):
        self.speed = speed
        
        # If we are starting from a 'stopped' state (terminated session), we start fresh.
        # If we are starting from a 'paused' state, we resume from current cursor.
        if self.status == "stopped":
            self.processed_count = 0
            
        if self.status != "running":
            self.status = "running"
            if self.processed_count >= self.total_count:
                self.processed_count = 0
            self._task = asyncio.create_task(self._run_loop())

    def pause(self):
        self.status = "paused"

    def stop(self):
        self.status = "stopped"
        if self._task:
            self._task.cancel()

    def reset(self):
        self.stop()
        self.processed_count = 0

replay_manager = ReplayEngineManager()
