import os
import httpx
import zipfile
import io

DATA_DIR = "data/raw"

def fetch_gdelt_sample():
    # Fetch a single recent GDELT 2.0 export file as a sample
    url = "http://data.gdeltproject.org/events/20240101.export.CSV.zip"
    target_path = os.path.join(DATA_DIR, "gdelt_sample.csv")
    
    if os.path.exists(target_path):
        print("GDELT sample already exists.")
        return
        
    print(f"Downloading GDELT sample from {url}...")
    with httpx.Client() as client:
        response = client.get(url, timeout=30.0, follow_redirects=True)
        response.raise_for_status()
        
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            # GDELT zips usually contain one CSV file
            csv_filename = z.namelist()[0]
            with z.open(csv_filename) as zf, open(target_path, 'wb') as f:
                f.write(zf.read())
                
    print("GDELT sample downloaded.")

def fetch_hf_financial_news():
    # Use HF Datasets API to download parquet files directly without installing the datasets library
    # The zeroshot/twitter-financial-news-sentiment has a parquet export
    url = "https://huggingface.co/datasets/zeroshot/twitter-financial-news-sentiment/resolve/refs%2Fconvert%2Fparquet/default/train/0000.parquet"
    target_path = os.path.join(DATA_DIR, "hf_financial_news.parquet")
    
    if os.path.exists(target_path):
        print("HF Financial News sample already exists.")
        return
        
    print(f"Downloading HF Financial News sample from {url}...")
    with httpx.Client() as client:
        response = client.get(url, timeout=30.0, follow_redirects=True)
        response.raise_for_status()
        
        with open(target_path, 'wb') as f:
            f.write(response.content)
            
    print("HF Financial News sample downloaded.")

if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)
    fetch_gdelt_sample()
    fetch_hf_financial_news()
