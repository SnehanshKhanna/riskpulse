# RiskPulse API Documentation

RiskPulse exposes a FastAPI REST backend.

## Endpoints

### 1. `GET /api/v1/dashboard/overview`
Returns high-level KPIs for the dashboard.
- **Response Model**: `DashboardOverviewResponse`
- **Fields**:
  - `total_signals` (int)
  - `total_stress_runs` (int)
  - `portfolio_value` (float)
  - `mode` (str: "LIVE" or "REPLAY")
  - `severity_counts` (dict[str, int])

### 2. `GET /api/v1/signals`
Returns paginated risk signals.
- **Query Params**:
  - `skip` (int, default=0)
  - `limit` (int, default=100)
- **Response Model**: `List[APIRiskSignal]`

### 3. `GET /api/v1/signals/{signal_id}`
Returns a specific signal's full details, including impact reasoning.
- **Path Param**: `signal_id` (str)
- **Response Model**: `APIRiskSignal`

### 4. `POST /api/v1/analyze`
Submit custom text for manual risk analysis.
- **Request Body**: `AnalyzeRequest` (text)
- **Response Model**: `APIRiskSignal`

### 5. `GET /api/v1/stress/runs`
Returns the history of stress test runs and portfolio valuation changes.
- **Response Model**: `List[APIStressRun]`

### 6. `GET /api/v1/mode`
Check current LIVE/REPLAY mode and live availability.
- **Response Model**: `ModeResponse`

### 7. `POST /api/v1/mode`
Switch between LIVE and REPLAY modes.
- **Query Params**: `mode` (str: "LIVE" or "REPLAY")
- **Behavior**: If LIVE, starts the `LivePollingService` (RSS fetch) and stops the `ReplayEngine`. If REPLAY, stops `LivePollingService`.

### 8. `POST /api/v1/replay/start`, `/pause`, `/stop`, `/reset`
Control the REPLAY playback manually.

### 9. `GET /api/v1/replay/status`
Returns current replay engine state and progress (`processed_count` / `total_count`).
