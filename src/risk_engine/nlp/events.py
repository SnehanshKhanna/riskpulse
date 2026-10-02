from sentence_transformers import SentenceTransformer, util
import torch
import json
import os

class EventClassifier:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", device: str = None):
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        self.model = SentenceTransformer(model_name, device=self.device)
        self.taxonomy = [
            "Geopolitical", "Macroeconomic", "Credit Event", "Market Shock", 
            "Regulatory/Legal", "Merger/Acquisition", "Earnings/Financial Performance", 
            "Product Launch", "Cyber/Operational Incident", "Commodity/Energy Shock", 
            "Leadership Change", "Other"
        ]
        
        # Descriptions to embed for similarity
        self.descriptions = [
            "geopolitical conflict war international relations military tension election",
            "macroeconomic inflation interest rates central bank monetary policy unemployment",
            "credit event default bankruptcy downgrade restructuring debt crisis",
            "market shock stock market crash high volatility flash crash selloff",
            "regulatory legal lawsuit fine SEC investigation antitrust legislation",
            "merger acquisition M&A buyout takeover joint venture",
            "earnings financial performance revenue profit loss guidance dividend",
            "product launch new product release software update innovation",
            "cyber operational incident hack data breach outage ransomware cyberattack",
            "commodity energy shock oil price surge gold natural gas supply disruption",
            "leadership change CEO resignation executive appointment new board member",
            "general news other normal company updates"
        ]
        
        # Precompute taxonomy embeddings
        self.taxonomy_embeddings = self.model.encode(self.descriptions, convert_to_tensor=True, device=self.device)
        
        self.keywords = {
            "Credit Event": ["default", "bankruptcy", "downgrade", "chapter 11", "insolvency"],
            "Merger/Acquisition": ["merger", "acquisition", "acquire", "buyout", "takeover"],
            "Earnings/Financial Performance": ["earnings", "eps", "revenue", "profit", "quarterly results"],
            "Cyber/Operational Incident": ["hack", "breach", "cyberattack", "ransomware", "outage"],
            "Leadership Change": ["ceo", "resigns", "steps down", "appointed", "new chief"]
        }

    def classify(self, text: str):
        # 1. Similarity with taxonomy
        text_emb = self.model.encode([text], convert_to_tensor=True, device=self.device)
        cos_scores = util.cos_sim(text_emb, self.taxonomy_embeddings)[0]
        
        # 2. Check keywords for strong priors
        text_lower = text.lower()
        keyword_boosts = torch.zeros(len(self.taxonomy), device=self.device)
        
        for i, category in enumerate(self.taxonomy):
            if category in self.keywords:
                for kw in self.keywords[category]:
                    if kw in text_lower:
                        keyword_boosts[i] += 0.3
                        break
                        
        final_scores = cos_scores + keyword_boosts
        
        top_results = torch.topk(final_scores, k=2)
        top1_idx = top_results.indices[0].item()
        top2_idx = top_results.indices[1].item()
        
        score_val = top_results.values[0].item()
        
        # Normalize a bit to represent confidence
        confidence = min(score_val, 1.0)
        
        event_type = self.taxonomy[top1_idx]
        event_top2 = self.taxonomy[top2_idx]
        
        if confidence < 0.25:
            event_type = "Other"
            
        return event_type, confidence, event_top2
