---
marp: true
theme: default
class: lead
paginate: true
backgroundColor: #f8f9fa
---

# RiskPulse
### AI-Powered Financial Risk Intelligence & Stress Testing
**Code to Connect: S&P Global and Crisil | Hackathon 2026**
**Candidate:** Snehansh Khanna
**College:** VIT Vellore

---

## 1. Problem & Approach

**The Challenge:**
Financial risk emerges from unstructured, real-time events. Manually tracking news, predicting its impact, and calculating immediate portfolio exposures is too slow.

**Our Approach:**
- **Unified NLP Engine**: Ingests unstructured financial news to extract entities, sentiment, and categorize events.
- **Explainable Impact Scoring**: A hybrid deterministic rule-based formula that measures severity.
- **Automated Stress Testing (Module B)**: High-impact events auto-trigger shocks against a synthetic wholesale-banking portfolio.
- **Dual-Mode Replay System**: A deterministic replay engine allows offline review of historical crises.

---

## 2. System Architecture

![Architecture](architecture.png)

- **Backend**: FastAPI + SQLite + SQLAlchemy
- **Data Pipeline**: Polars + PyArrow + Hugging Face
- **Frontend**: React 18 + Vite + Recharts
- **Models**: `ProsusAI/finbert`, `all-MiniLM-L6-v2`, `spaCy` NER

---

## 3. NLP Deep Dive & Explainability

We prioritize **accuracy and explainability**:
- **Entity Resolution**: spaCy NER matched with RapidFuzz aliases mapping to the S&P 100 universe.
- **Sentiment**: FinBERT classifies financial tone (Pos, Neg, Neu).
- **Event Classification**: `all-MiniLM` embeddings compare news against a 12-class taxonomy, augmented with lexical rules.
- **Explainable Impact**: 
  - `Impact = f(Severity, Sentiment, Market Relevance)`
  - *Example output*: "Impact 8.4 — Geopolitical event +2.5; strong negative sentiment +1.8; high market relevance +1.7"

---

## 4. Module B: Portfolio Stress Testing

**The Portfolio**:
A synthetic $7.3B wholesale-banking book containing Loans, Bonds, and Derivatives across major sectors.

**The Trigger**:
When the NLP engine scores an event as `High Severity` (Impact $\ge$ 7) and Adverse, a stress test triggers automatically.

**The Execution**:
Looks up predefined shocks (e.g. Geopolitical: Equities -12%, Rates -30bps) and recalculates the total portfolio MTM instantly.

---

## 5. Key Results & Validations

- **Dataset Used**: Evaluated on `zeroshot/twitter-financial-news-sentiment` and `topic` datasets, and integrated into the offline pipeline.
- **Performance**:
  - FinBERT Accuracy: ~66% (vs baseline mappings)
  - Inference Throughput: ~47 docs/sec (Sentiment), ~140 docs/sec (Events) on CPU.
- **End-to-End Reliability**: 100% deterministic Replay mode allows repeatable demonstrations without API rate limits.

---

## 6. Domain Impact & Next Steps

**Domain Impact**:
RiskPulse bridges the gap between qualitative news and quantitative risk management, providing risk officers with an actionable, instant view of idiosyncratic and macroeconomic shocks.

**Next Steps**:
- Introduce real-time streaming (Kafka/SSE).
- Calibrate shock priors using historical event-studies.
- Integrate Module A (Tactical Rebalancer) consuming the same generic Risk Signals.
