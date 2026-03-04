"""Quick verification of Phase 3 agent workers."""
import sys
sys.path.insert(0, ".")


def test_agent_imports():
    """Test that all agents import and instantiate."""
    print("Testing agent imports...")

    from app.agents.base_agent import BaseAgent
    print("  ✅ BaseAgent imported")

    from app.agents.competitor_watcher import CompetitorWatcher
    agent1 = CompetitorWatcher()
    assert agent1.agent_type == "competitor"
    assert agent1.agent_name == "Competitor"
    print(f"  ✅ CompetitorWatcher: type={agent1.agent_type}")

    from app.agents.model_provider_watcher import ModelProviderWatcher
    agent2 = ModelProviderWatcher()
    assert agent2.agent_type == "model_provider"
    print(f"  ✅ ModelProviderWatcher: type={agent2.agent_type}")

    from app.agents.research_scout import ResearchScout
    agent3 = ResearchScout()
    assert agent3.agent_type == "research"
    print(f"  ✅ ResearchScout: type={agent3.agent_type}")

    from app.agents.hf_benchmark_tracker import HFBenchmarkTracker
    agent4 = HFBenchmarkTracker()
    assert agent4.agent_type == "hf_benchmark"
    print(f"  ✅ HFBenchmarkTracker: type={agent4.agent_type}")


def test_post_processing():
    """Test agent-specific post-processing."""
    import asyncio

    print("\nTesting post-processing...")

    # Test competitor watcher impact detection
    from app.agents.competitor_watcher import CompetitorWatcher
    watcher = CompetitorWatcher()

    finding = {
        "title": "OpenAI Launches GPT-5 with New Pricing",
        "summary_short": "GPT-5 is now generally available with lower API pricing",
        "confidence": 0.7,
        "tags": [],
        "entities": {},
    }

    class MockSource:
        name = "OpenAI"
        css_selectors = None
    
    class MockExtraction:
        text = "test"

    result = asyncio.run(watcher.post_process_finding(finding, MockExtraction(), MockSource()))
    assert result["confidence"] > 0.7, "Should boost confidence for high-impact keywords"
    assert "generally available" in result["tags"], "Should detect GA keyword"
    assert "OpenAI" in result["entities"]["companies"], "Should add company entity"
    print(f"  ✅ CompetitorWatcher: confidence boosted to {result['confidence']}, tags={result['tags'][:3]}")

    # Test model provider watcher model detection
    from app.agents.model_provider_watcher import ModelProviderWatcher
    provider = ModelProviderWatcher()

    finding2 = {
        "title": "Claude 3.5 Sonnet with 200K Context",
        "summary_long": "Anthropic released Claude 3.5 Sonnet with 200K context window and improved tool use",
        "confidence": 0.8,
        "tags": [],
        "entities": {},
        "category": "other",
    }

    result2 = asyncio.run(provider.post_process_finding(finding2, MockExtraction(), MockSource()))
    assert result2["category"] == "models", "Should categorize as models"
    print(f"  ✅ ModelProviderWatcher: category={result2['category']}, models={result2['entities'].get('models', [])}")

    # Test HF benchmark SOTA detection
    from app.agents.hf_benchmark_tracker import HFBenchmarkTracker
    tracker = HFBenchmarkTracker()

    finding3 = {
        "title": "Llama 3.1 70B achieves SOTA on MMLU benchmark",
        "summary_long": "Meta's Llama 3.1 70B outperforms GPT-4 on MMLU with 87.2% accuracy",
        "source_url": "https://huggingface.co/spaces/open-llm-leaderboard",
        "confidence": 0.7,
        "tags": [],
        "entities": {},
        "category": "other",
    }

    class MockHFSource:
        name = "Open LLM Leaderboard"
        css_selectors = None
        url = "https://huggingface.co/spaces/open-llm-leaderboard"

    result3 = asyncio.run(tracker.post_process_finding(finding3, MockExtraction(), MockHFSource()))
    assert "sota_claim" in result3["tags"], "Should detect SOTA claim"
    assert "MMLU" in result3["tags"], "Should detect MMLU benchmark"
    assert result3["category"] == "benchmarks"
    print(f"  ✅ HFBenchmarkTracker: tags={result3['tags'][:5]}, benchmarks={result3['entities'].get('benchmarks', [])}")


if __name__ == "__main__":
    test_agent_imports()
    test_post_processing()
    print("\n🎉 All Phase 3 agents verified!")
