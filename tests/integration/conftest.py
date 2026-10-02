import os
import shutil
import pytest

# Set env BEFORE anything else is imported
DB_PATH = "c:/Users/Lenovo/Desktop/Projects/riskpulse/data/interim/riskpulse.db"
TEST_DB_PATH = "c:/Users/Lenovo/Desktop/Projects/riskpulse/data/interim/test_riskpulse.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

os.environ["DATABASE_URL"] = TEST_DATABASE_URL

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    # Copy the actual demo database so tests have a valid starting state (portfolio, batch signals, etc)
    if os.path.exists(DB_PATH):
        shutil.copy2(DB_PATH, TEST_DB_PATH)
    
    yield
    
    # Cleanup
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass
