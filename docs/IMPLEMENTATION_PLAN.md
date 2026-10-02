# IMPLEMENTATION PLAN: RiskPulse

**Candidate Name:** Snehansh Khanna
**College:** VIT Vellore
**Email:** snehansh.khanna2023@vitstudent.ac.in
**Repo Name:** riskpulse
## 1. Environment Findings & Stack Validation
- **OS**: Windows 11 Home
- **Hardware**: CPU: Intel i7-14650HX (16 Cores, 24 Threads). RAM: 16 GB. GPU: NVIDIA GeForce RTX 4060 Laptop (8GB VRAM), CUDA 13.4. Disk: Sufficient space expected for SQLite and moderate Parquet processing.
- **Dependencies Installed**: Python 3.13.1, pip 26.0.1, uv 0.11.7, Node v25.9.0, npm 11.12.1, Git 2.51.0.
- **Missing / Conflicts**: Docker is *not available*. Python 3.13 is installed instead of 3.11. npm script execution via powershell is blocked by Execution Policies (must use `cmd` or update policy).
- **Stack Validation & Substitutions**:
  - **Database**: Because Docker is missing, we must use **SQLite** (fallback explicitly permitted) via the SQLAlchemy `DATABASE_URL` layer. 
  - **Python**: PyTorch and spaCy might have issues on 3.13.1 depending on exact native wheel availability. We will use `uv venv --python 3.11` to lock to Python 3.11 to match the recommended architecture.
  - **GPU**: 8GB VRAM is ample for `FinBERT` + `all-MiniLM-L6-v2` batched inference.

## 2. System Architecture
- **Dual-Mode Data Ingestion**: Live APIs (WSJ/SEC RSS feeds) & Replay Engine streaming from local curated datasets.
- **Unified NLP Risk Engine**: Consumes raw documents, standardizes schemas, extracts entities, and uses ML models + rules to classify events and compute Impact Scores. Output is standardized as a `RiskSignal`.
- **Database (SQLite)**: Stores `RiskSignal`s, portfolios, events, aggregations, and stress-test historical runs.
- **Module B (Stress Engine)**: Listens for high-impact (`>= 7`) signals, runs rules, and applies market shocks to a synthetic wholesale portfolio, outputting value deltas.
- **Backend**: FastAPI serving REST endpoints and managing background processing.
- **Frontend**: React 18 + Vite dashboard with 4 core views (Overview, Intelligence, Stress, Analytics).

## 3. Component Architecture
- `src/data_pipeline`: Scripts for offline batch reading, processing, deduplication, and saving as Parquet.
- `src/risk_engine`: Core NLP logic (spaCy NER, FinBERT, zero-shot/embedding-head Event Classification, Rule-based Impact Formula).
- `src/stress_engine`: Mathematical valuation of Loans, Bonds, Derivatives under shocks mapped from Event Types.
- `src/api`: FastAPI endpoints, Pydantic validation, SQLite sessions.
- `src/frontend`: Dashboard SPA.

## 4. Data Architecture
- `data/raw`: Git-ignored, stores large dataset downloads.
- `data/processed`: Parquet output from offline pipeline.
- `data/demo`: Curated small JSONL files representing episodes for Replay mode.
- **DB Flow**: In Replay/Live, processed signals are written to SQLite; dashboard reads only SQLite.

## 5. NLP Architecture
1. **Cleaning**: Normalize text, unescape HTML, basic language filter.
2. **Entities**: `spaCy (en_core_web_sm)` + string matching for tickers and aliases against a S&P 100 universe.
3. **Sentiment**: `ProsusAI/finbert` (GPU, batched) → `[-1, 1]`.
4. **Events**: Hybrid. We'll use `all-MiniLM-L6-v2` embeddings + `scikit-learn` LogisticRegression head on weak labels (if we map GDELT themes) OR zero-shot NLI for missing classes. We'll augment with keyword lexicons for fast routing.
5. **Impact**: Rule-based scoring (`E, S, M, K, R, V, X` components mapped to points) to produce explainable `1-10` score.

## 6. Database Schema (SQLite via SQLAlchemy)
- `sources`: Track ingestion sources.
- `documents`: Raw text, id, timestamps.
- `companies` / `counterparties`: Reference data.
- `events`: Event clusters.
- `risk_signals`: Main output, foreign keys to document and event.
- `portfolios` & `portfolio_positions`: Module B synthetic data.
- `stress_runs` & `stress_position_results`: Before/After MTMs and driver breakdowns.
- `agg_daily_*`: Rollup tables.

