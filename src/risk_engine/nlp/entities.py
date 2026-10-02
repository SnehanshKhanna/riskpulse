import spacy
from typing import List, Dict, Any, Tuple
from rapidfuzz import fuzz, process
from src.risk_engine.schemas import EntityMatch

class EntityExtractor:
    def __init__(self, spacy_model: str = "en_core_web_sm"):
        self.nlp = spacy.load(spacy_model)
        # In a real scenario, this would load from a universe CSV.
        self.universe: Dict[str, Dict[str, Any]] = {
            "NVDA": {"name": "NVIDIA Corp", "aliases": ["Nvidia", "NVIDIA"]},
            "AAPL": {"name": "Apple Inc.", "aliases": ["Apple"]},
            "JPM": {"name": "JPMorgan Chase", "aliases": ["JPM", "J.P. Morgan"]},
            "MSFT": {"name": "Microsoft Corp", "aliases": ["Microsoft"]},
            "XOM": {"name": "Exxon Mobil", "aliases": ["Exxon"]}
        }
    
    def _find_company_by_name(self, text: str) -> Tuple[str, str, float]:
        """Returns (ticker, match_type, confidence) or (None, '', 0)"""
        # Exact alias match
        for ticker, data in self.universe.items():
            if text.lower() == data["name"].lower() or text.lower() in [a.lower() for a in data["aliases"]]:
                return ticker, "alias", 1.0
        
        # Fuzzy match
        choices = []
        for ticker, data in self.universe.items():
            choices.append(data["name"])
            choices.extend(data["aliases"])
        
        # We need to map back to ticker
        ticker_map = {}
        for ticker, data in self.universe.items():
            ticker_map[data["name"]] = ticker
            for alias in data["aliases"]:
                ticker_map[alias] = ticker
                
        if not choices:
            return None, "", 0.0
            
        best = process.extractOne(text, choices, scorer=fuzz.WRatio)
        if best and best[1] >= 90:
            return ticker_map[best[0]], "fuzzy", best[1] / 100.0
            
        return None, "", 0.0

    def extract(self, text: str, native_ticker_hint: str = None) -> Tuple[List[EntityMatch], Dict[str, float], str, str]:
        doc = self.nlp(text)
        entities = []
        companies = {}
        
        for ent in doc.ents:
            if ent.label_ in ["ORG", "GPE", "PERSON", "MONEY"]:
                ticker, match_type, confidence = None, "ner-only", 0.4
                if ent.label_ == "ORG":
                    ticker, match_type, confidence = self._find_company_by_name(ent.text)
                    if ticker:
                        companies[ticker] = companies.get(ticker, 0) + confidence
                
                entities.append(EntityMatch(
                    text=ent.text,
                    type=ent.label_,
                    ticker=ticker,
                    match_type=match_type,
                    confidence=confidence
                ))
        
        # Incorporate native_ticker_hint if provided
        if native_ticker_hint and native_ticker_hint in self.universe:
            companies[native_ticker_hint] = companies.get(native_ticker_hint, 0) + 0.95
            
        primary_company = None
        if companies:
            primary_company = max(companies.items(), key=lambda x: x[1])[0]
            
        scope = "company" if primary_company else "market"
            
        return entities, companies, primary_company, scope
