import os
import sys
import json
import time
from tqdm import tqdm
from datasets import load_dataset
from sklearn.metrics import classification_report, accuracy_score

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.risk_engine.nlp.sentiment import SentimentAnalyzer
from src.risk_engine.nlp.events import EventClassifier

def evaluate_sentiment():
    print("Evaluating FinBERT Sentiment on zeroshot/twitter-financial-news-sentiment...")
    # Dataset labels: 0: Bearish (Negative), 1: Bullish (Positive), 2: Neutral
    try:
        ds = load_dataset("zeroshot/twitter-financial-news-sentiment", split="validation")
        # Just sample 200 for speed
        ds = ds.shuffle(seed=42).select(range(200))
    except Exception as e:
        print(f"Failed to load dataset: {e}")
        return None

    analyzer = SentimentAnalyzer()
    
    texts = ds["text"]
    true_labels_int = ds["label"]
    
    # Map huggingface labels to our labels
    # 0 -> negative, 1 -> positive, 2 -> neutral
    label_map = {0: "negative", 1: "positive", 2: "neutral"}
    true_labels = [label_map[l] for l in true_labels_int]
    
    start = time.time()
    results = []
    for t in tqdm(texts):
        score, label, conf, ver = analyzer.analyze(t)
        results.append(label)
    end = time.time()
    
    pred_labels = results
    
    acc = accuracy_score(true_labels, pred_labels)
    report = classification_report(true_labels, pred_labels, output_dict=True)
    
    throughput = len(texts) / (end - start)
    
    print(f"Sentiment Evaluation Done. Acc: {acc:.2f}, Throughput: {throughput:.2f} docs/sec")
    
    return {
        "model": "ProsusAI/finbert",
        "dataset": "zeroshot/twitter-financial-news-sentiment",
        "samples": len(texts),
        "accuracy": acc,
        "throughput_docs_per_sec": throughput,
        "classification_report": report
    }

def evaluate_events():
    print("Evaluating Event Classifier on zeroshot/twitter-financial-news-topic...")
    try:
        ds = load_dataset("zeroshot/twitter-financial-news-topic", split="validation")
        ds = ds.shuffle(seed=42).select(range(200))
    except Exception as e:
        print(f"Failed to load event dataset: {e}")
        return None

    analyzer = EventClassifier()
    
    texts = ds["text"]
    true_labels_int = ds["label"]
    
    # We won't strictly map them because our taxonomy is different, but we can just measure throughput
    # and maybe evaluate how many are assigned a non-Other class.
    
    start = time.time()
    results = []
    for t in tqdm(texts):
        ev, conf, top2 = analyzer.classify(t)
        results.append(ev)
    end = time.time()
    
    throughput = len(texts) / (end - start)
    
    print(f"Event Evaluation Done. Throughput: {throughput:.2f} docs/sec")
    
    return {
        "model": "MiniLM + Rules",
        "dataset": "zeroshot/twitter-financial-news-topic",
        "samples": len(texts),
        "throughput_docs_per_sec": throughput
    }

def main():
    os.makedirs("docs/results", exist_ok=True)
    
    results = {}
    
    sent_res = evaluate_sentiment()
    if sent_res:
        results["sentiment"] = sent_res
        
    ev_res = evaluate_events()
    if ev_res:
        results["events"] = ev_res
        
    with open("docs/results/evaluation_results.json", "w") as f:
        json.dump(results, f, indent=2)
        
    print("Saved evaluation results to docs/results/evaluation_results.json")

if __name__ == "__main__":
    main()