## 7. API Architecture
- `FastAPI` providing REST/JSON interfaces.
- Error handling: Custom envelope for 4xx/5xx.
- Notable endpoints: `/mode`, `/replay/start`, `/analyze` (playground), `/signals`, `/stress/auto-evaluate`.

## 8. Frontend Architecture
- **React 18 + Vite + TypeScript**. Styling with Tailwind CSS. Charts: Recharts.
- Views: 1. Executive Overview. 2. Risk Intelligence (Signals + Analyze). 3. Stress Testing (Waterfall + Breakdown). 4. Analytics.

## 9. Dataset Acquisition Strategy
| Candidate | Source | Purpose | Volume | Fit & Strategy |
| --- | --- | --- | --- | --- |
| **WSJ/SEC RSS Feeds** | Public | Primary Source (Live/Batch) | Moderate | Use RSS for LIVE mode. Download recent historical RSS feeds for BATCH. |
| **zeroshot/twitter-financial-news-topic** | Hugging Face | Evaluation & Social Source | ~21k | Use full dataset for model eval and mapping to taxonomy. Will serve as the Replay "social" feed. |
| **Synthetic Portfolio** | Generator | Module B Book | ~300 pos | Will build a python script to generate realistic loan/bond distributions linked to S&P 100 tickers. |
| **Demo Set** | Curated | Reproducible App | ~200 docs | Extracted from the primary/social processing pipeline, covering 3-4 specific scenarios. |

## 10. Dataset Preprocessing Strategy
- Processed via `Polars` (or PyArrow chunks). 
- Deduplication: Exact hash for identical headlines, MinHash/embeddings (SHOULD-tier) for near-dups.
- Offline pipeline runs sequentially: `Load -> Map schemas -> NLP pipeline -> Save Parquet -> Generate report`.
- Resumable state using index checkpoints.

## 11. Model Strategy
- **Sentiment**: `ProsusAI/finbert`. Fast, robust for finance. Requires 400MB disk, runs fast on RTX 4060.
- **Event Classification**: A transparent hybrid approach using `all-MiniLM-L6-v2` embeddings for taxonomy similarity, augmented with keyword/rule evidence and confidence scoring. We will not use a supervised LogisticRegression ML model unless a defensible training dataset can be mapped and evaluated. 
- **NER**: `en_core_web_sm` (spaCy). Fast rule-based + basic statistical NER.

## 12. Evaluation Strategy
- Sentiment against subset of PhraseBank (note FinBERT leakage).
- Events: We will establish if `twitter-financial-news-topic` labels support meaningful evaluation against our taxonomy.
- Track metrics using `scripts/evaluate_*.py`. Store results in `docs/results`. All reported metrics will come from actual executed runs; no fabricated placeholder results.

## 13. Portfolio / Stress-Testing Methodology
- 300 positions, $10B exposure. Synthetic wholesale-banking portfolio.
- **Valuation & Scenario Assumptions**: We explicitly model scenario-based stress estimates, not production bank valuations.
  - Position-level effects exposed: EAD, LGD, PD shift, duration, credit spread / CS01, DV01/PV01, delta, beta, scenario shock, before/after value, P&L/value delta, and contribution to total portfolio impact.
- **Triggers**: Signal Impact `>=7`, Adverse, specific classes.
- Shocks defined in `scenarios.yaml`.


## 14. Replay / Live Architecture
- `RiskEngine` is decoupled.
- `LIVE`: Background thread polling RSS every X minutes, saving to DB.
- `REPLAY`: Streams from `data/demo/` or `data/processed/`, simulating timestamps.
- Mode is a global state toggled via UI.

## 15. Testing Strategy
- Core logic: `pytest` with fixtures.
- Pipeline: Run `test_vertical_slice.py` on 20 hand-crafted documents.
- Financial Math: Validate bond pricing formulas and hedge offset signs manually in tests.

## 16. Deployment / Run Strategy
- Local-first python execution.
- Command flow: `uv venv --python 3.11`, `uv pip install -r requirements.txt`, `python scripts/download_models.py`, `python -m src.cli seed`, `npm run dev`, `uvicorn src.api.main:app`.

## 17. Risk Mitigation & Fallbacks
- GPU unavailable or memory exhaust: Fallback to CPU mode.
- WSJ/SEC RSS feeds block: Fallback to REPLAY exclusively.
- SQLite locks during concurrent writes: Set WAL mode in SQLAlchemy.

