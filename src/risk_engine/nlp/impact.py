from typing import Dict, Any, List

class ImpactCalculator:
    def __init__(self):
        self.severity_prior = {
            "Credit Event": 0.80,
            "Geopolitical": 0.75,
            "Market Shock": 0.75,
            "Macroeconomic": 0.65,
            "Cyber/Operational Incident": 0.60,
            "Commodity/Energy Shock": 0.60,
            "Regulatory/Legal": 0.55,
            "Merger/Acquisition": 0.50,
            "Earnings/Financial Performance": 0.45,
            "Leadership Change": 0.30,
            "Product Launch": 0.25,
            "Other": 0.10
        }
        
        self.amplifiers = ["invasion", "collapse", "emergency", "sanctions", "crisis"]
        self.mitigators = ["reportedly", "may", "denies", "eases", "rumor"]
        
    def calculate(
        self,
        event_type: str,
        sentiment_score: float,
        scope: str,
        systemic_importance: float,
        corroboration_count: int,
        source_type: str,
        text: str,
        entity_confidence: float,
        sentiment_confidence: float,
        event_confidence: float
    ) -> Dict[str, Any]:
        
        text_lower = text.lower()
        
        # 1. E: Event severity
        base_e = self.severity_prior.get(event_type, 0.10)
        intensity_modifier = 0.0
        for amp in self.amplifiers:
            if amp in text_lower:
                intensity_modifier += 0.1
        for mit in self.mitigators:
            if mit in text_lower:
                intensity_modifier -= 0.1
        e_val = max(0.0, min(1.0, base_e + intensity_modifier))
        
        # 2. S: Sentiment magnitude
        s_val = abs(sentiment_score)
        
        # 3. M: Market relevance
        if scope == "company":
            m_val = systemic_importance
        elif scope == "sector":
            m_val = 0.65
        elif scope == "market":
            m_val = 0.80
        else:
            m_val = 0.40
            
        # 4. K: Corroboration
        k_val = min(1.0, (corroboration_count - 1) / 4.0)
        
        # 5. R: Source reliability
        if source_type == "news":
            r_val = 0.90
        elif source_type == "social":
            r_val = 0.45
        else:
            r_val = 0.75
            
        # 6. V and X
        v_val = 0.50
        x_val = 0.50
        
        # Weights
        w_e, w_s, w_m, w_k, w_r, w_v, w_x = 0.30, 0.15, 0.15, 0.15, 0.10, 0.10, 0.05
        raw = (w_e*e_val + w_s*s_val + w_m*m_val + w_k*k_val + w_r*r_val + w_v*v_val + w_x*x_val)
        
        # Confidence
        signal_confidence = (entity_confidence * sentiment_confidence * event_confidence) ** (1/3)
        confidence_factor = 0.70 + 0.30 * signal_confidence
        
        impact_raw = max(0.0, min(1.0, raw * confidence_factor))
        impact_score = round(1 + 9 * impact_raw, 1)
        
        # Risk level
        if impact_score < 4:
            risk_level = "Low"
        elif impact_score < 7:
            risk_level = "Medium"
        elif impact_score < 8.5:
            risk_level = "High"
        else:
            risk_level = "Critical"
            
        reasoning = {
            "formula": "E(0.3) + S(0.15) + M(0.15) + K(0.15) + R(0.1) + V(0.1) + X(0.05)",
            "components": [
                {"name": "Event", "value": round(e_val, 2), "weight": w_e, "points": round(9 * w_e * e_val * confidence_factor, 2)},
                {"name": "Sentiment", "value": round(s_val, 2), "weight": w_s, "points": round(9 * w_s * s_val * confidence_factor, 2)},
                {"name": "Market", "value": round(m_val, 2), "weight": w_m, "points": round(9 * w_m * m_val * confidence_factor, 2)}
            ],
            "signal_confidence": round(signal_confidence, 2)
        }
        
        return {
            "impact_score": impact_score,
            "risk_level": risk_level,
            "impact_reasoning": reasoning,
            "signal_confidence": signal_confidence,
            "stress_eligible": event_type in ["Geopolitical", "Macroeconomic", "Credit Event", "Market Shock", "Cyber/Operational Incident", "Commodity/Energy Shock"]
        }
