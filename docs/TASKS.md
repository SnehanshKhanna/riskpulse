# TASKS

## Phase 1: Foundation & Architecture Setup
| ID | Status | Priority | Task | Expected Output | Acceptance Criteria | Dependencies |
| --- | --- | --- | --- | --- | --- | --- |
| P1.1 | DONE | MUST | Initialize project structure | Folder skeleton created | `src/`, `data/`, `docs/`, `scripts/` exist | None |
| P1.2 | DONE | MUST | Setup `uv` virtual environment | Python environment ready | `requirements.txt` installed via `uv pip install` | P1.1 |
| P1.3 | DONE | MUST | Setup SQLite Database | SQLAlchemy models and SQLite connection | DB file created with `Base.metadata.create_all` | P1.2 |


## Phase 2: Vertical Slice (Mandatory)
| ID | Status | Priority | Task | Expected Output | Acceptance Criteria | Dependencies |
| --- | --- | --- | --- | --- | --- | --- |
| P2.1 | DONE | MUST | Implement `RawDocument` schema | Pydantic models for Document and Signal | Pydantic validation works | P1.3 |
| P2.2 | DONE | MUST | Implement Entity & Sentiment | spaCy NER and FinBERT basic wrappers | Can process 1 string to entities and sentiment score | P2.1 |
| P2.3 | DONE | MUST | Implement Event Classification & Impact | MiniLM head and Rule-based formula | Classifies event and calculates `1-10` score | P2.2 |
| P2.4 | DONE | MUST | Build Vertical Slice Test | Pytest script processing 20 hardcoded docs | End-to-end pipeline works and saves to SQLite | P2.3 |

## Phase 3: Data Acquisition & Offline Processing
| ID | Status | Priority | Task | Expected Output | Acceptance Criteria | Dependencies |
| --- | --- | --- | --- | --- | --- | --- |
| P3.1 | DONE | MUST | Script `fetch_data.py` | Python script to download datasets | Downloads GDELT CSV slices and Hugging Face sample | P2.4 |
| P3.2 | DONE | MUST | Build Polars Batch Processor | `batch_runner.py` with chunking | Reads CSV, applies NLP, saves Parquet, generates report | P3.1 |
| P3.3 | DONE | SHOULD | Implement MinHash Deduplication | Deduplicated documents | Removes similar headlines from batch | P3.2 |
| P3.4 | DONE | MUST | Curate Demo Dataset | `build_demo_dataset.py` | Small JSONL extracted for Demo replay mode | P3.2 |

## Phase 4: Module B (Stress Testing Engine)
| ID | Status | Priority | Task | Expected Output | Acceptance Criteria | Dependencies |
| --- | --- | --- | --- | --- | --- | --- |
| P4.1 | DONE | MUST | Generate Synthetic Portfolio | `generate_portfolio.py` | Creates 300+ positions linked to S&P 100 tickers | P1.3 |
| P4.2 | DONE | MUST | Implement Valuation logic | `valuation.py` | Functions compute Delta, Duration, Spread impacts | P4.1 |
| P4.3 | DONE | MUST | Define Trigger Rules & Scenarios | YAML config | YAML loads successfully | P4.2 |
| P4.4 | DONE | MUST | Implement Stress Engine | `stress_engine.py` | Listens to RiskSignal, triggers run, saves `StressResult` | P4.3 |

## Phase 5: API & Dual-Mode Integration
| ID | Status | Priority | Task | Expected Output | Acceptance Criteria | Dependencies |
| --- | --- | --- | --- | --- | --- | --- |
| P5.1 | DONE | MUST | Implement FastAPI Endpoints | `/signals`, `/analyze`, `/stress/runs` | Returns JSON payload matching schemas | P4.4 |
| P5.2 | DONE | MUST | Implement LIVE adapter | Mode manager | Polls LIVE RSS feeds (WSJ/SEC) and saves to DB | P5.1 |
| P5.3 | DONE | MUST | Implement REPLAY engine | Replay background task | Streams demo dataset at variable speed | P5.1 |

## Frontend Dashboard
| ID | Status | Priority | Task | Expected Output | Acceptance Criteria | Dependencies |
| --- | --- | --- | --- | --- | --- | --- |
| P6.1 | DONE | MUST | Setup React Vite App | Frontend skeleton | Runs on port 5173 | P5.3 |
| P6.2 | DONE | MUST | Overview View | Executive KPIs and trend chart | Renders data from `/dashboard/overview` | P6.1 |
| P6.3 | DONE | MUST | Intelligence View | Signal Table + Drawer | Filters work, drawer shows impact reasoning | P6.1 |
| P6.4 | DONE | MUST | Stress Testing View | Trigger queue, waterfall charts | Displays before/after Portfolio value | P6.1 |
| P6.5 | DONE | MUST | Analytics View | Heatmaps and distributions | Fetches from `/analytics/` | P6.1 |

## Phase 7: Evaluation, Validation, & Polish
| ID | Status | Priority | Task | Expected Output | Acceptance Criteria | Dependencies |
| --- | --- | --- | --- | --- | --- | --- |
| P7.1 | DONE | MUST | Implement `evaluate_*.py` | Evaluation scripts | Outputs `evaluation_results` json/table | P3.2 |
| P7.2 | DONE | MUST | Write Documentation | `docs/api.md`, `architecture.md` | Files are detailed and accurate | P6.5 |
| P7.3 | DONE | MUST | Presentation & README | `presentation.pdf`, `README.md` | Prepared for Hackathon submission | P7.2 |
