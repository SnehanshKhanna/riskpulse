# Live Data Source Evaluation

This document details the investigation and evaluation of potential live data sources for the RiskPulse engine, according to the requirements for Phase 7 (Live Polling).

## Evaluation Criteria
- **Access**: Current API availability and restrictions.
- **Freshness**: Polling frequency and genuine real-time capabilities.
- **Text Availability**: Must provide sufficient text (title + snippet or body) for NLP models (FinBERT).
- **Financial Relevance**: Must contain financially relevant news and entities.
- **Rate Limits**: Ability to handle automated polling loops.
- **Terms**: Licensing restrictions on scraping or storing data.

## Source Comparison Matrix

| Source | Access | Freshness | Text Available | Financial Relevance | Rate Limits | Storage/Processing Terms | API Reliability | Suitable for LIVE? |
|--------|--------|-----------|----------------|--------------------|-------------|--------------------------|-----------------|--------------------|
| **NewsAPI** | PARTIAL (Needs Key) | PASS | PARTIAL (Truncated) | PASS | PARTIAL | PARTIAL | PASS | **FAIL** (No key provided) |
| **GDELT DOC API** | PASS (Free) | PASS | **FAIL** (No Body/Snippet) | PASS | **FAIL** (Aggressive 429s) | PASS | PARTIAL | **FAIL** (No text) |
| **Yahoo Finance RSS** | PASS (Open) | PASS | PASS | PASS | **FAIL** (Blocks scraping) | PARTIAL | PARTIAL | **FAIL** (Blocked) |
| **CNBC Finance RSS** | PASS (Open) | PASS | PASS | PASS | **FAIL** (503 VCL Failed) | PARTIAL | PARTIAL | **FAIL** (Blocked) |
| **WSJ Markets RSS** | PASS (Open) | PASS | PASS (164 chars) | PASS | PASS | PASS (Personal Use) | PASS | **PASS** |
| **SEC Press Releases**| PASS (Open) | PASS | PASS (250 chars) | PASS | PASS | PASS (Public Domain) | PASS | **PASS** |

### 1. NewsAPI
NewsAPI was specifically evaluated. While the API supports querying (`q="banking OR finance"`), the environment does not currently contain a `NEWSAPI_KEY`. Furthermore, the free tier of NewsAPI notoriously truncates the `content` field to a snippet ending with `[+1234 chars]`, which limits deeper NLP. Without a key, this source cannot be verifiably connected.

### 2. GDELT
GDELT 2.0 DOC API was re-evaluated. The API is accessible without a key but has aggressive rate limiting (`Please limit requests to one every 5 seconds or contact...`). Crucially, the DOC API does **not** provide the actual article text, only metadata and a URL. Passing only a title to the NLP pipeline provides poor signal quality, and scraping the URL directly violates terms and fails unpredictably. GDELT is technically unsuitable.

### 3. X / Twitter
X/Twitter provides no legitimate, free API access that supports automated polling for broad financial topics at this time. Scraping is explicitly prohibited. Evaluated and Rejected.

### 4. Publisher RSS (Primary Selected)
Various publisher feeds were tested via an automated probe.
- Yahoo Finance and CNBC actively blocked the python probe (`429 Edge` and `503 VCL`).
- **WSJ Markets** (`https://feeds.a.dj.com/rss/RSSMarketsMain.xml`) successfully returned 20 XML items containing a Title and a Description (~160 chars). 
- **SEC Press Releases** (`https://www.sec.gov/news/pressreleases.rss`) successfully returned 25 XML items containing a Title and a Description (~250 chars). 
Since the RiskPulse NLP pipeline (FinBERT) processes sentences and short snippets extremely well (max 512 tokens), this length is perfectly sufficient for sentiment and NER extraction.

## Conclusion & Implementation

**Primary Source Selected**: `RSSAdapter` utilizing **WSJ Markets** and **SEC Press Releases**.
**Fallback Source Selected**: None required, as RSS feeds act as their own redundant arrays.
**Verification**: True live connectivity was verified against the RSS feeds. A `LivePollingService` has been implemented that fetches these feeds asynchronously, deduplicates them against the database, and processes them through the `RiskEngine` and `StressEngine`.

**Result**: The application frontend can now truthfully display `LIVE: Available`.
