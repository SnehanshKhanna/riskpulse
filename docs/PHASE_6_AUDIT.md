# Phase 6 Forensic Audit & Reconciliation

A comprehensive read-only audit was performed on the Phase 6 application stack (Database → FastAPI → React). The findings, root causes, and applied fixes are documented below, culminating in a final reconciliation table.

## 1. Findings and Fixes

### 1.1 Portfolio Value ($7,372,056,732)
**Finding:** The dashboard displayed exactly `$7,372,056,732`. 
**Reconciliation:** The database `PortfolioPosition` table contains exactly 300 wholesale synthetic positions. A `SELECT SUM(current_value)` across these positions evaluates to `7372056731.750005`. The backend returns this raw float, and the React UI utilizes `toLocaleString(undefined, { maximumFractionDigits: 0 })` which cleanly rounds the float to `7,372,056,732`. 
**Fix:** The behavior is correct and mathematically precise. It correctly represents the aggregated MTM (Mark-to-Market) value of the wholesale positions. No fix required.

### 1.2 Stress Loss Percentage (-0.00%)
**Finding:** The dashboard displayed a stress loss of `$28,529,945` alongside `(-0.00%)`.
**Root Cause:** The database accurately persists `pct_loss = 0.00387001` (representing 0.387%). The API relays this raw float. In `App.tsx`, the UI was rendering `{run.pct_loss.toFixed(2)}%`. Because `0.00387.toFixed(2)` is `0.00`, the percentage was masked.
**Fix:** Updated `App.tsx` to explicitly cast and scale: `{Number(run.pct_loss * 100).toFixed(2)}%`. It now displays `-0.39%`.

### 1.3 Severity Char / Counts mismatch
**Finding:** The top dashboard KPI stated `High Severity = 2 (recent)` while the Pie Chart showed only Low/Medium and didn't map severity colors correctly.
**Root Cause:** The severity counts were being built locally in the React frontend by aggregating only the 20 most recent signals retrieved by `/signals?limit=20`. If those 20 happened to not contain High, the pie chart was skewed. Additionally, Recharts was assigning colors indexically, not mapped by severity name.
**Fix:** 
1. Added global `severity_counts` aggregation inside FastAPI (`src/api/routes.py` `dashboard/overview` endpoint) calculating over the full database. 
2. Updated `App.tsx` to read `overview.severity_counts` and strictly map colors (`High`: red, `Medium`: orange, `Low`: blue).

### 1.4 Signal Count (636 vs 205)
**Finding:** The total signal count rendered as `636`, but the Replay JSON dataset has only `205` lines.
**Root Cause:** The DB holds `430` signals ingested via Phase 3's `batch_runner.py` (marked `ingest_mode='BATCH'`) and `206` signals ingested via `replay_manager` (marked `ingest_mode='REPLAY'`). The API simply runs a total `COUNT(*)` across `RiskSignal`. Replay state machine `Reset` deliberately resets the pointer back to `0/205` but intentionally avoids destroying historical RiskSignals, thus preserving a cumulative audit log of all simulations.
**Fix:** No code fix required. The persistence semantics explicitly append to the log to retain historical risk tracking.

### 1.5 Provenance Overwriting
**Finding:** The FastAPI masking logic unconditionally masked any `ingest_mode` that wasn't `LIVE` as `REPLAY`. This meant `MANUAL` (via `/analyze`) was being obscured.
**Fix:** Updated `routes.py` to: `if prov not in ["LIVE", "MANUAL"]: prov = "REPLAY"`. Now, distinct provenance types are maintained.

### 1.6 Timestamps
**Finding:** The timestamps displayed (e.g. 9:28 PM) represented the moment the `replay_manager` processed the record and simulated its ingestion `datetime.utcnow()`, rather than the original publication date.
**Fix:** Updated the UI label in the Signal Details modal from `Timestamp` to `Ingested At (Simulated)` to remain transparent.

### 1.7 UI Labels
**Finding:** The dashboard title was "Live Risk Signals", misleading users since LIVE mode is unavailable.
**Fix:** Renamed the panel to "Recent Risk Signals".

---

## 2. Final Reconciliation Table

| Metric | Database / Backend Value | API Response Value | React Displayed Value | Status |
| --- | --- | --- | --- | --- |
| **Total Signals** | `636` | `636` | `636` | **VERIFIED** |
| **Portfolio Value** | `7,372,056,731.75` | `7372056731.750005` | `$7,372,056,732` | **VERIFIED** |
| **Stress Runs** | `1` | `1` | `1` | **VERIFIED** |
| **Stress Absolute Loss**| `28,529,945.30` | `28529945.30` | `-$28,529,945` | **VERIFIED** |
| **Stress Pct Loss** | `0.0038700` | `0.0038700` | `-0.39%` | **FIXED** (was -0.00%) |
| **Replay Progress** | DB lines = `205` | `total_count: 205` | `205 / 205` | **VERIFIED** |
| **Severity (High)** | DB count = `235` (across 636) | `severity_counts: {High: 235, ...}` | `235 (total)` | **FIXED** (was local 2) |
| **Provenance** | `MANUAL` / `REPLAY` | `MANUAL` / `REPLAY` | Tags: `MANUAL` / `REPLAY` | **FIXED** (was forced Replay) |

All tests (`uv run pytest tests/integration/test_api.py -v`) were successfully rerun against the patched API logic and all passed cleanly. The frontend explicitly reflects backend reality.
