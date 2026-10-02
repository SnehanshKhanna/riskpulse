import asyncio
import logging
from src.risk_engine.ingestion.rss_adapter import RSSAdapter
from src.risk_engine.engine import RiskEngine
from src.stress_engine.engine import StressEngine
from src.db.session import SessionLocal
from src.db.models import RiskSignal
from src.api.schemas import APIRiskSignal
import threading

logger = logging.getLogger(__name__)

class LivePollingService:
    def __init__(self, interval_seconds: int = 60):
        self.interval_seconds = interval_seconds
        self.is_running = False
        self._task = None
        self.adapter = RSSAdapter(feed_urls=[
            "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
            "https://www.sec.gov/news/pressreleases.rss"
        ])
        self.seen_document_ids = set()
        
    def start(self):
        if not self.is_running:
            self.is_running = True
            self._task = asyncio.create_task(self._poll_loop())
            logger.info("Live polling service started.")

    def stop(self):
        self.is_running = False
        if self._task:
            self._task.cancel()
            logger.info("Live polling service stopped.")
            
    async def _poll_loop(self):
        # We need to run sync DB operations in threads if necessary, 
        # but for simplicity we'll do them fast in the async loop or via run_in_executor
        while self.is_running:
            try:
                documents = await self.adapter.fetch_recent()
                new_docs = [d for d in documents if d.document_id not in self.seen_document_ids]
                
                if new_docs:
                    await asyncio.to_thread(self._process_documents, new_docs)
                    
                    for d in new_docs:
                        self.seen_document_ids.add(d.document_id)
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in live polling loop: {e}")
                
            await asyncio.sleep(self.interval_seconds)

    def _process_documents(self, documents):
        db = SessionLocal()
        try:
            risk_engine = RiskEngine()
            stress_engine = StressEngine(db_session=db)
            
            for doc in documents:
                # Pre-check if document already exists in DB (robust deduplication across restarts)
                exists = db.query(RiskSignal).filter(RiskSignal.document_id == doc.document_id).first()
                if exists:
                    continue
                    
                processed_signal = risk_engine.process(doc)
                
                # Create DB Model
                db_signal = RiskSignal(
                    signal_id=processed_signal.signal_id,
                    document_id=processed_signal.document_id,
                    timestamp=processed_signal.timestamp,
                    source=processed_signal.source,
                    source_type=processed_signal.source_type,
                    data_origin=processed_signal.data_origin,
                    ingest_mode=processed_signal.ingest_mode,
                    headline=processed_signal.headline,
                    text_excerpt=processed_signal.text_excerpt,
                    primary_company=processed_signal.primary_company,
                    scope=processed_signal.scope,
                    sentiment_score=processed_signal.sentiment_score,
                    sentiment_label=processed_signal.sentiment_label,
                    event_type=processed_signal.event_type,
                    event_confidence=processed_signal.event_confidence,
                    direction=processed_signal.direction,
                    impact_score=processed_signal.impact_score,
                    risk_level=processed_signal.risk_level,
                    impact_reasoning=processed_signal.impact_reasoning,
                    entities=[e.dict() for e in processed_signal.entities],
                    signal_confidence=processed_signal.signal_confidence,
                    stress_eligible=processed_signal.stress_eligible
                )
                db.add(db_signal)
                db.commit()
                
                # Pass to StressEngine if eligible
                # We use the APIRiskSignal schema for run_stress
                api_signal = APIRiskSignal(
                    signal_id=db_signal.signal_id,
                    document_id=db_signal.document_id,
                    timestamp=db_signal.timestamp,
                    source=db_signal.source,
                    source_type=db_signal.source_type,
                    data_origin=db_signal.data_origin,
                    ingest_mode=db_signal.ingest_mode,
                    provenance="LIVE",
                    headline=db_signal.headline,
                    text_excerpt=db_signal.text_excerpt,
                    primary_company=db_signal.primary_company,
                    scope=db_signal.scope,
                    sentiment_score=db_signal.sentiment_score,
                    sentiment_label=db_signal.sentiment_label,
                    event_type=db_signal.event_type,
                    event_confidence=db_signal.event_confidence,
                    direction=db_signal.direction,
                    impact_score=db_signal.impact_score,
                    risk_level=db_signal.risk_level,
                    impact_reasoning=db_signal.impact_reasoning,
                    entities=db_signal.entities,
                    signal_confidence=db_signal.signal_confidence,
                    stress_eligible=db_signal.stress_eligible
                )
                
                stress_engine.run_stress(api_signal, portfolio_id="synthetic-1", run_mode="live")
                
        except Exception as e:
            logger.error(f"Error processing live documents: {e}")
        finally:
            db.close()

live_service = LivePollingService(interval_seconds=30)
