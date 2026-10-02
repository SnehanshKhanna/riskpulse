import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch.nn.functional as F

class SentimentAnalyzer:
    def __init__(self, model_name: str = "ProsusAI/finbert", device: str = None):
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name).to(self.device)
        self.model.eval()
        
    def analyze(self, text: str):
        # FinBERT labels: positive, negative, neutral
        # Usually 0=positive, 1=negative, 2=neutral for FinBERT but let's map dynamically based on model config.
        # But ProsusAI/finbert uses: 0=positive, 1=negative, 2=neutral
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512).to(self.device)
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = F.softmax(outputs.logits, dim=-1).squeeze().tolist()
            
        # P(pos) - P(neg)
        pos_prob = probs[0]
        neg_prob = probs[1]
        neu_prob = probs[2]
        
        score = pos_prob - neg_prob
        
        if score >= 0.15:
            label = "positive"
        elif score <= -0.15:
            label = "negative"
        else:
            label = "neutral"
            
        confidence = max(probs)
        return score, label, confidence, "ProsusAI/finbert"
