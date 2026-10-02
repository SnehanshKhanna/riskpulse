import uuid
from datetime import datetime
from src.risk_engine.schemas import RawDocument, RiskSignalSchema
from src.risk_engine.nlp.entities import EntityExtractor
from src.risk_engine.nlp.sentiment import SentimentAnalyzer
from src.risk_engine.nlp.events import EventClassifier
from src.risk_engine.nlp.impact import ImpactCalculator

class RiskEngine:
    def __init__(self, device: str = None):
        self.entity_extractor = EntityExtractor()
        self.sentiment_analyzer = SentimentAnalyzer(device=device)
        self.event_classifier = EventClassifier(device=device)
        self.impact_calculator = ImpactCalculator()
        
    def process(self, doc: RawDocument) -> RiskSignalSchema:
        text_to_analyze = doc.headline
        if doc.text:
            text_to_analyze = f"{doc.headline}. {doc.text}"
            
        # 1. Entities
        entities, companies, primary_company, scope = self.entity_extractor.extract(
            text_to_analyze, doc.native_ticker_hint
        )
        entity_conf = max([e.confidence for e in entities]) if entities else 0.5
        
        # 2. Sentiment
        sentiment_score, sentiment_label, sentiment_conf, sent_model = self.sentiment_analyzer.analyze(text_to_analyze)
        
        direction = "neutral"
        if sentiment_label == "positive": direction = "favourable"
        elif sentiment_label == "negative": direction = "adverse"
        
        # 3. Events
        event_type, event_conf, event_top2 = self.event_classifier.classify(text_to_analyze)
        
        # 4. Impact
        sys_imp = 0.5
        if primary_company in ["JPM", "AAPL", "MSFT"]:
            sys_imp = 0.95
        elif primary_company in ["NVDA", "XOM"]:
            sys_imp = 0.85
            
        impact_result = self.impact_calculator.calculate(
            event_type=event_type,
            sentiment_score=sentiment_score,
            scope=scope,
            systemic_importance=sys_imp,
            corroboration_count=1,
            source_type=doc.source_type,
            text=text_to_analyze,
            entity_confidence=entity_conf,
            sentiment_confidence=sentiment_conf,
            event_confidence=event_conf
        )
        
        # 5. Build RiskSignalSchema
        signal_id = str(uuid.uuid4())
        
        return RiskSignalSchema(
            signal_id=signal_id,
            document_id=doc.document_id,
            timestamp=doc.published_at,
            processed_at=datetime.utcnow(),
            source=doc.source_id,
            source_type=doc.source_type,
            data_origin=doc.data_origin,
            ingest_mode=doc.ingest_mode,
            headline=doc.headline,
            text_excerpt=doc.text[:200] if doc.text else None,
            url=doc.url,
            primary_company=primary_company,
            scope=scope,
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            sentiment_confidence=sentiment_conf,
            event_type=event_type,
            event_confidence=event_conf,
            event_top2=event_top2,
            direction=direction,
            impact_score=impact_result["impact_score"],
            risk_level=impact_result["risk_level"],
            impact_reasoning=impact_result["impact_reasoning"],
            entities=entities,
            companies=companies,
            signal_confidence=impact_result["signal_confidence"],
            stress_eligible=impact_result["stress_eligible"],
            model_version={"sentiment": sent_model, "event": "all-MiniLM-L6-v2"}
        )
