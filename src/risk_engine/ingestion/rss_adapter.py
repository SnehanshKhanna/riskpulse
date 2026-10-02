import httpx
import xml.etree.ElementTree as ET
from datetime import datetime
from src.risk_engine.schemas import RawDocument

class RSSAdapter:
    """
    Legitimate publisher RSS feed adapter.
    Fetches XML feeds and extracts title + description.
    """
    def __init__(self, feed_urls: list[str]):
        self.feed_urls = feed_urls
        self.headers = {
            "User-Agent": "RiskPulse/1.0 (Research/Academic Project)"
        }

    async def fetch_recent(self) -> list[RawDocument]:
        documents = []
        async with httpx.AsyncClient(timeout=10.0, headers=self.headers) as client:
            for url in self.feed_urls:
                try:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        root = ET.fromstring(resp.text)
                        for item in root.findall(".//item"):
                            title = item.findtext("title") or ""
                            desc = item.findtext("description") or ""
                            link = item.findtext("link") or ""
                            pubDate = item.findtext("pubDate") or datetime.utcnow().isoformat()
                            
                            # Clean up CDATA and HTML simple tags if necessary, but we'll let NLP pipeline handle simple text
                            text_content = f"{title}. {desc}"
                            
                            doc = RawDocument(
                                document_id=link, # Use canonical URL as ID for deduplication
                                headline=title,
                                text=desc,
                                source_id="RSS",
                                source_type="news",
                                data_origin="PUBLIC-REAL",
                                ingest_mode="LIVE",
                                published_at=datetime.utcnow(),
                                url=link,
                                source_meta={"title": title, "link": link}
                            )
                            documents.append(doc)
                except Exception as e:
                    print(f"Error fetching RSS {url}: {e}")
        return documents
