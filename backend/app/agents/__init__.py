"""
Agent workers for intelligence gathering across multiple domains.

This package provides specialized agents that discover URLs, crawl content,
extract text, and produce structured findings. Each agent extends BaseAgent
and overrides discover_urls() and post_process_finding() for domain-specific
behavior.

Available agents:
    - CompetitorWatcher: Monitors competitor companies for strategic intelligence
    - ModelProviderWatcher: Tracks LLM provider announcements and model releases
    - ResearchScout: Discovers academic papers and research publications
    - HFBenchmarkTracker: Monitors HuggingFace benchmark leaderboards
"""
