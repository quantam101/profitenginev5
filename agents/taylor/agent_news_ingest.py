import asyncio
import time
import json
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import deque
import httpx
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsSource(Enum):
    """Supported news sources."""
    HACKERNEWS = "https://hacker-news.firebaseio.com/v0"
    TECHCRUNCH = "https://api.techcrunch.com"
    COINDESK = "https://api.coindesk.com/v1"
    ARXIV = "http://export.arxiv.org/api/query"
    NEWSAPI = "https://newsapi.org/v2"


@dataclass
class NewsArticle:
    """Represents a news article."""
    source: str
    title: str
    url: str
    timestamp: float
    category: str = "general"
    content: Optional[str] = None
    author: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class NewsQueue:
    """Thread-safe queue for articles."""

    def __init__(self, maxsize: int = 1000):
        self.queue: deque = deque(maxlen=maxsize)
        self.lock = asyncio.Lock()

    async def put(self, item: NewsArticle) -> None:
        """Add article to queue."""
        async with self.lock:
            self.queue.append(item)
            logger.info(f"Queued: {item.title[:50]}... from {item.source}")

    async def get(self) -> Optional[NewsArticle]:
        """Get article from queue (FIFO)."""
        async with self.lock:
            if self.queue:
                return self.queue.popleft()
            return None

    async def get_all(self) -> List[NewsArticle]:
        """Get and clear all articles."""
        async with self.lock:
            items = list(self.queue)
            self.queue.clear()
            return items

    async def size(self) -> int:
        """Get queue size."""
        async with self.lock:
            return len(self.queue)


