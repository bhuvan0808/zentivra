"""Core pipeline components for the AI research intelligence system.

This package implements the main processing pipeline:

  fetch -> extract -> preprocess -> summarize -> dedup -> rank

Components:
- fetcher: HTTP/RSS/Playwright URL fetching with retries and rate limiting
- extractor: Content extraction from HTML (trafilatura/BeautifulSoup) and feeds
- preprocessor: Text normalization and cleaning before AI extraction
- summarizer: LLM-powered content summarization and finding generation
- dedup: Deduplication via text similarity and optional semantic embeddings
- change_detector: Content diff detection between crawl cycles
- ranker: LLM-powered relevance ranking of findings
- rate_limiter: Request rate limiting per domain
- security: Password hashing with bcrypt
- valkey_client: Async Valkey/Redis client for session management
"""
