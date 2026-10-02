import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.db.models import Base, Source, Company

# Use in-memory SQLite for testing DB creation
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()

def test_db_create_and_insert(db_session):
    # Insert a source
    new_source = Source(id="test_gdelt", name="GDELT", type="news")
    db_session.add(new_source)
    
    # Insert a company
    new_company = Company(ticker="NVDA", name="NVIDIA Corp", sector="Technology", industry="Semiconductors", systemic_importance=0.9)
    db_session.add(new_company)
    
    db_session.commit()
    
    # Query back
    source = db_session.query(Source).filter_by(id="test_gdelt").first()
    assert source is not None
    assert source.name == "GDELT"
    
    company = db_session.query(Company).filter_by(ticker="NVDA").first()
    assert company is not None
    assert company.systemic_importance == 0.9
