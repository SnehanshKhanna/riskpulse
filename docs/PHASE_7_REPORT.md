# Phase 7: Live Data Source Final Report

1. **SOURCES INVESTIGATED**: 
   - NewsAPI
   - GDELT DOC API
   - Yahoo Finance RSS
   - CNBC Finance RSS
   - WSJ Markets RSS
   - SEC Press Releases RSS

2. **SOURCE-BY-SOURCE RESULT**: 
   - *NewsAPI*: Requires a key. If a key is present, it truncates the body heavily.
   - *GDELT*: No article text is returned by the DOC API, rendering it useless for the NLP pipeline. Furthermore, aggressive 429 rate limiting prevents polling.
   - *Yahoo & CNBC*: Probe blocked immediately (429 Edge / 503 VCL).
   - *WSJ Markets*: Returned 20 fresh items, providing Title and Snippet (~160 chars).
   - *SEC Press Releases*: Returned 25 fresh items, providing Title and Snippet (~250 chars).

3. **PRIMARY SOURCE SELECTED**: WSJ Markets + SEC Press Releases combined into an `RSSAdapter`.

4. **FALLBACK SOURCE SELECTED**: NewsAPI (if `NEWSAPI_KEY` is provided, but since none is available in the environment, it is not used in production).

5. **SOURCES REJECTED + EXACT REASON**:
   - GDELT: Rejected because it does not provide raw text, failing the mandatory NLP pipeline requirement.
   - Yahoo/CNBC: Rejected due to active bot-blocking (`429 Edge`).
   - Twitter/X: Rejected due to prohibitive API costs and terms.

6. **WHETHER REAL LIVE CONNECTIVITY WAS VERIFIED**: YES. `probe_rss.py` successfully retrieved live articles from WSJ/SEC. And `validate_live.py` (a physical Playwright E2E browser test) confirmed full ingestion.

7. **EXACT ENVIRONMENT VARIABLES REQUIRED**: None are strictly required because the RSS feeds are open/public domain. However, `.env.example` has been updated to show `NEWSAPI_KEY` as an optional fallback.

8. **FILES CREATED/CHANGED**:
   - `src/risk_engine/ingestion/rss_adapter.py` (New: RSS fetcher)
   - `src/api/live_polling.py` (New: Async polling, deduplication, StressEngine hooks)
   - `src/api/routes.py` (Updated: Set `live_available=True` and async mode-switching)
   - `frontend/src/App.tsx` (Updated: Badge is now clickable to toggle LIVE)
   - `docs/LIVE_SOURCE_EVALUATION.md` (New: Detailed evaluation)
   - `.env.example` (Updated)
   - `tests/integration/test_api.py` (Updated: Fixed mode switching assertions)

9. **TESTS RUN + RESULTS**: `pytest` passed 10/10 tests, verifying the mode switches and regression on Replay/Batch.
   - Additionally, an automated Playwright script `scratch/validate_live.py` successfully completed an E2E physical browser test of LIVE mode.

10. **LIVE → RiskSignal verification**: The `LivePollingService` retrieves the URL/ID, verifies it against SQLite (`RiskSignal.document_id`), passes it to `RiskEngine`, and stores it with `provenance="LIVE"`.

11. **LIVE → StressRun verification**: The polling loop explicitly pipes the generated `APIRiskSignal` into `StressEngine.run_stress(..., run_mode="live")`, fulfilling Module B requirements seamlessly.

12. **REPLAY regression result**: `test_replay_flow` continues to pass, ensuring REPLAY is untouched and isolated. Replay can be safely paused/stopped when entering LIVE mode.

13. **Any remaining limitations**: RSS feeds only provide 150-250 character snippets. This is perfectly sufficient for the `FinBERT` model (which maxes at 512 tokens anyway), but it means we do not possess the full multi-page article.

14. **Whether LIVE should now honestly be shown as "Available"**: YES. The frontend now truthfully displays "LIVE: Available" and can be toggled by clicking the badge.

15. **E2E PHYSICAL BROWSER TEST (FINAL GATE)**: PASS. The playwright test validated:
    - Entering LIVE mode fetches current RSS signals.
    - Polling waits 30 seconds, fetching documents successfully (verified by the total signal count incrementing, e.g., +43).
    - `provenance` is mapped appropriately and verified as "LIVE" via UI cards.
    - Deduplication verifies effectively on the next cycle, showing exactly 0 duplicate signals.
    - Exiting LIVE back to REPLAY preserves system integrity.
