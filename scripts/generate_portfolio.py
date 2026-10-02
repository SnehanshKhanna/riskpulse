import csv
import uuid
import random
from datetime import datetime

TICKERS = ["NVDA", "AAPL", "JPM", "MSFT", "XOM"]
SECTORS = ["Technology", "Technology", "Financials", "Technology", "Energy"]

def generate():
    portfolio_id = str(uuid.uuid4())
    positions = []
    
    # Generate 300 positions
    for i in range(300):
        pos_id = str(uuid.uuid4())
        
        # Pick asset class
        ac = random.choices(
            ["Corporate Bond", "Corporate Loan", "Equity", "Derivative"],
            weights=[0.4, 0.4, 0.1, 0.1]
        )[0]
        
        inst_type = "Standard"
        if ac == "Corporate Loan":
            inst_type = random.choice(["Fixed", "Floating"])
        elif ac == "Derivative":
            inst_type = random.choice(["IR Swap", "FX Forward", "CDS"])
        elif ac == "Corporate Bond":
            inst_type = "Fixed"
            
        ticker_idx = random.randint(0, len(TICKERS)-1)
        ticker = TICKERS[ticker_idx]
        sector = SECTORS[ticker_idx]
        obligor = f"{ticker} Entity"
        
        current_value = random.uniform(1e6, 50e6)
        notional = current_value * random.uniform(1.0, 1.2) if ac != "Derivative" else current_value * 10
        
        pos = {
            "position_id": pos_id,
            "portfolio_id": portfolio_id,
            "asset_class": ac,
            "instrument_type": inst_type,
            "obligor": obligor,
            "ticker": ticker,
            "sector": sector,
            "country": "US",
            "currency": "USD",
            "notional": round(notional, 2),
            "current_value": round(current_value, 2),
            "exposure": round(current_value if ac != "Derivative" else current_value * 1.5, 2),
            "rating_bucket": random.choice(["AAA", "AA", "A", "BBB", "BB", "B", "CCC"]),
            "maturity_years": round(random.uniform(1.0, 10.0), 2),
            "rate_type": inst_type if inst_type in ["Fixed", "Floating"] else "Fixed",
            "modified_duration": round(random.uniform(2.0, 8.0), 2) if ac in ["Corporate Bond", "Corporate Loan"] else 0.0,
            "convexity": round(random.uniform(0.1, 1.0), 2) if ac in ["Corporate Bond", "Corporate Loan"] else 0.0,
            "spread_duration": round(random.uniform(2.0, 8.0), 2) if ac in ["Corporate Bond", "Corporate Loan", "Derivative"] else 0.0,
            "dv01": round(random.uniform(100, 5000), 2) if inst_type == "IR Swap" else 0.0,
            "delta": round(random.uniform(0.1, 1.0), 2) if ac in ["Equity", "Derivative"] else 0.0,
            "beta": round(random.uniform(0.8, 1.5), 2) if ac == "Equity" else 0.0,
            "lgd": 0.45,
            "pd_base": round(random.uniform(0.001, 0.05), 4),
            "data_origin": "SYNTHETIC"
        }
        positions.append(pos)
        
    # We would write this to CSV in data/portfolio/synthetic_portfolio.csv
    # But for now, we just print the first one.
    import os
    os.makedirs("data/portfolio", exist_ok=True)
    with open("data/portfolio/synthetic_portfolio.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=positions[0].keys())
        writer.writeheader()
        for p in positions:
            writer.writerow(p)
            
    print(f"Generated 300 positions in data/portfolio/synthetic_portfolio.csv")

if __name__ == "__main__":
    generate()