## 18. Performance Considerations
- Batched inference for FinBERT (`batch_size=16` or `32` for RTX 4060).
- SQLite indexed properly on `(timestamp, risk_level)`.

## 19. Exact Implementation Phases
- **Phase 1: Foundation & Architecture Setup**
- **Phase 2: Vertical Slice (Mandatory end-to-end on 20 docs)**
- **Phase 3: Data Acquisition & Offline Processing**
- **Phase 4: Module B (Stress Testing Engine)**
- **Phase 5: API & Dual-Mode Integration**
- **Phase 6: Frontend Dashboard**
- **Phase 7: Evaluation, Validation, & Polish**

## 20. Task Breakdown (See TASKS.md)

## 21. Dependencies
- Phase 1 must complete before Phase 2.
- Phase 2 (Vertical Slice) must be approved by passing tests before Phase 3 (Scaling).
- Phase 4 relies on Phase 2's RiskSignal definitions.

## 22. Acceptance Criteria for each Phase
- P1: Repo structured, env setup, SQLite functional.
- P2: 20 raw docs can pass through NLP and save to DB without error.
- P3: Validation milestone: Parquet output generated for >5000 docs. (Note: This is not an artificial limit; we will process larger practical datasets where useful using chunking/streaming without loading entirely into memory). Report generated.
- P4: Synthetic portfolio script works. Value delta calculation accurate and exposes position-level metrics.

- P5: API endpoints respond cleanly. LIVE/REPLAY toggle works.
- P6: React UI renders all 4 views. Data is sourced from API.
- P7: README complete, tests passing, metrics recorded.

## 23. Case-study vs Product vs Should/Nice Classification
- **MUST (A/B)**: SQLite, FastAPI, React, FinBERT, spaCy, Stress rules, Replay mode, 4 views.
- **SHOULD (C)**: Event-study priors, MinHash dedup, SSE feed.
- **NICE (C)**: Advanced clustering viz, auth.

## 24. Hackathon Deliverables Checklist
- [ ] Code repo public.
- [ ] README.md with template (clearly distinguishing data provenance).
- [ ] `docs/presentation.pdf`.
- [ ] `docs/architecture.png`.
- [ ] `/data` populated with demo sets.
- [ ] `docs/demo_script.md`.

## 25. Demo Scenarios & Presentation Outline
- **Data Provenance Distinction**: We clearly label and distinguish between LIVE GDELT data, downloaded historical/public data, curated REPLAY data, synthetic portfolio data, and generated stress scenarios. REPLAY will never be presented as LIVE.
- **Demo Scenario 1**: Replay geopolitical shock (e.g., Ukraine/Russia subset or similar macro event) -> Triggers widespread stress.
- **Demo Scenario 2**: Replay targeted credit event (e.g., specific firm downgrade) -> Triggers idiosyncratic stress.
- **Presentation**: Title -> Problem -> Architecture -> NLP Deep Dive -> Demo results -> Next Steps.


## 26. Assumptions
- SQLite WAL mode is performant enough for the scale of UI reading + batch writing we will do.
- Hugging Face datasets are accessible locally without auth tokens.

## 27. Open questions / decisions requiring my approval
- **Q1 (Python Version)**: System has Python 3.13.1. I propose using `uv` to create a virtualenv explicitly with Python 3.11 to ensure `torch`, `spacy` and `scikit-learn` stability (as requested in recommended stack). Approved?
- **Q2 (Docker/PostgreSQL)**: Docker is missing on the target host. According to Target-Architecture Preservation Rules, I propose falling back to SQLite via SQLAlchemy. Approved?
- **Q3 (Dataset Selection)**: I propose using `WSJ/SEC RSS feeds` for Live, and a slice of GDELT + `zeroshot/twitter-financial-news-topic` for Replay/Offline batching. Is this combination acceptable?
- **Q4 (Case Study Inconsistencies)**: 
  - **C1 (Demo Length)**: Designing core live flow to fit within <= 5 min.
  - **C3 (Dataset Size limit)**: Will keep large datasets git-ignored and only commit curated sample + demo.
  - **C4 (Transaction Data)**: Will generate synthetic portfolio.
  - **C5/C7 (Live/Real-time)**: Will rely on Replay mode for demo stability, Live mode for demonstration only.
- **Candidate Metadata**: I need the placeholder values for Candidate Name, College, Email, and Repo Name.
