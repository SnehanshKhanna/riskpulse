# RiskPulse Architecture

RiskPulse is designed as a modular monolith. It ingests unstructured text and produces structured financial risk signals, feeding them into a portfolio stress-testing engine.

## Core Components

### 1. Data Pipeline & Ingestion
- **Offline Batch Processing**: Uses Polars/PyArrow to process large datasets (e.g. Hugging Face datasets) into Parquet formats.
- **LIVE Polling Engine**: A `LivePollingService` utilizing an `RSSAdapter` (WSJ/SEC) runs as an `asyncio` background task to pull live XML feeds, deduplicate them, and push them into the RiskEngine natively.
- **REPLAY Engine**: A BackgroundTask thread that simulates real-time data streaming by playing back curated historical processed signals from SQLite.

### 2. Risk Engine (`src/risk_engine/`)
The core NLP pipeline that normalizes documents into `RiskSignal`s.
- **Entities**: Extracts ORG/GPE/PERSON via spaCy NER and RapidFuzz alias matching.
- **Sentiment**: Runs `ProsusAI/finbert` to classify financial sentiment (positive, negative, neutral) with confidence scores.
- **Event Classifier**: Uses `all-MiniLM-L6-v2` embeddings matched against a defined taxonomy, augmented with regex keyword boosts.
- **Impact Scorer**: A hybrid rule-based scorer that combines event severity, sentiment magnitude, market relevance, and reliability into an explainable 1-10 `impact_score`.

### 3. Stress Engine (`src/stress_engine/`)
Module B implementation.
- Evaluates `RiskSignal`s against trigger conditions (e.g., Impact > 7, Adverse Direction).
- Looks up shock vectors from `data/config/scenarios.yaml`.
- Applies shifts (Equity pct drop, Rate bps shifts, Credit spread shifts) against a synthetic wholesale banking portfolio containing Loans, Bonds, and Derivatives.
- Calculates delta MTM for the total portfolio and records a `StressRun`.

### 4. API & Backend (`src/api/`)
- Built with **FastAPI**.
- State is managed in a local **SQLite** database via **SQLAlchemy**.
- Defines standard REST endpoints for the frontend to consume.
- Handles dual-mode (LIVE/REPLAY) multiplexing.

### 5. Frontend (`src/frontend/`)
- Built with **React 18**, **Vite**, and **TypeScript**.
- Styled with **Tailwind CSS**.
- Charts rendered with **Recharts**.
- Divided into logical views: Dashboard Overview, Intelligence (Signal Feed), Stress Testing, and Analytics.

## Data Storage
- **SQL Database**: Stores documents, signals, manual tests, and stress runs.
- **Parquet/JSONL**: Offline processed data and demo configurations.
