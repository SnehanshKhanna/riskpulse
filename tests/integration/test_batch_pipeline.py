import os
import pytest
import sqlite3

DEMO_DATA_FILE = "data/demo/replay_dataset.jsonl"
DB_FILE = "data/interim/riskpulse.db"

def test_batch_pipeline_output():
    # 1. Check if demo dataset was created and contains records
    assert os.path.exists(DEMO_DATA_FILE), "Demo dataset JSONL not found"
    
    with open(DEMO_DATA_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) > 0, "Demo dataset is empty"
        
    # 2. Check if SQLite was populated with signals
    assert os.path.exists(DB_FILE), "SQLite DB not found"
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Check documents
    cursor.execute("SELECT count(*) FROM documents")
    doc_count = cursor.fetchone()[0]
    assert doc_count > 0, "No documents written to SQLite"
    
    # Check signals
    cursor.execute("SELECT count(*) FROM risk_signals")
    signal_count = cursor.fetchone()[0]
    assert signal_count > 0, "No signals written to SQLite"
    
    conn.close()

if __name__ == "__main__":
    pytest.main([__file__])