class AgentNewsIngest:
    """Ingests news from multiple sources every 30 seconds."""

    FETCH_INTERVAL = 30  # seconds
    MAX_RETRIES = 3
    TIMEOUT = 10

    def __init__(self, api_keys: Optional[Dict[str, str]] = None):
        """Initialize news ingestion agent.

        Args:
            api_keys: Dictionary with optional API keys for sources requiring auth
                     Keys: 'newsapi', 'techcrunch', etc.
        """
        self.api_keys = api_keys or {}
        self.queue = NewsQueue()
        self.running = False
        self.last_fetch_times = {source.name: 0 for source in NewsSource}
        self.http_client = None
        self.fetch_count = 0
        self.error_count = 0
        self._init_time = time.time()

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self.http_client is None:
            self.http_client = httpx.AsyncClient(timeout=self.TIMEOUT)
        return self.http_client

    async def fetch(self) -> Dict[str, List[NewsArticle]]:
        """Fetch news from all sources concurrently.

        Returns:
            Dictionary mapping source names to lists of articles
        """
        logger.info(f"Starting fetch cycle #{self.fetch_count + 1}")
        results = {}

        tasks = [
            self._fetch_hackernews(),
            self._fetch_techcrunch(),
            self._fetch_coindesk(),
            self._fetch_arxiv(),
            self._fetch_newsapi(),
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for source_name, articles in zip(
            [s.name for s in NewsSource],
            responses
        ):
            if isinstance(articles, Exception):
                logger.error(f"{source_name} fetch failed: {articles}")
                self.error_count += 1
                results[source_name] = []
            else:
                results[source_name] = articles

        self.fetch_count += 1
        return results

    async def _fetch_hackernews(self) -> List[NewsArticle]:
        """Fetch from Hacker News top stories."""
        try:
            client = await self._get_client()
            # Get top 30 story IDs
            resp = await client.get(f"{NewsSource.HACKERNEWS.value}/topstories.json")
            story_ids = resp.json()[:30]

            articles = []
            for story_id in story_ids[:5]:  # Get details for top 5
                story_resp = await client.get(
                    f"{NewsSource.HACKERNEWS.value}/item/{story_id}.json"
                )
                story = story_resp.json()
                if story and story.get("title"):
                    articles.append(
                        NewsArticle(
                            source="hackernews",
                            title=story["title"],
                            url=story.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                            timestamp=story.get("time", time.time()),
                            category="tech",
                            author=story.get("by"),
                        )
                    )
            return articles
        except Exception as e:
            logger.error(f"HackerNews fetch error: {e}")
            return []

    async def _fetch_techcrunch(self) -> List[NewsArticle]:
        """Fetch from TechCrunch (mock - requires API key)."""
        try:
            # TechCrunch requires authentication - using mock data
            articles = [
                NewsArticle(
                    source="techcrunch",
                    title="AI Startup Raises $50M Series B",
                    url="https://techcrunch.com/example",
                    timestamp=time.time(),
                    category="startups",
                    author="TechCrunch"
                ),
                NewsArticle(
                    source="techcrunch",
                    title="SaaS Market Consolidation Accelerates",
                    url="https://techcrunch.com/example2",
                    timestamp=time.time() - 3600,
                    category="saas",
                    author="TechCrunch"
                ),
            ]
            return articles
        except Exception as e:
            logger.error(f"TechCrunch fetch error: {e}")
            return []

    async def _fetch_coindesk(self) -> List[NewsArticle]:
        """Fetch from CoinDesk cryptocurrency news."""
        try:
            client = await self._get_client()
            resp = await client.get(f"{NewsSource.COINDESK.value}/news")
            data = resp.json()

            articles = []
            for item in data.get("data", [])[:5]:
                articles.append(
                    NewsArticle(
                        source="coindesk",
                        title=item.get("title", "Crypto News"),
                        url=item.get("url", ""),
                        timestamp=time.time(),
                        category="crypto",
                        content=item.get("description"),
                    )
                )
            return articles
        except Exception as e:
            logger.error(f"CoinDesk fetch error: {e}")
            return []

    async def _fetch_arxiv(self) -> List[NewsArticle]:
        """Fetch from arXiv research papers."""
        try:
            client = await self._get_client()
            resp = await client.get(
                f"{NewsSource.ARXIV.value}?search_query=cat:cs.AI&start=0&max_results=5"
            )

            articles = []
            # Simple XML parsing for arXiv
            content = resp.text
            entries = content.split("<entry>")[1:]

            for i, entry in enumerate(entries[:5]):
                title_start = entry.find("<title>") + 7
                title_end = entry.find("</title>")
                title = entry[title_start:title_end] if title_start > 6 else f"Research Paper {i}"

                articles.append(
                    NewsArticle(
                        source="arxiv",
                        title=title,
                        url=f"https://arxiv.org/",
                        timestamp=time.time(),
                        category="research",
                    )
                )
            return articles
        except Exception as e:
            logger.error(f"arXiv fetch error: {e}")
            return []

    async def _fetch_newsapi(self) -> List[NewsArticle]:
        """Fetch from NewsAPI (requires API key)."""
        try:
            if "newsapi" not in self.api_keys:
                logger.warning("NewsAPI key not provided, skipping")
                return []

            client = await self._get_client()
            params = {
                "q": "technology",
                "sortBy": "publishedAt",
                "language": "en",
                "apiKey": self.api_keys["newsapi"],
            }
            resp = await client.get(f"{NewsSource.NEWSAPI.value}/everything", params=params)
            data = resp.json()

            articles = []
            for article in data.get("articles", [])[:5]:
                articles.append(
                    NewsArticle(
                        source="newsapi",
                        title=article.get("title", ""),
                        url=article.get("url", ""),
                        timestamp=datetime.fromisoformat(
                            article.get("publishedAt", "").replace("Z", "+00:00")
                        ).timestamp(),
                        category="general",
                        author=article.get("author"),
                        content=article.get("description"),
                    )
                )
            return articles
        except Exception as e:
            logger.error(f"NewsAPI fetch error: {e}")
            return []

    async def queue(self, articles: Dict[str, List[NewsArticle]]) -> int:
        """Queue articles from fetch results.

        Args:
            articles: Dictionary of source -> articles from fetch()

        Returns:
            Total number of articles queued
        """
        total = 0
        for source, article_list in articles.items():
            for article in article_list:
                await self.queue.put(article)
                total += 1

        logger.info(f"Queued {total} articles across all sources")
        return total

    async def ingest(self, duration: Optional[int] = None) -> None:
        """Main ingestion loop - fetch every 30 seconds.

        Args:
            duration: Optional duration in seconds to run. None = run indefinitely.
        """
        self.running = True
        start_time = time.time()

        logger.info(f"Starting news ingestion (interval: {self.FETCH_INTERVAL}s)")

        try:
            while self.running:
                if duration and (time.time() - start_time) > duration:
                    logger.info(f"Duration limit reached ({duration}s)")
                    break

                # Fetch from all sources
                articles = await self.fetch()

                # Queue all articles
                await self.queue(articles)

                queue_size = await self.queue.size()
                logger.info(
                    f"Cycle complete - Queue size: {queue_size}, "
                    f"Total fetches: {self.fetch_count}, Errors: {self.error_count}"
                )

                # Wait before next fetch
                await asyncio.sleep(self.FETCH_INTERVAL)

        except asyncio.CancelledError:
            logger.info("Ingestion cancelled")
        except Exception as e:
            logger.error(f"Ingestion error: {e}", exc_info=True)
        finally:
            self.running = False
            if self.http_client:
                await self.http_client.aclose()

    async def get_articles(self, count: Optional[int] = None) -> List[NewsArticle]:
        """Retrieve articles from queue.

        Args:
            count: Maximum articles to retrieve. None = get all

        Returns:
            List of articles
        """
        if count is None:
            return await self.queue.get_all()

        articles = []
        for _ in range(count):
            article = await self.queue.get()
            if article:
                articles.append(article)
            else:
                break

        return articles

    def stop(self) -> None:
        """Stop the ingestion loop."""
        self.running = False

    async def stats(self) -> Dict[str, Any]:
        """Get ingestion statistics."""
        return {
            "running": self.running,
            "fetch_count": self.fetch_count,
            "error_count": self.error_count,
            "queue_size": await self.queue.size(),
            "uptime_seconds": time.time() - self._init_time,
        }


if __name__ == "__main__":

    async def main():
        # Example usage
        ingestor = AgentNewsIngest(api_keys={"newsapi": "your-key-here"})

        # Run for 60 seconds with 30-second fetch interval
        ingest_task = asyncio.create_task(ingestor.ingest(duration=60))

        try:
            await ingest_task
        except KeyboardInterrupt:
            ingestor.stop()

        # Get all queued articles
        articles = await ingestor.get_articles()
        print(f"\nTotal articles collected: {len(articles)}")
        for article in articles[:5]:
            print(f"  - {article.title} ({article.source})")

        # Print stats
        stats = await ingestor.stats()
        print(f"\nStats: {json.dumps(stats, indent=2)}")

    asyncio.run(main())
