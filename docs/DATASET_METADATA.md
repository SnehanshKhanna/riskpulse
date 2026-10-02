# Dataset Metadata

This document catalogs the exact datasets utilized during data acquisition and offline processing (Phase 3), serving as the provenance record for our Replay mode and analytics pipeline.

## 1. Hugging Face Twitter Financial News Sentiment

- **Source:** Hugging Face Datasets
- **URL / Identifier:** `zeroshot/twitter-financial-news-sentiment`
- **Acquisition Date:** 2026-10-01
- **Dataset Version / Date:** default train split (0000.parquet)
- **License / Provenance:** MIT License. Scraped and curated financial news tweets.
- **Original Schema:** 
  - `text` (string): The financial tweet / news headline.
  - `label` (int64): 0, 1, 2 representing sentiment (Bearish, Bullish, Neutral).
- **Pipeline Role:** CURATED-REPLAY
- **Preprocessing Steps:** 
  - Fetched incrementally via PyArrow `iter_batches` directly from Parquet.
  - Passed through `dedup.py` (MinHash with 64 permutations, Jaccard threshold 0.85) which flagged ~14% of records as exact or near-duplicates.
  - Pushed through the `RiskEngine` (Entities, Sentiment, Events, Impact).
  - High-impact or stress-eligible records (Impact >= 5.0) were routed to `data/demo/replay_dataset.jsonl`.
  - Processed records (Documents + Signals) were committed to the local SQLite database.

## 2. GDELT 2.0 (Attempted and Evaluated)
- **Source:** GDELT DOC API / Event Export
- **Notes:** GDELT was evaluated. The tested GDELT acquisition path was rate-limited and did not provide the raw text required by the NLP pipeline. GDELT was therefore not used for the current text-processing/replay dataset. The Hugging Face financial-news dataset is the actual current data source. We do not claim that the current system is processing GDELT data.
