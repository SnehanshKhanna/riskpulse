import React, { useState, useEffect } from 'react';
import { 
  Play, Pause, Square, RotateCcw, Activity, AlertTriangle, 
  DollarSign, BarChart2, Radio, Database, Search, FileText 
} from 'lucide-react';
import { 
  Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts';
import * as api from './services/api';

const SEVERITY_COLORS: Record<string, string> = {
  'High': '#ef4444', 
  'Medium': '#f59e0b', 
  'Low': '#3b82f6'
};

function App() {
  const [mode, setMode] = useState<any>(null);
  const [overview, setOverview] = useState<any>(null);
  const [signals, setSignals] = useState<any[]>([]);
  const [stressRuns, setStressRuns] = useState<any[]>([]);
  const [replayState, setReplayState] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modals
  const [selectedSignal, setSelectedSignal] = useState<any>(null);
  const [selectedStressRun, setSelectedStressRun] = useState<any>(null);
  
  // Manual Analysis
  const [analyzeText, setAnalyzeText] = useState("");
  const [analyzing, setAnalyzing] = useState(false);

  const isRequestInFlight = React.useRef(false);

  const fetchData = async () => {
    if (isRequestInFlight.current) return;
    isRequestInFlight.current = true;
    try {
      const modeData = await api.getMode();
      setMode(modeData);
      
      const overviewData = await api.getDashboardOverview();
      setOverview(overviewData);
      
      const signalsData = await api.getSignals(20);
      setSignals(signalsData);
      
      const runsData = await api.getStressRuns(10);
      setStressRuns(runsData);
      
      const rStatus = await api.getReplayStatus();
      setReplayState(rStatus);
      
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch data from API. Is backend running?');
    } finally {
      setLoading(false);
      isRequestInFlight.current = false;
    }
  };

  useEffect(() => {
    fetchData(); // Initial fetch
  }, []);

  useEffect(() => {
    let intervalTime = null;

    if (mode?.current_mode === 'LIVE') {
      intervalTime = 5000; // 5 seconds for LIVE updates
    } else if (mode?.current_mode === 'REPLAY' && replayState?.status === 'running') {
      intervalTime = 2000; // Fast 2 second updates when replay is streaming
    }

    if (intervalTime !== null) {
      const interval = setInterval(fetchData, intervalTime);
      return () => clearInterval(interval);
    }
  }, [mode?.current_mode, replayState?.status]);

  const handleReplayAction = async (action: string) => {
    try {
      if (action === 'start') await api.replayStart(10.0);
      else if (action === 'pause') await api.replayPause();
      else if (action === 'stop') await api.replayStop();
      else if (action === 'reset') await api.replayReset();
      fetchData();
    } catch (err) {
      console.error("Replay action failed", err);
    }
  };

  const handleAnalyze = async () => {
    if (!analyzeText) return;
    setAnalyzing(true);
    try {
      const result = await api.analyzeText(analyzeText);
      setSelectedSignal(result);
      setAnalyzeText("");
      fetchData();
    } catch (err) {
      console.error(err);
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading && !overview) {
    return <div style={{ display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center' }}>
      <h2>Initializing RiskPulse...</h2>
    </div>;
  }

  if (error && !overview) {
    return <div style={{ padding: '2rem', color: 'var(--accent-red)' }}>
      <h2>Connection Error</h2>
      <p>{error}</p>
    </div>;
  }

  // Analytics Prep
  const severityDist = overview?.severity_counts || {};
  const pieData = Object.keys(severityDist).map(k => ({ name: k, value: severityDist[k] }));

  return (
    <div className="app-container">
      <header className="header">
        <div className="header-title">
          <Activity size={28} />
          RiskPulse
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div 
            className={`mode-badge ${mode?.current_mode === 'LIVE' ? 'mode-live' : 'mode-replay'}`}
            style={{ cursor: mode?.live_available ? 'pointer' : 'default' }}
            onClick={async () => {
              if (mode?.live_available) {
                const newMode = mode?.current_mode === 'LIVE' ? 'REPLAY' : 'LIVE';
                try {
                  await fetch(`http://127.0.0.1:8000/api/v1/mode?mode=${newMode}`, { method: 'POST' });
                  fetchData();
                } catch (e) {
                  console.error("Failed to toggle mode", e);
                }
              }
            }}
          >
            {mode?.current_mode || 'REPLAY'}
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            LIVE: {mode?.live_available ? 'Available (Click badge to toggle)' : 'Unavailable (Config)'}
          </span>
        </div>
      </header>

      <main className="main-content">
        <div className="dashboard-grid">
          <div className="stat-card">
            <div className="stat-title"><Radio size={16} style={{ display: 'inline', marginRight: '5px' }}/> Total Signals</div>
            <div className="stat-value">{overview?.total_signals || 0}</div>
          </div>
          <div className="stat-card">
            <div className="stat-title"><AlertTriangle size={16} style={{ display: 'inline', marginRight: '5px' }}/> High Severity</div>
            <div className="stat-value" style={{ color: 'var(--accent-red)' }}>
              {overview?.severity_counts?.High || 0} (total)
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-title"><Database size={16} style={{ display: 'inline', marginRight: '5px' }}/> Stress Runs</div>
            <div className="stat-value">{overview?.total_stress_runs || 0}</div>
          </div>
          <div className="stat-card">
            <div className="stat-title"><DollarSign size={16} style={{ display: 'inline', marginRight: '5px' }}/> Portfolio Value</div>
            <div className="stat-value">${(overview?.portfolio_value || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
          </div>
        </div>

        <div className="content-grid">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div className="panel">
              <div className="panel-header">
                <div className="panel-title">
                  <Play size={20} /> Replay Engine
                </div>
                <div className="controls-bar">
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginRight: '1rem' }}>
                    Status: <strong style={{ color: 'white' }}>{replayState?.status}</strong> ({replayState?.processed_count} / {replayState?.total_count})
                  </span>
                  <button className="btn" onClick={() => handleReplayAction('start')}><Play size={16}/> Start</button>
                  <button className="btn" onClick={() => handleReplayAction('pause')}><Pause size={16}/> Pause</button>
                  <button className="btn" onClick={() => handleReplayAction('stop')}><Square size={16}/> Stop</button>
                  <button className="btn" onClick={() => handleReplayAction('reset')}><RotateCcw size={16}/> Reset</button>
                </div>
              </div>
              <div style={{ height: '4px', background: 'var(--panel-border)', borderRadius: '2px', overflow: 'hidden' }}>
                <div style={{ 
                  width: `${replayState?.total_count ? (replayState.processed_count / replayState.total_count) * 100 : 0}%`, 
                  height: '100%', 
                  background: 'var(--accent-blue)',
                  transition: 'width 0.3s'
                }}></div>
              </div>
            </div>

            <div className="panel">
              <div className="panel-header">
                <div className="panel-title"><BarChart2 size={20} /> Risk Analytics (Recent)</div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div style={{ height: '250px' }}>
                  <h4 style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.5rem', textAlign: 'center' }}>Severity Distribution</h4>
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value">
                        {pieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={SEVERITY_COLORS[entry.name] || '#94a3b8'} />
                        ))}
                      </Pie>
                      <Tooltip contentStyle={{ background: '#0b0f19', border: '1px solid #1e293b' }} />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div>
                  <h4 style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>Recent Stress Losses</h4>
                  {stressRuns.length === 0 ? <p style={{ color: 'var(--text-muted)' }}>No stress runs yet.</p> : (
                    <div className="signal-list">
                      {stressRuns.slice(0, 3).map(run => (
                        <div key={run.run_id} className="signal-item" onClick={() => setSelectedStressRun(run)}>
                          <div className="signal-header">
                            <span>{new Date(run.timestamp).toLocaleTimeString()}</span>
                            <span className="tag tag-red">-{Number(run.pct_loss * 100).toFixed(2)}%</span>
                          </div>
                          <div className="signal-headline">{run.scenario} Shock</div>
                          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                            Loss: ${(run.absolute_loss).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="panel">
              <div className="panel-header">
                <div className="panel-title"><Search size={20} /> Manual Analysis</div>
              </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <input 
                  type="text" 
                  value={analyzeText}
                  onChange={(e) => setAnalyzeText(e.target.value)}
                  placeholder="Paste a headline or financial news text to analyze..." 
                  style={{ flex: 1, padding: '0.75rem', borderRadius: '6px', border: '1px solid var(--panel-border)', background: 'rgba(255,255,255,0.05)', color: 'white' }}
                />
                <button className="btn btn-primary" onClick={handleAnalyze} disabled={analyzing}>
                  {analyzing ? 'Analyzing...' : 'Analyze'}
                </button>
              </div>
            </div>
          </div>

          <div className="panel">
            <div className="panel-header">
              <div className="panel-title"><FileText size={20} /> Recent Risk Signals</div>
            </div>
            {signals.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '2rem 0' }}>Waiting for signals...</p>
            ) : (
              <div className="signal-list">
                {signals.map(signal => (
                  <div key={signal.signal_id} className="signal-item" onClick={() => setSelectedSignal(signal)}>
                    <div className="signal-header">
                      <span>{new Date(signal.timestamp).toLocaleTimeString()}</span>
                      <span>{signal.primary_company || 'MACRO'}</span>
                    </div>
                    <div className="signal-headline">{signal.headline}</div>
                    <div className="signal-footer">
                      <span className={`tag ${signal.sentiment_label === 'negative' ? 'tag-red' : signal.sentiment_label === 'positive' ? 'tag-green' : 'tag-blue'}`}>
                        {signal.sentiment_label.toUpperCase()}
                      </span>
                      <span className={`tag ${signal.impact_score >= 5.0 ? 'tag-orange' : 'tag-purple'}`}>
                        Impact: {signal.impact_score.toFixed(1)}
                      </span>
                      <span className="tag" style={{ border: '1px solid rgba(255,255,255,0.2)' }}>
                        {signal.provenance}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Modals */}
      {selectedSignal && (
        <div className="modal-overlay" onClick={() => setSelectedSignal(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <div className="panel-title">Risk Signal Details</div>
              <button className="btn" onClick={() => setSelectedSignal(null)}>Close</button>
            </div>
            <div className="modal-body">
              <h2 style={{ marginBottom: '1.5rem' }}>{selectedSignal.headline}</h2>
              
              <div className="detail-grid">
                <div className="detail-item">
                  <span className="detail-label">Provenance</span>
                  <span className="detail-value tag tag-purple" style={{ display: 'inline-block', width: 'fit-content' }}>{selectedSignal.provenance}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Source</span>
                  <span className="detail-value">{selectedSignal.source} ({selectedSignal.source_type})</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Ingested At (Simulated)</span>
                  <span className="detail-value">{new Date(selectedSignal.timestamp).toLocaleString()}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Company / Entity</span>
                  <span className="detail-value">{selectedSignal.primary_company || 'N/A'}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Event Type</span>
                  <span className="detail-value">{selectedSignal.event_type} (Conf: {(selectedSignal.event_confidence * 100).toFixed(0)}%)</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Sentiment</span>
                  <span className={`detail-value ${selectedSignal.sentiment_label === 'negative' ? 'tag-red' : ''}`}>{selectedSignal.sentiment_label.toUpperCase()} (Score: {selectedSignal.sentiment_score.toFixed(2)})</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Impact Score</span>
                  <span className="detail-value">{selectedSignal.impact_score.toFixed(2)} / 10</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Stress Trigger</span>
                  <span className="detail-value">{selectedSignal.stress_eligible ? 'YES' : 'NO'}</span>
                </div>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <span className="detail-label">Logic Trace & Reasoning</span>
              </div>
              <div className="reasoning-box">
                {JSON.stringify(selectedSignal.impact_reasoning, null, 2)}
              </div>
            </div>
          </div>
        </div>
      )}

      {selectedStressRun && (
        <div className="modal-overlay" onClick={() => setSelectedStressRun(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <div className="panel-title">Stress Test Results: {selectedStressRun.scenario}</div>
              <button className="btn" onClick={() => setSelectedStressRun(null)}>Close</button>
            </div>
            <div className="modal-body">
              <div className="detail-grid">
                <div className="detail-item">
                  <span className="detail-label">Run ID</span>
                  <span className="detail-value" style={{ fontSize: '0.8rem' }}>{selectedStressRun.run_id}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Timestamp</span>
                  <span className="detail-value">{new Date(selectedStressRun.timestamp).toLocaleString()}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Triggering Signal ID</span>
                  <span className="detail-value" style={{ fontSize: '0.8rem' }}>{selectedStressRun.triggering_signal_id || 'Manual'}</span>
                </div>
              </div>

              <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', padding: '1.5rem', borderRadius: '8px', marginBottom: '2rem', display: 'flex', justifyContent: 'space-between' }}>
                <div className="detail-item">
                  <span className="detail-label">Portfolio Before</span>
                  <span className="detail-value" style={{ fontSize: '1.5rem' }}>${selectedStressRun.portfolio_value_before.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Portfolio After</span>
                  <span className="detail-value" style={{ fontSize: '1.5rem' }}>${selectedStressRun.portfolio_value_after.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                </div>
                <div className="detail-item" style={{ textAlign: 'right' }}>
                  <span className="detail-label" style={{ color: '#fca5a5' }}>Total Loss</span>
                  <span className="detail-value" style={{ fontSize: '1.5rem', color: '#fca5a5' }}>
                    -${selectedStressRun.absolute_loss.toLocaleString(undefined, { maximumFractionDigits: 0 })} ({Number(selectedStressRun.pct_loss * 100).toFixed(2)}%)
                  </span>
                </div>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <span className="detail-label">Scenario Assumptions & Shocks Applied</span>
              </div>
              <div className="reasoning-box">
                {JSON.stringify(selectedStressRun.shocks_applied, null, 2)}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
