import csv
import os
from sqlalchemy.orm import Session
from src.db.session import engine, Base, SessionLocal
from src.db.models import Source, Company, Portfolio, PortfolioPosition

def seed_db():
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    
    # 1. Sources
    if db.query(Source).count() == 0:
        db.add_all([
            Source(id="gdelt", name="GDELT DOC API", type="news"),
            Source(id="twitter-financial-news", name="HuggingFace Twitter Financial", type="social")
        ])
        
    # 2. Companies (Universe)
    if db.query(Company).count() == 0:
        db.add_all([
            Company(ticker="NVDA", name="NVIDIA Corp", sector="Technology", industry="Semiconductors", systemic_importance=0.9),
            Company(ticker="AAPL", name="Apple Inc.", sector="Technology", industry="Consumer Electronics", systemic_importance=0.95),
            Company(ticker="JPM", name="JPMorgan Chase", sector="Financials", industry="Banks", systemic_importance=0.95),
            Company(ticker="MSFT", name="Microsoft Corp", sector="Technology", industry="Software", systemic_importance=0.95),
            Company(ticker="XOM", name="Exxon Mobil", sector="Energy", industry="Oil & Gas", systemic_importance=0.85)
        ])
        
    # 3. Portfolio
    if db.query(Portfolio).count() == 0:
        portfolio = Portfolio(portfolio_id="synthetic-1", name="Wholesale Banking Book", description="Synthetic portfolio")
        db.add(portfolio)
        db.commit() # Commit so we can add positions
        
        # Check if we generated the portfolio CSV
        portfolio_file = "data/portfolio/synthetic_portfolio.csv"
        if os.path.exists(portfolio_file):
            with open(portfolio_file, "r") as f:
                reader = csv.DictReader(f)
                positions = []
                for row in reader:
                    positions.append(PortfolioPosition(
                        position_id=row["position_id"],
                        portfolio_id="synthetic-1",
                        asset_class=row["asset_class"],
                        instrument_type=row["instrument_type"],
                        obligor=row["obligor"],
                        ticker=row["ticker"],
                        sector=row["sector"],
                        country=row["country"],
                        currency=row["currency"],
                        notional=float(row["notional"]),
                        current_value=float(row["current_value"]),
                        exposure=float(row["exposure"]),
                        rating_bucket=row["rating_bucket"],
                        maturity_years=float(row["maturity_years"]),
                        rate_type=row["rate_type"],
                        modified_duration=float(row["modified_duration"]),
                        convexity=float(row["convexity"]),
                        spread_duration=float(row["spread_duration"]),
                        dv01=float(row["dv01"]),
                        delta=float(row["delta"]),
                        beta=float(row["beta"]),
                        lgd=float(row["lgd"]),
                        pd_base=float(row["pd_base"]),
                        data_origin=row["data_origin"]
                    ))
                db.bulk_save_objects(positions)
                
    db.commit()
    db.close()
    print("Database seeded successfully.")

if __name__ == "__main__":
    seed_db()
